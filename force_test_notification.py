#!/usr/bin/env python3
"""
Script pour forcer une notification de test pendant que l'app tourne
"""
import asyncio
import os
from datetime import datetime
from app.notifier.discord import DiscordNotifier
from app.models import Watch, Listing

async def test_notification():
    # Charger l'URL du webhook depuis .env
    from dotenv import load_dotenv
    load_dotenv()
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL non trouvé dans .env")
        return
    
    print(f"🧪 Test de notification avec webhook: {webhook_url[:50]}...")
    
    # Créer une notification de test
    notifier = DiscordNotifier(default_webhook_url=webhook_url)
    
    try:
        await notifier.start()
        
        # Créer un faux watch (objet Watch)
        fake_watch = Watch(
            id="test-watch-123",
            name="tripack rivalité destinée",
            query="tripack rivalité destinée",
            vinted_domain="vinted.fr",
            max_price=25.0,
            currency="EUR",
            polling_interval_sec=45,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            notification_webhook=None,
            filters_json="{}",
            min_seller_rating=None,
            min_seller_feedback_count=None
        )
        
        # Créer un faux listing (objet Listing)
        fake_listing = Listing(
            listing_id="test-listing-123",
            title="🧪 TEST - Tripack Rivalité Destinée - Cartes Pokémon",
            price_amount=15.0,
            price_currency="EUR",
            url="https://www.vinted.fr/test-listing",
            thumbnail_url="https://via.placeholder.com/300x300.png?text=TEST",
            domain="vinted.fr",
            seller_rating=4.5,
            seller_feedback_count=100,
            condition="Très bon état",
            size="Unique",
            brand="Pokémon",
            posted_time=datetime.now()
        )
        
        # Envoyer la notification (ordre correct: watch, listing)
        success = await notifier.send_listing_notification(fake_watch, fake_listing)
        
        if success:
            print("✅ Notification de test envoyée avec succès!")
            print("📱 Vérifiez votre Discord pour voir la notification!")
        else:
            print("❌ Échec de l'envoi de la notification de test")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.stop()

if __name__ == '__main__':
    asyncio.run(test_notification())
