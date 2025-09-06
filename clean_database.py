#!/usr/bin/env python3
"""
Script pour nettoyer la base de données et supprimer les watches en double
"""
import sqlite3
from collections import defaultdict

def clean_database():
    conn = sqlite3.connect('vinted_monitor.db')
    cursor = conn.cursor()
    
    print("🧹 Nettoyage de la base de données...")
    
    # 1. Voir l'état actuel
    cursor.execute('SELECT COUNT(*) FROM watches')
    total_watches = cursor.fetchone()[0]
    print(f"📊 Watches actuelles: {total_watches}")
    
    # 2. Identifier les doublons par nom
    cursor.execute('SELECT id, name, created_at FROM watches ORDER BY name, created_at')
    all_watches = cursor.fetchall()
    
    # Grouper par nom
    watches_by_name = defaultdict(list)
    for watch_id, name, created_at in all_watches:
        watches_by_name[name].append((watch_id, created_at))
    
    # 3. Supprimer les doublons (garder le plus récent)
    watches_to_delete = []
    watches_to_keep = []
    
    for name, watches in watches_by_name.items():
        if len(watches) > 1:
            # Trier par date de création (plus récent en premier)
            watches.sort(key=lambda x: x[1], reverse=True)
            
            # Garder le plus récent
            keep_id = watches[0][0]
            watches_to_keep.append((keep_id, name))
            
            # Marquer les autres pour suppression
            for watch_id, _ in watches[1:]:
                watches_to_delete.append((watch_id, name))
                
            print(f"🔍 {name}: {len(watches)} doublons trouvés, gardé {keep_id[:8]}...")
        else:
            # Pas de doublon
            watches_to_keep.append((watches[0][0], name))
    
    # 4. Supprimer les doublons
    if watches_to_delete:
        print(f"🗑️  Suppression de {len(watches_to_delete)} watches en double...")
        
        for watch_id, name in watches_to_delete:
            # Supprimer les données liées
            cursor.execute('DELETE FROM seen_listings WHERE watch_id = ?', (watch_id,))
            cursor.execute('DELETE FROM notifications WHERE watch_id = ?', (watch_id,))
            cursor.execute('DELETE FROM watches WHERE id = ?', (watch_id,))
            print(f"  ❌ Supprimé: {name} ({watch_id[:8]}...)")
    
    # 5. Nettoyer aussi les tables liées
    cursor.execute('DELETE FROM seen_listings')
    cursor.execute('DELETE FROM notifications')
    print("🧽 Nettoyé les listings vus et notifications")
    
    # 6. Vérifier le résultat
    cursor.execute('SELECT COUNT(*) FROM watches')
    final_watches = cursor.fetchone()[0]
    
    cursor.execute('SELECT id, name FROM watches')
    remaining_watches = cursor.fetchall()
    
    print(f"\n✅ Nettoyage terminé!")
    print(f"📊 Watches restantes: {final_watches}")
    
    for watch_id, name in remaining_watches:
        print(f"  ✅ {name} ({watch_id[:8]}...)")
    
    # Sauvegarder les changements
    conn.commit()
    conn.close()
    
    print(f"\n🎯 Base de données nettoyée: {total_watches} → {final_watches} watches")

if __name__ == '__main__':
    clean_database()
