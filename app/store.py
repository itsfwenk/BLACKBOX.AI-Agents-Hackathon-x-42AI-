"""
SQLite database operations for the Vinted monitoring service.
Handles watches, seen listings, and notifications.
"""

import aiosqlite
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import Watch, SeenListing, Notification
from .utils import logger


class DatabaseStore:
    """SQLite database store for Vinted monitor data."""
    
    def __init__(self, db_path: str = "vinted_monitor.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database and create tables."""
        # Ensure database directory exists
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with self._lock:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
    
    async def close(self) -> None:
        """Close database connection."""
        async with self._lock:
            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("Database connection closed")
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        # Watches table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS watches (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                vinted_domain TEXT NOT NULL,
                query TEXT NOT NULL,
                max_price REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'EUR',
                filters_json TEXT NOT NULL DEFAULT '{}',
                polling_interval_sec INTEGER NOT NULL DEFAULT 30,
                notification_webhook TEXT,
                min_seller_feedback_count INTEGER,
                min_seller_rating REAL,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Seen listings table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS seen_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watch_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY (watch_id) REFERENCES watches (id) ON DELETE CASCADE,
                UNIQUE (watch_id, listing_id)
            )
        """)
        
        # Notifications table (for audit)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watch_id TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                notified_at TEXT NOT NULL,
                FOREIGN KEY (watch_id) REFERENCES watches (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_seen_listings_watch_id 
            ON seen_listings (watch_id)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_seen_listings_listing_id 
            ON seen_listings (listing_id)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_watch_id 
            ON notifications (watch_id)
        """)
        
        await self._connection.commit()
        logger.debug("Database tables created/verified")
    
    # Watch operations
    
    async def save_watch(self, watch: Watch) -> None:
        """Save or update a watch."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        watch.updated_at = datetime.utcnow()
        
        async with self._lock:
            await self._connection.execute("""
                INSERT OR REPLACE INTO watches (
                    id, name, vinted_domain, query, max_price, currency,
                    filters_json, polling_interval_sec, notification_webhook,
                    min_seller_feedback_count, min_seller_rating, active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                watch.id, watch.name, watch.vinted_domain, watch.query,
                watch.max_price, watch.currency, watch.filters_json,
                watch.polling_interval_sec, watch.notification_webhook,
                watch.min_seller_feedback_count, watch.min_seller_rating,
                watch.active, watch.created_at.isoformat(),
                watch.updated_at.isoformat()
            ))
            await self._connection.commit()
        
        logger.debug(f"Saved watch: {watch.name} ({watch.id})")
    
    async def get_watch(self, watch_id: str) -> Optional[Watch]:
        """Get a watch by ID."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            cursor = await self._connection.execute(
                "SELECT * FROM watches WHERE id = ?", (watch_id,)
            )
            row = await cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_watch(row)
    
    async def get_all_watches(self, active_only: bool = True) -> List[Watch]:
        """Get all watches."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        query = "SELECT * FROM watches"
        params = ()
        
        if active_only:
            query += " WHERE active = 1"
        
        query += " ORDER BY name"
        
        async with self._lock:
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
        
        return [self._row_to_watch(row) for row in rows]
    
    async def delete_watch(self, watch_id: str) -> bool:
        """Delete a watch and its associated data."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            # Delete associated seen listings and notifications
            await self._connection.execute(
                "DELETE FROM seen_listings WHERE watch_id = ?", (watch_id,)
            )
            await self._connection.execute(
                "DELETE FROM notifications WHERE watch_id = ?", (watch_id,)
            )
            
            # Delete the watch
            cursor = await self._connection.execute(
                "DELETE FROM watches WHERE id = ?", (watch_id,)
            )
            await self._connection.commit()
            
            deleted = cursor.rowcount > 0
        
        if deleted:
            logger.info(f"Deleted watch: {watch_id}")
        
        return deleted
    
    async def set_watch_active(self, watch_id: str, active: bool) -> bool:
        """Set watch active status."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            cursor = await self._connection.execute(
                "UPDATE watches SET active = ?, updated_at = ? WHERE id = ?",
                (active, datetime.utcnow().isoformat(), watch_id)
            )
            await self._connection.commit()
            
            updated = cursor.rowcount > 0
        
        if updated:
            logger.debug(f"Set watch {watch_id} active: {active}")
        
        return updated
    
    # Seen listings operations
    
    async def is_listing_seen(self, watch_id: str, listing_id: str) -> bool:
        """Check if a listing has been seen for a watch."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            cursor = await self._connection.execute(
                "SELECT 1 FROM seen_listings WHERE watch_id = ? AND listing_id = ?",
                (watch_id, listing_id)
            )
            row = await cursor.fetchone()
        
        return row is not None
    
    async def mark_listing_seen(self, watch_id: str, listing_id: str) -> None:
        """Mark a listing as seen for a watch."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        now = datetime.utcnow().isoformat()
        
        async with self._lock:
            await self._connection.execute("""
                INSERT OR REPLACE INTO seen_listings (
                    watch_id, listing_id, first_seen_at, last_seen_at
                ) VALUES (
                    ?, ?, 
                    COALESCE((SELECT first_seen_at FROM seen_listings 
                             WHERE watch_id = ? AND listing_id = ?), ?),
                    ?
                )
            """, (watch_id, listing_id, watch_id, listing_id, now, now))
            await self._connection.commit()
        
        logger.debug(f"Marked listing {listing_id} as seen for watch {watch_id}")
    
    async def get_seen_listings(self, watch_id: str) -> List[SeenListing]:
        """Get all seen listings for a watch."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            cursor = await self._connection.execute(
                "SELECT * FROM seen_listings WHERE watch_id = ? ORDER BY last_seen_at DESC",
                (watch_id,)
            )
            rows = await cursor.fetchall()
        
        return [self._row_to_seen_listing(row) for row in rows]
    
    async def clear_seen_listings(self, watch_id: str) -> int:
        """Clear all seen listings for a watch."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            cursor = await self._connection.execute(
                "DELETE FROM seen_listings WHERE watch_id = ?", (watch_id,)
            )
            await self._connection.commit()
            
            deleted_count = cursor.rowcount
        
        logger.info(f"Cleared {deleted_count} seen listings for watch {watch_id}")
        return deleted_count
    
    async def cleanup_old_seen_listings(self, days: int = 30) -> int:
        """Clean up seen listings older than specified days."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self._lock:
            cursor = await self._connection.execute(
                "DELETE FROM seen_listings WHERE last_seen_at < ?",
                (cutoff_date.isoformat(),)
            )
            await self._connection.commit()
            
            deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old seen listings")
        
        return deleted_count
    
    # Notification operations
    
    async def record_notification(self, watch_id: str, listing_id: str) -> None:
        """Record a notification for audit purposes."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        async with self._lock:
            await self._connection.execute(
                "INSERT INTO notifications (watch_id, listing_id, notified_at) VALUES (?, ?, ?)",
                (watch_id, listing_id, datetime.utcnow().isoformat())
            )
            await self._connection.commit()
        
        logger.debug(f"Recorded notification for listing {listing_id} in watch {watch_id}")
    
    async def get_notification_count(self, watch_id: str, hours: int = 24) -> int:
        """Get notification count for a watch in the last N hours."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with self._lock:
            cursor = await self._connection.execute(
                "SELECT COUNT(*) FROM notifications WHERE watch_id = ? AND notified_at > ?",
                (watch_id, cutoff_time.isoformat())
            )
            row = await cursor.fetchone()
        
        return row[0] if row else 0
    
    # Statistics and maintenance
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        
        stats = {}
        
        async with self._lock:
            # Watch counts
            cursor = await self._connection.execute("SELECT COUNT(*) FROM watches")
            stats['total_watches'] = (await cursor.fetchone())[0]
            
            cursor = await self._connection.execute("SELECT COUNT(*) FROM watches WHERE active = 1")
            stats['active_watches'] = (await cursor.fetchone())[0]
            
            # Seen listings count
            cursor = await self._connection.execute("SELECT COUNT(*) FROM seen_listings")
            stats['total_seen_listings'] = (await cursor.fetchone())[0]
            
            # Notifications count
            cursor = await self._connection.execute("SELECT COUNT(*) FROM notifications")
            stats['total_notifications'] = (await cursor.fetchone())[0]
            
            # Recent notifications (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            cursor = await self._connection.execute(
                "SELECT COUNT(*) FROM notifications WHERE notified_at > ?",
                (cutoff_time.isoformat(),)
            )
            stats['recent_notifications'] = (await cursor.fetchone())[0]
        
        return stats
    
    # Helper methods
    
    def _row_to_watch(self, row) -> Watch:
        """Convert database row to Watch object."""
        return Watch(
            id=row[0],
            name=row[1],
            vinted_domain=row[2],
            query=row[3],
            max_price=row[4],
            currency=row[5],
            filters_json=row[6],
            polling_interval_sec=row[7],
            notification_webhook=row[8],
            min_seller_feedback_count=row[9],
            min_seller_rating=row[10],
            active=bool(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13])
        )
    
    def _row_to_seen_listing(self, row) -> SeenListing:
        """Convert database row to SeenListing object."""
        return SeenListing(
            id=row[0],
            watch_id=row[1],
            listing_id=row[2],
            first_seen_at=datetime.fromisoformat(row[3]),
            last_seen_at=datetime.fromisoformat(row[4])
        )
    
    def _row_to_notification(self, row) -> Notification:
        """Convert database row to Notification object."""
        return Notification(
            id=row[0],
            watch_id=row[1],
            listing_id=row[2],
            notified_at=datetime.fromisoformat(row[3])
        )


# Global database instance
_db_store: Optional[DatabaseStore] = None


async def get_db_store(db_path: str = "vinted_monitor.db") -> DatabaseStore:
    """Get or create global database store instance."""
    global _db_store
    
    if _db_store is None:
        _db_store = DatabaseStore(db_path)
        await _db_store.initialize()
    
    return _db_store


async def close_db_store() -> None:
    """Close global database store instance."""
    global _db_store
    
    if _db_store:
        await _db_store.close()
        _db_store = None
