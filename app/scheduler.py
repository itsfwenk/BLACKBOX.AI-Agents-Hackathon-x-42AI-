"""
Async scheduler for managing watch polling and notifications.
"""

import asyncio
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import signal
import sys

from .models import Watch, Listing
from .store import DatabaseStore, get_db_store
from .scraper import VintedScraper, BrowserManager
from .notifier import DiscordNotifier
from .currency import CurrencyConverter, get_currency_converter
from .config import GlobalConfig
from .utils import logger, ExponentialBackoff


class WatchScheduler:
    """Scheduler for managing watch polling tasks."""
    
    def __init__(self, 
                 global_config: GlobalConfig,
                 browser_manager: BrowserManager,
                 scraper: VintedScraper,
                 notifier: DiscordNotifier,
                 currency_converter: Optional[CurrencyConverter] = None):
        """
        Initialize watch scheduler.
        
        Args:
            global_config: Global configuration
            browser_manager: Browser manager instance
            scraper: Vinted scraper instance
            notifier: Discord notifier instance
            currency_converter: Currency converter instance (optional)
        """
        self.global_config = global_config
        self.browser_manager = browser_manager
        self.scraper = scraper
        self.notifier = notifier
        self.currency_converter = currency_converter
        
        # Scheduler state
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._watches: Dict[str, Watch] = {}
        self._db_store: Optional[DatabaseStore] = None
        
        # Statistics
        self._stats = {
            'total_polls': 0,
            'successful_polls': 0,
            'failed_polls': 0,
            'listings_found': 0,
            'notifications_sent': 0,
            'start_time': None
        }
        
        # Concurrency control
        self._domain_semaphores: Dict[str, asyncio.Semaphore] = {}
        
        logger.info("Watch scheduler initialized")
    
    async def start(self, watches: List[Watch]) -> None:
        """
        Start the scheduler with given watches.
        
        Args:
            watches: List of watches to schedule
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info(f"Starting scheduler with {len(watches)} watches")
        
        try:
            # Initialize database
            self._db_store = await get_db_store(self.global_config.database_path)
            
            # Check for existing watches and avoid duplicates
            for watch_config in watches:
                # Check if a watch with this name already exists
                existing_watches = await self._db_store.get_all_watches(active_only=False)
                existing_watch = None
                
                for existing in existing_watches:
                    if existing.name == watch_config.name and existing.vinted_domain == watch_config.vinted_domain:
                        existing_watch = existing
                        break
                
                if existing_watch:
                    # Update existing watch with new config
                    existing_watch.query = watch_config.query
                    existing_watch.max_price = watch_config.max_price
                    existing_watch.currency = watch_config.currency
                    existing_watch.polling_interval_sec = watch_config.polling_interval_sec
                    existing_watch.notification_webhook = watch_config.notification_webhook
                    existing_watch.min_seller_rating = watch_config.min_seller_rating
                    existing_watch.min_seller_feedback_count = watch_config.min_seller_feedback_count
                    existing_watch.filters = watch_config.filters
                    existing_watch.active = True  # Ensure it's active
                    
                    await self._db_store.save_watch(existing_watch)
                    self._watches[existing_watch.id] = existing_watch
                    logger.info(f"Updated existing watch: {existing_watch.name}")
                else:
                    # Create new watch
                    await self._db_store.save_watch(watch_config)
                    self._watches[watch_config.id] = watch_config
                    logger.info(f"Created new watch: {watch_config.name}")
            
            # Create domain semaphores for concurrency control
            domains = set(watch.vinted_domain for watch in watches)
            for domain in domains:
                self._domain_semaphores[domain] = asyncio.Semaphore(self.global_config.concurrency)
            
            # Start browser and notifier
            await self.browser_manager.start()
            await self.notifier.start()
            
            if self.currency_converter:
                await self.currency_converter.start()
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start watch tasks
            self._running = True
            self._stats['start_time'] = datetime.utcnow()
            
            for watch in watches:
                if watch.active:
                    await self._start_watch_task(watch)
            
            logger.info(f"Scheduler started with {len(self._tasks)} active watch tasks")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the scheduler and cleanup resources."""
        if not self._running:
            return
        
        logger.info("Stopping scheduler...")
        self._running = False
        
        # Cancel all watch tasks
        for task_id, task in self._tasks.items():
            if not task.done():
                task.cancel()
                logger.debug(f"Cancelled task: {task_id}")
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        self._tasks.clear()
        
        # Cleanup resources
        await self.browser_manager.stop()
        await self.notifier.stop()
        
        if self.currency_converter:
            await self.currency_converter.stop()
        
        logger.info("Scheduler stopped")
    
    async def add_watch(self, watch: Watch) -> None:
        """
        Add a new watch to the scheduler.
        
        Args:
            watch: Watch to add
        """
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        # Save to database
        await self._db_store.save_watch(watch)
        self._watches[watch.id] = watch
        
        # Create domain semaphore if needed
        if watch.vinted_domain not in self._domain_semaphores:
            self._domain_semaphores[watch.vinted_domain] = asyncio.Semaphore(self.global_config.concurrency)
        
        # Start task if watch is active and scheduler is running
        if watch.active and self._running:
            await self._start_watch_task(watch)
        
        logger.info(f"Added watch: {watch.name}")
    
    async def remove_watch(self, watch_id: str) -> bool:
        """
        Remove a watch from the scheduler.
        
        Args:
            watch_id: ID of watch to remove
        
        Returns:
            True if watch was removed, False if not found
        """
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        # Stop task if running
        if watch_id in self._tasks:
            task = self._tasks[watch_id]
            if not task.done():
                task.cancel()
            del self._tasks[watch_id]
        
        # Remove from database
        success = await self._db_store.delete_watch(watch_id)
        
        # Remove from memory
        if watch_id in self._watches:
            watch_name = self._watches[watch_id].name
            del self._watches[watch_id]
            logger.info(f"Removed watch: {watch_name}")
        
        return success
    
    async def pause_watch(self, watch_id: str) -> bool:
        """
        Pause a watch (set inactive).
        
        Args:
            watch_id: ID of watch to pause
        
        Returns:
            True if watch was paused, False if not found
        """
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        # Stop task if running
        if watch_id in self._tasks:
            task = self._tasks[watch_id]
            if not task.done():
                task.cancel()
            del self._tasks[watch_id]
        
        # Update database
        success = await self._db_store.set_watch_active(watch_id, False)
        
        # Update memory
        if watch_id in self._watches:
            self._watches[watch_id].active = False
            logger.info(f"Paused watch: {self._watches[watch_id].name}")
        
        return success
    
    async def resume_watch(self, watch_id: str) -> bool:
        """
        Resume a watch (set active).
        
        Args:
            watch_id: ID of watch to resume
        
        Returns:
            True if watch was resumed, False if not found
        """
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        # Update database
        success = await self._db_store.set_watch_active(watch_id, True)
        
        if success and watch_id in self._watches:
            watch = self._watches[watch_id]
            watch.active = True
            
            # Start task if scheduler is running
            if self._running:
                await self._start_watch_task(watch)
            
            logger.info(f"Resumed watch: {watch.name}")
        
        return success
    
    async def _start_watch_task(self, watch: Watch) -> None:
        """Start a polling task for a watch."""
        if watch.id in self._tasks:
            # Task already running
            return
        
        task = asyncio.create_task(self._watch_polling_loop(watch))
        self._tasks[watch.id] = task
        
        logger.debug(f"Started polling task for watch: {watch.name}")
    
    async def _watch_polling_loop(self, watch: Watch) -> None:
        """Main polling loop for a watch."""
        backoff = ExponentialBackoff(initial_delay=1.0, max_delay=300.0)
        
        logger.info(f"Starting polling loop for watch: {watch.name} (interval: {watch.polling_interval_sec}s)")
        
        while self._running and watch.active:
            try:
                # Acquire domain semaphore for concurrency control
                semaphore = self._domain_semaphores.get(watch.vinted_domain)
                if semaphore:
                    async with semaphore:
                        await self._poll_watch(watch)
                else:
                    await self._poll_watch(watch)
                
                # Reset backoff on success
                backoff.reset()
                self._stats['successful_polls'] += 1
                
                # Wait for next poll
                await asyncio.sleep(watch.polling_interval_sec)
                
            except asyncio.CancelledError:
                logger.debug(f"Polling task cancelled for watch: {watch.name}")
                break
                
            except Exception as e:
                logger.error(f"Error in polling loop for watch {watch.name}: {e}")
                self._stats['failed_polls'] += 1
                
                # Apply exponential backoff
                await backoff.wait()
        
        logger.info(f"Polling loop ended for watch: {watch.name}")
    
    async def _poll_watch(self, watch: Watch) -> None:
        """Poll a single watch for new listings."""
        logger.debug(f"Polling watch: {watch.name}")
        
        self._stats['total_polls'] += 1
        
        try:
            # Scrape listings
            listings = await self.scraper.scrape_watch(watch)
            
            if not listings:
                logger.debug(f"No listings found for watch: {watch.name}")
                return
            
            self._stats['listings_found'] += len(listings)
            
            # Process each listing
            new_listings = []
            
            for listing in listings:
                # Check if already seen
                if await self._db_store.is_listing_seen(watch.id, listing.listing_id):
                    # Update last seen time
                    await self._db_store.mark_listing_seen(watch.id, listing.listing_id)
                    continue
                
                # Apply filters
                if not await self._apply_filters(watch, listing):
                    continue
                
                # Mark as seen
                await self._db_store.mark_listing_seen(watch.id, listing.listing_id)
                new_listings.append(listing)
            
            # Send notifications for new listings
            for listing in new_listings:
                try:
                    success = await self.notifier.send_listing_notification(watch, listing)
                    if success:
                        await self._db_store.record_notification(watch.id, listing.listing_id)
                        self._stats['notifications_sent'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send notification for listing {listing.listing_id}: {e}")
            
            if new_listings:
                logger.info(f"Found {len(new_listings)} new listings for watch: {watch.name}")
            else:
                logger.debug(f"No new listings for watch: {watch.name}")
                
        except Exception as e:
            logger.error(f"Error polling watch {watch.name}: {e}")
            raise
    
    async def _apply_filters(self, watch: Watch, listing: Listing) -> bool:
        """
        Apply watch filters to a listing.
        
        Args:
            watch: Watch configuration
            listing: Listing to filter
        
        Returns:
            True if listing passes all filters, False otherwise
        """
        try:
            # Price filter (with currency conversion if needed)
            if not await self._check_price_filter(watch, listing):
                return False
            
            # Seller filters
            if not self._check_seller_filters(watch, listing):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    async def _check_price_filter(self, watch: Watch, listing: Listing) -> bool:
        """Check if listing price is within watch limits."""
        listing_price = listing.price_amount
        listing_currency = listing.price_currency
        watch_max_price = watch.max_price
        watch_currency = watch.currency
        
        # If currencies match, direct comparison
        if listing_currency == watch_currency:
            return listing_price <= watch_max_price
        
        # Try currency conversion if converter is available
        if self.currency_converter:
            try:
                converted_price = await self.currency_converter.convert(
                    listing_price, listing_currency, watch_currency
                )
                
                if converted_price is not None:
                    logger.debug(f"Converted price: {listing_price} {listing_currency} -> {converted_price} {watch_currency}")
                    return converted_price <= watch_max_price
                    
            except Exception as e:
                logger.warning(f"Currency conversion failed: {e}")
        
        # If conversion fails, skip listing with different currency
        logger.debug(f"Skipping listing due to currency mismatch: {listing_currency} vs {watch_currency}")
        return False
    
    def _check_seller_filters(self, watch: Watch, listing: Listing) -> bool:
        """Check if listing meets seller requirements."""
        # Check minimum seller rating
        if watch.min_seller_rating is not None:
            if listing.seller_rating is None or listing.seller_rating < watch.min_seller_rating:
                logger.debug(f"Listing filtered out: seller rating {listing.seller_rating} < {watch.min_seller_rating}")
                return False
        
        # Check minimum seller feedback count
        if watch.min_seller_feedback_count is not None:
            if listing.seller_feedback_count is None or listing.seller_feedback_count < watch.min_seller_feedback_count:
                logger.debug(f"Listing filtered out: seller feedback {listing.seller_feedback_count} < {watch.min_seller_feedback_count}")
                return False
        
        return True
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        uptime = None
        if self._stats['start_time']:
            uptime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
        
        return {
            'running': self._running,
            'active_tasks': len(self._tasks),
            'total_watches': len(self._watches),
            'active_watches': sum(1 for w in self._watches.values() if w.active),
            'uptime_seconds': uptime,
            'statistics': self._stats.copy(),
            'browser_pages': 0 if not self.browser_manager.is_running() else len(self.browser_manager._contexts)
        }
    
    def get_watch_status(self, watch_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific watch."""
        if watch_id not in self._watches:
            return None
        
        watch = self._watches[watch_id]
        task = self._tasks.get(watch_id)
        
        return {
            'id': watch.id,
            'name': watch.name,
            'active': watch.active,
            'query': watch.query,
            'domain': watch.vinted_domain,
            'max_price': watch.max_price,
            'currency': watch.currency,
            'polling_interval_sec': watch.polling_interval_sec,
            'task_running': task is not None and not task.done() if task else False,
            'created_at': watch.created_at.isoformat(),
            'updated_at': watch.updated_at.isoformat()
        }
    
    def list_watches(self) -> List[Dict[str, Any]]:
        """List all watches with their status."""
        return [self.get_watch_status(watch_id) for watch_id in self._watches.keys()]
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data from database."""
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        seen_listings_cleaned = await self._db_store.cleanup_old_seen_listings(days)
        
        return {
            'seen_listings_cleaned': seen_listings_cleaned
        }
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self._db_store:
            raise RuntimeError("Scheduler not started")
        
        return await self._db_store.get_stats()
