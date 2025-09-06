"""
Main Vinted scraper that orchestrates browser management and data extraction.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Watch, Listing
from ..utils import logger, sleep_with_jitter, create_search_url, ExponentialBackoff
from .browser import BrowserManager
from .parsers import VintedParser


class VintedScraper:
    """Main scraper for Vinted listings."""
    
    def __init__(self, 
                 browser_manager: BrowserManager,
                 min_delay_ms: int = 800,
                 max_delay_ms: int = 2200,
                 max_pages_per_poll: int = 2):
        """
        Initialize Vinted scraper.
        
        Args:
            browser_manager: Browser manager instance
            min_delay_ms: Minimum delay between requests
            max_delay_ms: Maximum delay between requests
            max_pages_per_poll: Maximum pages to scrape per poll
        """
        self.browser_manager = browser_manager
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self.max_pages_per_poll = max_pages_per_poll
        
        # Cache parsers by domain
        self._parsers: Dict[str, VintedParser] = {}
        
        logger.info(f"Vinted scraper initialized (delay: {min_delay_ms}-{max_delay_ms}ms, max_pages: {max_pages_per_poll})")
    
    def _get_parser(self, domain: str) -> VintedParser:
        """Get or create parser for domain."""
        if domain not in self._parsers:
            self._parsers[domain] = VintedParser(domain)
        return self._parsers[domain]
    
    async def scrape_watch(self, watch: Watch) -> List[Listing]:
        """
        Scrape listings for a watch.
        
        Args:
            watch: Watch configuration
        
        Returns:
            List of scraped listings
        """
        logger.info(f"Starting scrape for watch: {watch.name} ({watch.query})")
        
        try:
            # Build search URL
            filters = watch.filters.copy()
            filters['max_price'] = watch.max_price
            
            search_url = create_search_url(
                domain=watch.vinted_domain,
                query=watch.query,
                filters=filters
            )
            
            logger.debug(f"Search URL: {search_url}")
            
            # Get parser for domain
            parser = self._get_parser(watch.vinted_domain)
            
            # Scrape listings
            listings = await self._scrape_listings(
                url=search_url,
                parser=parser,
                watch_id=watch.id,
                max_pages=self.max_pages_per_poll
            )
            
            logger.info(f"Scraped {len(listings)} listings for watch: {watch.name}")
            return listings
            
        except Exception as e:
            logger.error(f"Error scraping watch {watch.name}: {e}")
            return []
    
    async def _scrape_listings(self, 
                               url: str, 
                               parser: VintedParser, 
                               watch_id: str,
                               max_pages: int) -> List[Listing]:
        """
        Scrape listings from multiple pages.
        
        Args:
            url: Initial search URL
            parser: Domain parser
            watch_id: Watch ID for logging
            max_pages: Maximum pages to scrape
        
        Returns:
            List of scraped listings
        """
        all_listings = []
        backoff = ExponentialBackoff(initial_delay=1.0, max_delay=30.0)
        
        async with self.browser_manager.get_page(domain=parser.domain) as page:
            current_url = url
            
            for page_num in range(1, max_pages + 1):
                try:
                    logger.debug(f"Scraping page {page_num} for watch {watch_id}")
                    
                    # Navigate to page with retry
                    success = await self.browser_manager.navigate_with_retry(
                        page=page,
                        url=current_url,
                        max_retries=3,
                        timeout=30000
                    )
                    
                    if not success:
                        logger.warning(f"Failed to navigate to page {page_num} for watch {watch_id}")
                        break
                    
                    # Wait for listings to load
                    listings_loaded = await self.browser_manager.wait_for_listings(page, timeout=15000)
                    if not listings_loaded:
                        logger.warning(f"No listings found on page {page_num} for watch {watch_id}")
                        break
                    
                    # Add delay before scraping
                    await sleep_with_jitter(self.min_delay_ms, self.max_delay_ms)
                    
                    # Extract listings from current page
                    page_listings = await parser.extract_listings(page)
                    
                    if not page_listings:
                        logger.warning(f"No listings extracted from page {page_num} for watch {watch_id}")
                        break
                    
                    all_listings.extend(page_listings)
                    logger.debug(f"Extracted {len(page_listings)} listings from page {page_num}")
                    
                    # Check if there's a next page and we haven't reached the limit
                    if page_num < max_pages:
                        has_next = await parser.has_next_page(page)
                        if not has_next:
                            logger.debug(f"No more pages available after page {page_num}")
                            break
                        
                        # Click next page
                        next_success = await parser.click_next_page(page)
                        if not next_success:
                            logger.warning(f"Failed to navigate to next page after page {page_num}")
                            break
                        
                        # Add delay between pages
                        await sleep_with_jitter(self.min_delay_ms, self.max_delay_ms)
                    
                    # Reset backoff on success
                    backoff.reset()
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page_num} for watch {watch_id}: {e}")
                    
                    # Apply exponential backoff
                    await backoff.wait()
                    
                    # Continue to next page on error
                    continue
        
        # Remove duplicates based on listing_id
        unique_listings = {}
        for listing in all_listings:
            if listing.listing_id not in unique_listings:
                unique_listings[listing.listing_id] = listing
        
        final_listings = list(unique_listings.values())
        logger.info(f"Scraped {len(final_listings)} unique listings across {page_num} pages for watch {watch_id}")
        
        return final_listings
    
    async def test_scrape(self, watch: Watch, dry_run: bool = True) -> Dict[str, Any]:
        """
        Test scrape for a watch without storing results.
        
        Args:
            watch: Watch configuration
            dry_run: If True, don't store results or send notifications
        
        Returns:
            Dictionary with scrape results and statistics
        """
        start_time = datetime.utcnow()
        
        try:
            # Scrape listings
            listings = await self.scrape_watch(watch)
            
            # Calculate statistics
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze results
            price_stats = self._calculate_price_stats(listings)
            
            results = {
                'success': True,
                'watch_name': watch.name,
                'watch_id': watch.id,
                'query': watch.query,
                'domain': watch.vinted_domain,
                'max_price': watch.max_price,
                'currency': watch.currency,
                'listings_found': len(listings),
                'duration_seconds': round(duration, 2),
                'dry_run': dry_run,
                'timestamp': start_time.isoformat(),
                'price_stats': price_stats,
                'sample_listings': [
                    {
                        'id': listing.listing_id,
                        'title': listing.title[:100],
                        'price': f"{listing.price_amount} {listing.price_currency}",
                        'url': listing.url,
                        'brand': listing.brand,
                        'size': listing.size,
                        'condition': listing.condition
                    }
                    for listing in listings[:5]  # First 5 listings as sample
                ]
            }
            
            logger.info(f"Test scrape completed for {watch.name}: {len(listings)} listings in {duration:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Test scrape failed for {watch.name}: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'success': False,
                'watch_name': watch.name,
                'watch_id': watch.id,
                'error': str(e),
                'duration_seconds': round(duration, 2),
                'dry_run': dry_run,
                'timestamp': start_time.isoformat()
            }
    
    def _calculate_price_stats(self, listings: List[Listing]) -> Dict[str, Any]:
        """Calculate price statistics for listings."""
        if not listings:
            return {}
        
        prices = [listing.price_amount for listing in listings if listing.price_amount is not None]
        
        if not prices:
            return {}
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': round(sum(prices) / len(prices), 2),
            'total_listings': len(listings),
            'listings_with_price': len(prices)
        }
    
    async def validate_domain(self, domain: str) -> bool:
        """
        Validate that a Vinted domain is accessible.
        
        Args:
            domain: Vinted domain to validate
        
        Returns:
            True if domain is accessible, False otherwise
        """
        try:
            test_url = f"https://{domain}"
            
            async with self.browser_manager.get_page(domain=domain) as page:
                success = await self.browser_manager.navigate_with_retry(
                    page=page,
                    url=test_url,
                    max_retries=2,
                    timeout=15000
                )
                
                if success:
                    # Check if it's actually a Vinted page
                    title = await page.title()
                    if 'vinted' in title.lower():
                        logger.info(f"Domain {domain} is accessible")
                        return True
                
                logger.warning(f"Domain {domain} is not accessible or not a Vinted site")
                return False
                
        except Exception as e:
            logger.error(f"Error validating domain {domain}: {e}")
            return False
    
    async def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """
        Get information about a Vinted domain.
        
        Args:
            domain: Vinted domain
        
        Returns:
            Dictionary with domain information
        """
        try:
            parser = self._get_parser(domain)
            
            info = {
                'domain': domain,
                'base_url': f"https://{domain}",
                'default_currency': parser.get_domain_currency(),
                'accessible': await self.validate_domain(domain)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting domain info for {domain}: {e}")
            return {
                'domain': domain,
                'error': str(e),
                'accessible': False
            }
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported Vinted domains."""
        return [
            'vinted.fr',
            'vinted.com',
            'vinted.de',
            'vinted.it',
            'vinted.es',
            'vinted.pl',
            'vinted.lt',
            'vinted.cz'
        ]
    
    async def cleanup(self) -> None:
        """Cleanup scraper resources."""
        # Clear parser cache
        self._parsers.clear()
        logger.debug("Vinted scraper cleaned up")
