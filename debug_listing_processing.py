#!/usr/bin/env python3
"""
Script pour déboguer le traitement des listings
"""
import asyncio
import os
from dotenv import load_dotenv
from app.config import ConfigManager
from app.scraper import BrowserManager, VintedScraper
from app.store import get_db_store, close_db_store

async def debug_listing_processing():
    load_dotenv()
    
    # Load config
    config_manager = ConfigManager(env_file='.env', watches_file='config/watches.yaml')
    config_manager.load_config()
    global_config = config_manager.global_config
    
    # Get first watch (ETB aventures ensemble)
    watch_config = config_manager.watches[0]  # ETB aventures ensemble
    watch = watch_config.to_watch()
    
    print(f"🔍 Debugging listing processing for: {watch.name}")
    print(f"📊 Max price: €{watch.max_price}")
    
    # Initialize database
    db_store = await get_db_store(global_config.database_path)
    
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
        print(f"\n🔍 Scraping listings...")
        listings = await scraper.scrape_watch(watch)
        
        if not listings:
            print("❌ No listings found")
            return
        
        print(f"📦 Found {len(listings)} listings")
        
        # Process first 5 listings to debug
        for i, listing in enumerate(listings[:5]):
            print(f"\n--- Listing {i+1} ---")
            print(f"ID: {listing.listing_id}")
            print(f"Title: {listing.title[:60]}...")
            print(f"Price: €{listing.price_amount}")
            print(f"URL: {listing.url}")
            
            # Check if already seen
            is_seen = await db_store.is_listing_seen(watch.id, listing.listing_id)
            print(f"Already seen: {is_seen}")
            
            # Check price filter
            price_ok = listing.price_amount <= watch.max_price
            print(f"Price OK (≤€{watch.max_price}): {price_ok}")
            
            # Check seller filters
            seller_rating_ok = True
            if watch.min_seller_rating is not None:
                seller_rating_ok = listing.seller_rating is not None and listing.seller_rating >= watch.min_seller_rating
            
            seller_feedback_ok = True
            if watch.min_seller_feedback_count is not None:
                seller_feedback_ok = listing.seller_feedback_count is not None and listing.seller_feedback_count >= watch.min_seller_feedback_count
            
            print(f"Seller rating OK: {seller_rating_ok} (rating: {listing.seller_rating})")
            print(f"Seller feedback OK: {seller_feedback_ok} (feedback: {listing.seller_feedback_count})")
            
            # Overall result
            would_notify = not is_seen and price_ok and seller_rating_ok and seller_feedback_ok
            print(f"🎯 Would notify: {would_notify}")
            
            if would_notify:
                print("✅ This listing should trigger a notification!")
            else:
                reasons = []
                if is_seen:
                    reasons.append("already seen")
                if not price_ok:
                    reasons.append(f"price too high (€{listing.price_amount} > €{watch.max_price})")
                if not seller_rating_ok:
                    reasons.append(f"seller rating too low ({listing.seller_rating} < {watch.min_seller_rating})")
                if not seller_feedback_ok:
                    reasons.append(f"seller feedback too low ({listing.seller_feedback_count} < {watch.min_seller_feedback_count})")
                print(f"❌ Filtered out: {', '.join(reasons)}")
        
        # Check database state
        print(f"\n📊 Database state:")
        stats = await db_store.get_stats()
        print(f"Total seen listings: {stats['total_seen_listings']}")
        print(f"Total notifications: {stats['total_notifications']}")
        
        # Check seen listings for this watch
        seen_listings = await db_store.get_seen_listings(watch.id)
        print(f"Seen listings for this watch: {len(seen_listings)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.stop()
        await close_db_store()

if __name__ == '__main__':
    asyncio.run(debug_listing_processing())
