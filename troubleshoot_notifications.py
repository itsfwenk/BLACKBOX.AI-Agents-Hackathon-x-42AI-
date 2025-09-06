#!/usr/bin/env python3
"""
Comprehensive troubleshooting script for Vinted Monitor Discord notifications
"""

import asyncio
import yaml
import os
from pathlib import Path
import sys

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import ConfigManager
from app.notifier import DiscordNotifier
from app.scraper import BrowserManager, VintedScraper
from app.store import get_db_store, close_db_store

async def troubleshoot_notifications():
    print("🔍 VINTED MONITOR TROUBLESHOOTING")
    print("=" * 50)
    
    # 1. Check configuration files
    print("\n1️⃣ CHECKING CONFIGURATION FILES")
    print("-" * 30)
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file exists")
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'DISCORD_WEBHOOK_URL' in env_content:
                webhook_line = [line for line in env_content.split('\n') if 'DISCORD_WEBHOOK_URL' in line][0]
                if webhook_line.startswith('#'):
                    print("❌ DISCORD_WEBHOOK_URL is commented out!")
                elif '=' in webhook_line and len(webhook_line.split('=')[1].strip()) > 10:
                    print("✅ DISCORD_WEBHOOK_URL is configured")
                else:
                    print("❌ DISCORD_WEBHOOK_URL is empty or invalid")
            else:
                print("❌ DISCORD_WEBHOOK_URL not found in .env")
    else:
        print("❌ .env file not found")
    
    # Check watches.yaml
    if os.path.exists('config/watches.yaml'):
        print("✅ config/watches.yaml exists")
        try:
            data = yaml.safe_load(open('config/watches.yaml'))
            print(f"✅ YAML is valid with {len(data['watches'])} watches")
            
            for i, watch in enumerate(data['watches']):
                print(f"   {i+1}. {watch['name']}")
                print(f"      Query: \"{watch['query']}\"")
                print(f"      Max Price: {watch['max_price']} {watch['currency']}")
                if 'ETB rivalités' in watch['name']:
                    print("      ⭐ This is your ETB watch")
        except Exception as e:
            print(f"❌ YAML parsing error: {e}")
    else:
        print("❌ config/watches.yaml not found")
    
    # 2. Test Discord webhook
    print("\n2️⃣ TESTING DISCORD WEBHOOK")
    print("-" * 30)
    
    try:
        config_manager = ConfigManager(env_file='.env', watches_file='config/watches.yaml')
        config_manager.load_config()
        global_config = config_manager.global_config
        
        if global_config.discord_webhook_url:
            print(f"✅ Webhook URL loaded: {global_config.discord_webhook_url[:50]}...")
            
            notifier = DiscordNotifier(default_webhook_url=global_config.discord_webhook_url)
            await notifier.start()
            
            success = await notifier.test_webhook()
            if success:
                print("✅ Discord webhook test SUCCESSFUL")
            else:
                print("❌ Discord webhook test FAILED")
            
            await notifier.stop()
        else:
            print("❌ No Discord webhook URL configured")
            
    except Exception as e:
        print(f"❌ Discord webhook error: {e}")
    
    # 3. Test scraper for ETB watch
    print("\n3️⃣ TESTING ETB SCRAPER")
    print("-" * 30)
    
    try:
        # Find ETB watch
        etb_watch = None
        for watch_config in config_manager.watches:
            if 'ETB rivalités' in watch_config.name:
                etb_watch = watch_config.to_watch()
                break
        
        if etb_watch:
            print(f"✅ Found ETB watch: {etb_watch.name}")
            print(f"   Query: \"{etb_watch.query}\"")
            print(f"   Max Price: {etb_watch.max_price} {etb_watch.currency}")
            
            # Test scraper
            browser_manager = BrowserManager(headless=True, concurrency=1)
            scraper = VintedScraper(browser_manager=browser_manager, max_pages_per_poll=1)
            
            await browser_manager.start()
            print("✅ Browser started")
            
            # Test scrape
            print("🔍 Testing scrape...")
            result = await scraper.test_scrape(etb_watch, dry_run=True)
            
            if result['success']:
                print(f"✅ Scrape successful! Found {result['listings_found']} listings")
                if result['listings_found'] > 0:
                    print("✅ Items are available on Vinted")
                else:
                    print("⚠️  No listings found - check your search query")
            else:
                print(f"❌ Scrape failed: {result.get('error', 'Unknown error')}")
            
            await browser_manager.stop()
        else:
            print("❌ ETB watch not found in configuration")
            
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
    
    # 4. Check database
    print("\n4️⃣ CHECKING DATABASE")
    print("-" * 30)
    
    try:
        db_store = await get_db_store(global_config.database_path)
        stats = await db_store.get_stats()
        
        print(f"✅ Database connected: {global_config.database_path}")
        print(f"   Total watches: {stats['total_watches']}")
        print(f"   Seen listings: {stats['total_seen_listings']}")
        print(f"   Total notifications: {stats['total_notifications']}")
        
        if stats['total_seen_listings'] > 0:
            print("⚠️  You have seen listings - monitor will only notify for NEW items")
            print("   Use: python -m app.main clear-seen \"ETB rivalités destinées\"")
        
        await close_db_store()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # 5. Summary and recommendations
    print("\n5️⃣ SUMMARY & RECOMMENDATIONS")
    print("-" * 30)
    
    print("\n🎯 TO GET NOTIFICATIONS:")
    print("1. Make sure Discord webhook is working (test above)")
    print("2. Clear seen listings: python -m app.main clear-seen \"ETB rivalités destinées\"")
    print("3. Start monitor: python -m app.main run")
    print("4. Wait for NEW listings to appear (existing ones won't trigger notifications)")
    
    print("\n🧪 TO TEST IMMEDIATELY:")
    print("1. python -m app.main test-watch \"ETB rivalités destinées\"")
    print("   (This will send a test notification)")

if __name__ == '__main__':
    asyncio.run(troubleshoot_notifications())
