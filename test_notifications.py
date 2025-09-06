#!/usr/bin/env python3
"""
Test script to verify Discord notifications are working.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import ConfigManager
from app.notifier import DiscordNotifier
from app.models import Watch, Listing
from datetime import datetime

async def test_notifications():
    """Test Discord notifications with sample data."""
    print("🧪 Testing Discord notifications...")
    
    # Load configuration
    config_manager = ConfigManager()
    config_manager.load_config()
    global_config = config_manager.global_config
    
    # Create notifier
    notifier = DiscordNotifier(
        default_webhook_url=global_config.discord_webhook_url,
        disable_images=global_config.disable_images
    )
    
    try:
        await notifier.start()
        
        # Create sample watch
        watch = Watch(
            name="ETB aventures ensemble",
            vinted_domain="vinted.fr",
            query="ETB aventures ensemble",
            max_price=150.0,
            currency="EUR"
        )
        
        # Create sample listing
        listing = Listing(
            listing_id="test_123456",
            title="Box protection ETB marque: phoenix shield état: Très bon",
            price_amount=19.9,
            price_currency="EUR",
            url="https://www.vinted.fr/items/7027203081-box-protection-etb?referrer=catalog",
            thumbnail_url="https://images1.vinted.net/t/01_00_123/123456.jpeg",
            brand="Phoenix Shield",
            size=None,
            condition="Très bon",
            posted_time=datetime.utcnow(),
            seller_rating=4.8,
            seller_feedback_count=156,
            domain="vinted.fr"
        )
        
        print(f"📤 Sending test notification...")
        print(f"   Title: {listing.title}")
        print(f"   Price: {listing.price_amount} {listing.price_currency}")
        print(f"   URL: {listing.url}")
        
        # Send notification
        success = await notifier.send_listing_notification(watch, listing)
        
        if success:
            print("✅ Test notification sent successfully!")
            print("🔔 Check your Discord channel for the notification")
            print("📋 The notification should include:")
            print("   • Clickable title that opens the Vinted listing")
            print("   • Price, brand, condition details")
            print("   • Seller rating and feedback count")
            print("   • Color-coded embed (green for good deals)")
        else:
            print("❌ Failed to send test notification")
            
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")
        
    finally:
        await notifier.stop()

if __name__ == "__main__":
    asyncio.run(test_notifications())
