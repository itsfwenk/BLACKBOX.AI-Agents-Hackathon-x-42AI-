#!/usr/bin/env python3
"""
Script pour déboguer les prix des listings trouvés
"""
import asyncio
import os
from dotenv import load_dotenv
from app.config import ConfigManager
from app.scraper import BrowserManager, VintedScraper

async def debug_prices():
    load_dotenv()
    
    # Load config
    config_manager = ConfigManager(env_file='.env', watches_file='config/watches.yaml')
    config_manager.load_config()
    global_config = config_manager.global_config
    
    # Get first watch (ETB aventures ensemble)
    watch_config = config_manager.watches[0]  # ETB aventures ensemble
    watch = watch_config.to_watch()
    
    print(f"🔍 Debugging prices for: {watch.name}")
    print(f"📊 Max price: €{watch.max_price}")
    print(f"🎯 Price range: €{watch_config.filters.get('price_from', 0)} - €{watch.max_price}")
    
    # Initialize scraper
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
    
    try:
        await browser_manager.start()
        
        # Scrape listings
        listings = await scraper.scrape_watch(watch)
        
        if not listings:
            print("❌ No listings found")
            return
        
        print(f"\n📦 Found {len(listings)} listings:")
        
        # Analyze prices
        prices = [listing.price_amount for listing in listings if listing.price_amount]
        prices.sort()
        
        if prices:
            print(f"💰 Price range found: €{min(prices)} - €{max(prices)}")
            print(f"📈 Average price: €{sum(prices)/len(prices):.2f}")
            
            # Show first 10 listings with prices
            print(f"\n📋 Sample listings:")
            for i, listing in enumerate(listings[:10]):
                status = "✅" if listing.price_amount <= watch.max_price else "❌"
                print(f"  {i+1}. €{listing.price_amount} {status} - {listing.title[:50]}...")
            
            # Count how many would pass price filter
            in_range = [p for p in prices if p <= watch.max_price]
            print(f"\n🎯 Listings within max price (€{watch.max_price}): {len(in_range)}/{len(prices)}")
            
            if watch_config.filters.get('price_from'):
                price_from = watch_config.filters['price_from']
                in_full_range = [p for p in prices if price_from <= p <= watch.max_price]
                print(f"🎯 Listings in full range (€{price_from}-€{watch.max_price}): {len(in_full_range)}/{len(prices)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.stop()

if __name__ == '__main__':
    asyncio.run(debug_prices())
