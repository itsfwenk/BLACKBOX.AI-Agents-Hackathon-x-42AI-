#!/usr/bin/env python3
"""
Script pour déboguer la base de données en temps réel
"""
import sqlite3
import time

def check_database():
    conn = sqlite3.connect('vinted_monitor.db')
    cursor = conn.cursor()
    
    print("=== ÉTAT DE LA BASE DE DONNÉES ===")
    
    # Compter les listings vus
    cursor.execute('SELECT COUNT(*) FROM seen_listings')
    seen_count = cursor.fetchone()[0]
    print(f"📊 Listings vus: {seen_count}")
    
    # Compter les notifications
    cursor.execute('SELECT COUNT(*) FROM notifications')
    notif_count = cursor.fetchone()[0]
    print(f"📱 Notifications envoyées: {notif_count}")
    
    # Voir les derniers listings vus (s'il y en a)
    if seen_count > 0:
        cursor.execute('SELECT watch_id, listing_id, first_seen_at FROM seen_listings ORDER BY first_seen_at DESC LIMIT 5')
        recent_seen = cursor.fetchall()
        print(f"📋 Derniers listings vus:")
        for watch_id, listing_id, seen_at in recent_seen:
            print(f"  - Watch: {watch_id[:8]}... | Listing: {listing_id} | Vu: {seen_at}")
    
    # Voir les watches dans la DB
    cursor.execute('SELECT id, name, active FROM watches')
    watches = cursor.fetchall()
    print(f"🎯 Watches dans la DB: {len(watches)}")
    for watch_id, name, active in watches:
        status = "✅ Actif" if active else "❌ Inactif"
        print(f"  - {name} ({watch_id[:8]}...) {status}")
    
    conn.close()

if __name__ == '__main__':
    while True:
        try:
            check_database()
            print("\n" + "="*50)
            time.sleep(10)  # Vérifier toutes les 10 secondes
        except KeyboardInterrupt:
            print("\n👋 Arrêt du monitoring")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(5)
