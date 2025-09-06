#!/usr/bin/env python3
"""
Script pour monitorer la précision des nouvelles recherches
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
import time

async def monitor_precision():
    """Monitor les notifications et leur fréquence"""
    
    print("🔍 MONITORING DE LA PRÉCISION DES RECHERCHES")
    print("=" * 60)
    
    last_notification_count = 0
    start_time = datetime.now()
    
    while True:
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('vinted_monitor.db')
            cursor = conn.cursor()
            
            # Compter les notifications des 10 dernières minutes
            ten_minutes_ago = datetime.now() - timedelta(minutes=10)
            cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE created_at > ?
            """, (ten_minutes_ago.isoformat(),))
            
            recent_notifications = cursor.fetchone()[0]
            
            # Compter le total des notifications
            cursor.execute("SELECT COUNT(*) FROM notifications")
            total_notifications = cursor.fetchone()[0]
            
            # Compter les listings vus récemment
            cursor.execute("""
                SELECT COUNT(*) FROM seen_listings 
                WHERE seen_at > ?
            """, (ten_minutes_ago.isoformat(),))
            
            recent_seen = cursor.fetchone()[0]
            
            # Statistiques par watch
            cursor.execute("""
                SELECT w.name, COUNT(n.id) as notification_count
                FROM watches w
                LEFT JOIN notifications n ON w.id = n.watch_id 
                WHERE n.created_at > ? OR n.created_at IS NULL
                GROUP BY w.id, w.name
                ORDER BY notification_count DESC
            """, (ten_minutes_ago.isoformat(),))
            
            watch_stats = cursor.fetchall()
            
            conn.close()
            
            # Affichage des stats
            current_time = datetime.now().strftime("%H:%M:%S")
            runtime = datetime.now() - start_time
            
            print(f"\n⏰ {current_time} | Runtime: {str(runtime).split('.')[0]}")
            print(f"📊 Notifications (10 min): {recent_notifications}")
            print(f"📦 Listings vus (10 min): {recent_seen}")
            print(f"🎯 Total notifications: {total_notifications}")
            
            if recent_notifications > 0:
                precision_ratio = recent_notifications / max(recent_seen, 1) * 100
                print(f"🎯 Ratio précision: {precision_ratio:.1f}%")
            
            print("\n📋 Par watch (10 min):")
            for watch_name, count in watch_stats:
                print(f"  - {watch_name}: {count} notifications")
            
            # Alertes
            if recent_notifications > 20:
                print("⚠️  ALERTE: Trop de notifications (>20 en 10min)")
            elif recent_notifications > 0:
                print("✅ Notifications modérées")
            else:
                print("🔇 Aucune notification récente")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Erreur monitoring: {e}")
        
        # Attendre 30 secondes avant la prochaine vérification
        await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_precision())
    except KeyboardInterrupt:
        print("\n👋 Arrêt du monitoring")
