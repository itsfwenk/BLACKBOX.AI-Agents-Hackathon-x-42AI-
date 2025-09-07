"""
Discord webhook notifications for Vinted listings.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models import Watch, Listing
from ..utils import logger, format_relative_time, truncate_text, RateLimiter


class DiscordNotifier:
    """Discord webhook notifier for Vinted listings."""
    
    def __init__(self, 
                 default_webhook_url: Optional[str] = None,
                 disable_images: bool = False,
                 rate_limit_requests: int = 5,
                 rate_limit_window: float = 1.0):
        """
        Initialize Discord notifier.
        
        Args:
            default_webhook_url: Default Discord webhook URL
            disable_images: Disable images in notifications
            rate_limit_requests: Max requests per time window
            rate_limit_window: Rate limit time window in seconds
        """
        self.default_webhook_url = default_webhook_url
        self.disable_images = disable_images
        self._rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Discord notifier initialized (images: {'disabled' if disable_images else 'enabled'})")
    
    async def start(self) -> None:
        """Start the notifier session."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("Discord notifier session started")
    
    async def stop(self) -> None:
        """Stop the notifier session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("Discord notifier session stopped")
    
    async def send_listing_notification(self,
                                        watch: Watch,
                                        listing: Listing,
                                        extra_text: Optional[str] = None) -> bool:
        """
        Send notification for a new listing.

        Args:
            watch: Watch that found the listing
            listing: Listing to notify about
            extra_text: Additional text to include in notification (e.g., AI analysis reason)

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Get webhook URL (watch-specific or default)
            webhook_url = watch.notification_webhook or self.default_webhook_url

            if not webhook_url:
                logger.error(f"No webhook URL configured for watch {watch.name}")
                return False

            # Create Discord embed
            embed = self._create_listing_embed(watch, listing, extra_text)

            # Send notification
            success = await self._send_webhook(webhook_url, embed)

            if success:
                logger.info(f"Sent Discord notification for listing {listing.listing_id} (watch: {watch.name})")
            else:
                logger.error(f"Failed to send Discord notification for listing {listing.listing_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
    
    async def send_watch_status_notification(self, 
                                             watch: Watch, 
                                             status: str, 
                                             details: Optional[str] = None) -> bool:
        """
        Send status notification for a watch.
        
        Args:
            watch: Watch to notify about
            status: Status message
            details: Additional details
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            webhook_url = watch.notification_webhook or self.default_webhook_url
            
            if not webhook_url:
                logger.warning(f"No webhook URL configured for watch status notification: {watch.name}")
                return False
            
            embed = self._create_status_embed(watch, status, details)
            success = await self._send_webhook(webhook_url, embed)
            
            if success:
                logger.info(f"Sent watch status notification for {watch.name}: {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending watch status notification: {e}")
            return False
    
    async def send_error_notification(self, 
                                      watch: Watch, 
                                      error: str, 
                                      details: Optional[str] = None) -> bool:
        """
        Send error notification for a watch.
        
        Args:
            watch: Watch that encountered error
            error: Error message
            details: Additional error details
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            webhook_url = watch.notification_webhook or self.default_webhook_url
            
            if not webhook_url:
                return False
            
            embed = self._create_error_embed(watch, error, details)
            success = await self._send_webhook(webhook_url, embed)
            
            if success:
                logger.info(f"Sent error notification for {watch.name}: {error}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def _create_listing_embed(self, watch: Watch, listing: Listing, extra_text: Optional[str] = None) -> Dict[str, Any]:
        """Create Discord embed for a listing notification."""
        # Determine embed color based on price
        color = self._get_price_color(listing.price_amount, watch.max_price)

        # Build description
        description_parts = [
            f"**{listing.price_amount} {listing.price_currency}**"
        ]

        if listing.brand:
            description_parts.append(f"Brand: {listing.brand}")

        if listing.size:
            description_parts.append(f"Size: {listing.size}")

        if listing.condition:
            description_parts.append(f"Condition: {listing.condition}")

        # Add extra text (AI analysis reason) if provided
        if extra_text:
            description_parts.append(f"**AI Analysis:** {extra_text}")

        description = "\n".join(description_parts)
        
        # Create embed
        embed = {
            "title": truncate_text(listing.title, 256),
            "description": description,
            "url": listing.url,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Watch",
                    "value": watch.name,
                    "inline": True
                },
                {
                    "name": "Domain",
                    "value": listing.domain,
                    "inline": True
                },
                {
                    "name": "Max Price",
                    "value": f"{watch.max_price} {watch.currency}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Vinted Monitor • Listing ID: {listing.listing_id}"
            }
        }
        
        # Add thumbnail if available and not disabled
        if listing.thumbnail_url and not self.disable_images:
            embed["thumbnail"] = {"url": listing.thumbnail_url}
        
        # Add seller info if available
        if listing.seller_rating is not None or listing.seller_feedback_count is not None:
            seller_info = []
            if listing.seller_rating is not None:
                seller_info.append(f"Rating: {listing.seller_rating}/5")
            if listing.seller_feedback_count is not None:
                seller_info.append(f"Reviews: {listing.seller_feedback_count}")
            
            embed["fields"].append({
                "name": "Seller",
                "value": " • ".join(seller_info),
                "inline": True
            })
        
        # Add posted time if available
        if listing.posted_time:
            embed["fields"].append({
                "name": "Posted",
                "value": format_relative_time(listing.posted_time),
                "inline": True
            })
        
        return embed
    
    def _create_status_embed(self, watch: Watch, status: str, details: Optional[str] = None) -> Dict[str, Any]:
        """Create Discord embed for watch status notification."""
        embed = {
            "title": f"Watch Status: {watch.name}",
            "description": status,
            "color": 0x00ff00,  # Green
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Query",
                    "value": watch.query,
                    "inline": True
                },
                {
                    "name": "Domain",
                    "value": watch.vinted_domain,
                    "inline": True
                },
                {
                    "name": "Max Price",
                    "value": f"{watch.max_price} {watch.currency}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Vinted Monitor • Watch ID: {watch.id}"
            }
        }
        
        if details:
            embed["fields"].append({
                "name": "Details",
                "value": truncate_text(details, 1024),
                "inline": False
            })
        
        return embed
    
    def _create_error_embed(self, watch: Watch, error: str, details: Optional[str] = None) -> Dict[str, Any]:
        """Create Discord embed for error notification."""
        embed = {
            "title": f"Watch Error: {watch.name}",
            "description": truncate_text(error, 2048),
            "color": 0xff0000,  # Red
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Query",
                    "value": watch.query,
                    "inline": True
                },
                {
                    "name": "Domain",
                    "value": watch.vinted_domain,
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Vinted Monitor • Watch ID: {watch.id}"
            }
        }
        
        if details:
            embed["fields"].append({
                "name": "Error Details",
                "value": truncate_text(details, 1024),
                "inline": False
            })
        
        return embed
    
    def _get_price_color(self, price: float, max_price: float) -> int:
        """Get color based on price relative to max price."""
        if price <= max_price * 0.5:
            return 0x00ff00  # Green - Great deal
        elif price <= max_price * 0.75:
            return 0xffff00  # Yellow - Good deal
        elif price <= max_price:
            return 0xff8000  # Orange - At limit
        else:
            return 0xff0000  # Red - Over limit (shouldn't happen)
    
    async def _send_webhook(self, webhook_url: str, embed: Dict[str, Any]) -> bool:
        """
        Send webhook to Discord.
        
        Args:
            webhook_url: Discord webhook URL
            embed: Discord embed data
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._session:
            await self.start()
        
        try:
            # Apply rate limiting
            await self._rate_limiter.acquire()
            
            # Prepare payload
            payload = {
                "embeds": [embed],
                "username": "Vinted Monitor"
            }
            
            # Send webhook
            async with self._session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Discord webhook failed: {response.status} - {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("Discord webhook timeout")
            return False
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    async def test_webhook(self, webhook_url: Optional[str] = None) -> bool:
        """
        Test webhook connectivity.
        
        Args:
            webhook_url: Webhook URL to test (uses default if None)
        
        Returns:
            True if webhook is working, False otherwise
        """
        url = webhook_url or self.default_webhook_url
        
        if not url:
            logger.error("No webhook URL provided for testing")
            return False
        
        test_embed = {
            "title": "Vinted Monitor Test",
            "description": "This is a test notification from Vinted Monitor",
            "color": 0x0099ff,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Vinted Monitor • Test Notification"
            }
        }
        
        success = await self._send_webhook(url, test_embed)
        
        if success:
            logger.info("Webhook test successful")
        else:
            logger.error("Webhook test failed")
        
        return success
    
    def is_valid_webhook_url(self, url: str) -> bool:
        """Validate Discord webhook URL format."""
        import re
        
        if not url:
            return False
        
        # Discord webhook URL pattern
        pattern = r'https://discord\.com/api/webhooks/\d+/[\w-]+'
        return bool(re.match(pattern, url))
