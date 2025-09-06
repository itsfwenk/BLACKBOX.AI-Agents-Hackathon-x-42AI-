#!/usr/bin/env python3
"""
Simulate what happens when a new ETB listing appears.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import ConfigManager
from app.notifier import DiscordNotifier
from app.models import Watch, Listing

async def simulate_new_listing():
    """Simulate a new ETB listing notification."""
    print("🎬 Simulating: New ETB listing appears on Vinted...")
    print()
    
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
        print("❌ ETB watch not found")
        return
    
    watch = etb_watch_config.to_watch()
    
    # Create notifier
    notifier = DiscordNotifier(
        default_webhook_url=global_config.discord_webhook_url,
        disable_images=global_config.disable_images
    )
    
    try:
        await notifier.start()
        
        # Create a realistic new listing with proper Vinted URL format
        listing_id = f"{int(datetime.now().timestamp())}"
        new_listing = Listing(
            listing_id=listing_id,
            title="🆕 ETB Pokémon Écarlate et Violet - Destinées de Paldea NEUF",
            price_amount=89.99,
            price_currency="EUR",
            url=f"https://www.vinted.fr/items/{listing_id}-etb-pokemon-ecarlate-violet-destinees-paldea-neuf",
            thumbnail_url="https://images1.vinted.net/t/01_00_new/new_etb.jpeg",
            brand="Pokémon",
            size=None,
            condition="Neuf avec étiquettes",
            posted_time=datetime.now(),
            seller_rating=4.9,
            seller_feedback_count=234,
            domain="vinted.fr"
        )
        
        print(f"📦 New listing detected:")
        print(f"   Title: {new_listing.title}")
        print(f"   Price: {new_listing.price_amount} {new_listing.price_currency}")
        print(f"   Condition: {new_listing.condition}")
        print(f"   Seller: ⭐ {new_listing.seller_rating} ({new_listing.seller_feedback_count} reviews)")
        print()
        
        print("📤 Sending Discord notification...")
        
        success = await notifier.send_listing_notification(watch, new_listing)
        
        if success:
            print("✅ Discord notification sent!")
            print()
            print("🔔 This is what you'll receive when a real new ETB listing appears:")
            print("   • Rich Discord embed with item details")
            print("   • Clickable title that opens the Vinted listing")
            print("   • Price, condition, and seller information")
            print("   • Color-coded (green for great deals)")
            print()
            print("🎯 Your monitor is ready to catch new deals!")
        else:
            print("❌ Failed to send notification")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await notifier.stop()

if __name__ == "__main__":
    asyncio.run(simulate_new_listing())
