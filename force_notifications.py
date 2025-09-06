#!/usr/bin/env python3
"""
Force notifications for existing listings to test the system.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import ConfigManager
from app.notifier import DiscordNotifier
from app.scraper import BrowserManager, VintedScraper
from app.models import Watch
from datetime import datetime

async def force_notifications():
    """Force notifications for current ETB listings."""
    print("🚀 Forcing notifications for current ETB listings...")
    
    # Load configuration
    config_manager = ConfigManager()
    config_manager.load_config()
    global_config = config_manager.global_config
    
    # Find ETB watch
    etb_watch_config = None
    for watch_config in config_manager.watches:
        if "ETB" in watch_config.name:
            etb_watch_config = watch_config
            break
    
    if not etb_watch_config:
        print("❌ ETB watch not found in configuration")
        return
    
    watch = etb_watch_config.to_watch()
    print(f"📋 Found watch: {watch.name}")
    print(f"   Query: {watch.query}")
    print(f"   Max Price: {watch.max_price} {watch.currency}")
    
    # Initialize components
    browser_manager = BrowserManager(
        headless=global_config.headless,
        user_agent=global_config.user_agent,
        concurrency=1
    )
    
    scraper = VintedScraper(
        browser_manager=browser_manager,
        min_delay_ms=global_config.min_delay_ms,
        max_delay_ms=global_config.max_delay_ms,
        max_pages_per_poll=1
    )
    
    notifier = DiscordNotifier(
        default_webhook_url=global_config.discord_webhook_url,
        disable_images=global_config.disable_images
    )
    
    try:
        await browser_manager.start()
        await notifier.start()
        
        print("🔍 Scraping current listings...")
        listings = await scraper.scrape_watch(watch)
        
        print(f"📦 Found {len(listings)} listings")
        
        # Filter listings under max price
        valid_listings = [
            listing for listing in listings 
            if listing.price_amount <= watch.max_price
        ]
        
        print(f"💰 {len(valid_listings)} listings under {watch.max_price} {watch.currency}")
        
        if valid_listings:
            # Send notifications for first 3 listings
            for i, listing in enumerate(valid_listings[:3], 1):
                print(f"\n📤 Sending notification {i}/3:")
                print(f"   Title: {listing.title[:60]}...")
                print(f"   Price: {listing.price_amount} {listing.price_currency}")
                print(f"   URL: {listing.url}")
                
                success = await notifier.send_listing_notification(watch, listing)
                
                if success:
                    print(f"   ✅ Notification sent!")
                else:
                    print(f"   ❌ Failed to send notification")
                
                # Small delay between notifications
                await asyncio.sleep(2)
            
            print(f"\n🎉 Sent notifications for {min(3, len(valid_listings))} listings!")
            print("🔔 Check your Discord channel for the notifications")
        else:
            print("❌ No listings found under the price limit")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await browser_manager.stop()
        await notifier.stop()

if __name__ == "__main__":
    asyncio.run(force_notifications())
