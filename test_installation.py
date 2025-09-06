#!/usr/bin/env python3
"""
Test script to verify Vinted Monitor installation and basic functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_installation():
    """Test basic functionality of the Vinted Monitor."""
    print("🧪 Testing Vinted Monitor Installation...")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from app.config import ConfigManager, GlobalConfig
        from app.models import Watch, Listing, WatchConfig
        from app.store import DatabaseStore
        from app.scraper import BrowserManager, VintedScraper, VintedParser
        from app.notifier import DiscordNotifier
        from app.currency import CurrencyConverter
        from app.scheduler import WatchScheduler
        from app.utils import normalize_price, create_search_url
        print("✅ All imports successful")
        
        # Test configuration
        print("\n⚙️  Testing configuration...")
        global_config = GlobalConfig.from_env()
        print(f"✅ Global config loaded (headless: {global_config.headless})")
        
        # Test models
        print("\n📋 Testing models...")
        watch = Watch(
            name="Test Watch",
            vinted_domain="vinted.fr",
            query="test item",
            max_price=50.0,
            currency="EUR"
        )
        print(f"✅ Watch model created: {watch.name}")
        
        listing = Listing(
            listing_id="123456",
            title="Test Item",
            price_amount=25.0,
            price_currency="EUR",
            url="https://vinted.fr/items/123456",
            domain="vinted.fr"
        )
        print(f"✅ Listing model created: {listing.title}")
        
        # Test utilities
        print("\n🔧 Testing utilities...")
        amount, currency = normalize_price("€25.50")
        assert amount == 25.50 and currency == "EUR"
        print("✅ Price normalization working")
        
        url = create_search_url("vinted.fr", "test", {"max_price": 50})
        assert "vinted.fr/catalog" in url
        print("✅ Search URL creation working")
        
        # Test database (in-memory)
        print("\n🗄️  Testing database...")
        import tempfile
        import os
        
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(temp_fd)
        
        try:
            db_store = DatabaseStore(temp_path)
            await db_store.initialize()
            
            await db_store.save_watch(watch)
            retrieved_watch = await db_store.get_watch(watch.id)
            assert retrieved_watch.name == watch.name
            print("✅ Database operations working")
            
            await db_store.close()
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        
        # Test currency converter
        print("\n💱 Testing currency converter...")
        converter = CurrencyConverter()
        result = await converter.convert(100.0, "EUR", "EUR")
        assert result == 100.0
        print("✅ Currency converter working")
        
        # Test Discord notifier (without sending)
        print("\n🔔 Testing Discord notifier...")
        notifier = DiscordNotifier("https://discord.com/api/webhooks/test/test")
        embed = notifier._create_listing_embed(watch, listing)
        assert embed["title"] == listing.title
        print("✅ Discord notifier working")
        
        # Test parser
        print("\n🔍 Testing parser...")
        parser = VintedParser("vinted.fr")
        assert parser.domain == "vinted.fr"
        assert parser.get_domain_currency() == "EUR"
        print("✅ Parser working")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Vinted Monitor is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your Discord webhook")
        print("2. Copy config/watches.yaml.example to config/watches.yaml")
        print("3. Run: python -m app.main init")
        print("4. Run: python -m app.main run")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_installation())
    sys.exit(0 if success else 1)
