"""
Tests for database store operations.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from datetime import datetime, timedelta

from app.store import DatabaseStore
from app.models import Watch, SeenListing


@pytest_asyncio.fixture
async def db_store():
    """Create a temporary database store for testing."""
    # Create temporary database file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_fd)
    
    store = DatabaseStore(temp_path)
    await store.initialize()
    
    try:
        yield store
    finally:
        await store.close()
        
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


@pytest.fixture
def sample_watch():
    """Create a sample watch for testing."""
    return Watch(
        id="test-watch-1",
        name="Test Watch",
        vinted_domain="vinted.fr",
        query="test item",
        max_price=50.0,
        currency="EUR",
        polling_interval_sec=30,
        active=True
    )


class TestWatchOperations:
    """Test watch database operations."""
    
    @pytest.mark.asyncio
    async def test_save_and_get_watch(self, db_store, sample_watch):
        """Test saving and retrieving a watch."""
        # Save watch
        await db_store.save_watch(sample_watch)
        
        # Retrieve watch
        retrieved_watch = await db_store.get_watch(sample_watch.id)
        
        assert retrieved_watch is not None
        assert retrieved_watch.id == sample_watch.id
        assert retrieved_watch.name == sample_watch.name
        assert retrieved_watch.query == sample_watch.query
        assert retrieved_watch.max_price == sample_watch.max_price
        assert retrieved_watch.active == sample_watch.active
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_watch(self, db_store):
        """Test retrieving a non-existent watch."""
        watch = await db_store.get_watch("nonexistent-id")
        assert watch is None
    
    @pytest.mark.asyncio
    async def test_get_all_watches(self, db_store, sample_watch):
        """Test retrieving all watches."""
        # Initially empty
        watches = await db_store.get_all_watches()
        assert len(watches) == 0
        
        # Add watch
        await db_store.save_watch(sample_watch)
        
        # Should have one watch
        watches = await db_store.get_all_watches()
        assert len(watches) == 1
        assert watches[0].id == sample_watch.id
    
    @pytest.mark.asyncio
    async def test_get_active_watches_only(self, db_store):
        """Test retrieving only active watches."""
        # Create active and inactive watches
        active_watch = Watch(
            id="active-watch",
            name="Active Watch",
            vinted_domain="vinted.fr",
            query="active",
            max_price=30.0,
            active=True
        )
        
        inactive_watch = Watch(
            id="inactive-watch",
            name="Inactive Watch",
            vinted_domain="vinted.fr",
            query="inactive",
            max_price=30.0,
            active=False
        )
        
        await db_store.save_watch(active_watch)
        await db_store.save_watch(inactive_watch)
        
        # Get all watches
        all_watches = await db_store.get_all_watches(active_only=False)
        assert len(all_watches) == 2
        
        # Get only active watches
        active_watches = await db_store.get_all_watches(active_only=True)
        assert len(active_watches) == 1
        assert active_watches[0].id == "active-watch"
    
    @pytest.mark.asyncio
    async def test_update_watch(self, db_store, sample_watch):
        """Test updating a watch."""
        # Save initial watch
        await db_store.save_watch(sample_watch)
        
        # Update watch
        sample_watch.name = "Updated Watch Name"
        sample_watch.max_price = 75.0
        await db_store.save_watch(sample_watch)
        
        # Retrieve updated watch
        updated_watch = await db_store.get_watch(sample_watch.id)
        assert updated_watch.name == "Updated Watch Name"
        assert updated_watch.max_price == 75.0
    
    @pytest.mark.asyncio
    async def test_delete_watch(self, db_store, sample_watch):
        """Test deleting a watch."""
        # Save watch
        await db_store.save_watch(sample_watch)
        
        # Verify it exists
        watch = await db_store.get_watch(sample_watch.id)
        assert watch is not None
        
        # Delete watch
        deleted = await db_store.delete_watch(sample_watch.id)
        assert deleted is True
        
        # Verify it's gone
        watch = await db_store.get_watch(sample_watch.id)
        assert watch is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_watch(self, db_store):
        """Test deleting a non-existent watch."""
        deleted = await db_store.delete_watch("nonexistent-id")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_set_watch_active(self, db_store, sample_watch):
        """Test setting watch active status."""
        # Save watch as active
        await db_store.save_watch(sample_watch)
        
        # Set inactive
        updated = await db_store.set_watch_active(sample_watch.id, False)
        assert updated is True
        
        # Verify status changed
        watch = await db_store.get_watch(sample_watch.id)
        assert watch.active is False
        
        # Set active again
        updated = await db_store.set_watch_active(sample_watch.id, True)
        assert updated is True
        
        # Verify status changed
        watch = await db_store.get_watch(sample_watch.id)
        assert watch.active is True


class TestSeenListingsOperations:
    """Test seen listings database operations."""
    
    @pytest.mark.asyncio
    async def test_mark_and_check_listing_seen(self, db_store, sample_watch):
        """Test marking and checking seen listings."""
        await db_store.save_watch(sample_watch)
        
        listing_id = "test-listing-123"
        
        # Initially not seen
        is_seen = await db_store.is_listing_seen(sample_watch.id, listing_id)
        assert is_seen is False
        
        # Mark as seen
        await db_store.mark_listing_seen(sample_watch.id, listing_id)
        
        # Should now be seen
        is_seen = await db_store.is_listing_seen(sample_watch.id, listing_id)
        assert is_seen is True
    
    @pytest.mark.asyncio
    async def test_mark_listing_seen_twice(self, db_store, sample_watch):
        """Test marking the same listing as seen twice."""
        await db_store.save_watch(sample_watch)
        
        listing_id = "test-listing-456"
        
        # Mark as seen twice
        await db_store.mark_listing_seen(sample_watch.id, listing_id)
        await db_store.mark_listing_seen(sample_watch.id, listing_id)
        
        # Should still be seen (no error)
        is_seen = await db_store.is_listing_seen(sample_watch.id, listing_id)
        assert is_seen is True
    
    @pytest.mark.asyncio
    async def test_get_seen_listings(self, db_store, sample_watch):
        """Test retrieving seen listings for a watch."""
        await db_store.save_watch(sample_watch)
        
        # Mark multiple listings as seen
        listing_ids = ["listing-1", "listing-2", "listing-3"]
        for listing_id in listing_ids:
            await db_store.mark_listing_seen(sample_watch.id, listing_id)
        
        # Get seen listings
        seen_listings = await db_store.get_seen_listings(sample_watch.id)
        
        assert len(seen_listings) == 3
        seen_ids = [sl.listing_id for sl in seen_listings]
        for listing_id in listing_ids:
            assert listing_id in seen_ids
    
    @pytest.mark.asyncio
    async def test_clear_seen_listings(self, db_store, sample_watch):
        """Test clearing seen listings for a watch."""
        await db_store.save_watch(sample_watch)
        
        # Mark listings as seen
        listing_ids = ["listing-1", "listing-2"]
        for listing_id in listing_ids:
            await db_store.mark_listing_seen(sample_watch.id, listing_id)
        
        # Verify they exist
        seen_listings = await db_store.get_seen_listings(sample_watch.id)
        assert len(seen_listings) == 2
        
        # Clear seen listings
        cleared_count = await db_store.clear_seen_listings(sample_watch.id)
        assert cleared_count == 2
        
        # Verify they're gone
        seen_listings = await db_store.get_seen_listings(sample_watch.id)
        assert len(seen_listings) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_seen_listings(self, db_store, sample_watch):
        """Test cleaning up old seen listings."""
        await db_store.save_watch(sample_watch)
        
        # Mark a listing as seen
        await db_store.mark_listing_seen(sample_watch.id, "old-listing")
        
        # Manually update the timestamp to be old
        # (This is a bit hacky but necessary for testing)
        old_date = datetime.utcnow() - timedelta(days=35)
        await db_store._connection.execute(
            "UPDATE seen_listings SET last_seen_at = ? WHERE listing_id = ?",
            (old_date.isoformat(), "old-listing")
        )
        await db_store._connection.commit()
        
        # Add a recent listing
        await db_store.mark_listing_seen(sample_watch.id, "recent-listing")
        
        # Clean up old listings (30 days)
        cleaned_count = await db_store.cleanup_old_seen_listings(30)
        assert cleaned_count == 1
        
        # Verify only recent listing remains
        seen_listings = await db_store.get_seen_listings(sample_watch.id)
        assert len(seen_listings) == 1
        assert seen_listings[0].listing_id == "recent-listing"


class TestNotificationOperations:
    """Test notification database operations."""
    
    @pytest.mark.asyncio
    async def test_record_notification(self, db_store, sample_watch):
        """Test recording a notification."""
        await db_store.save_watch(sample_watch)
        
        # Record notification
        await db_store.record_notification(sample_watch.id, "test-listing")
        
        # Check notification count
        count = await db_store.get_notification_count(sample_watch.id, hours=24)
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_get_notification_count(self, db_store, sample_watch):
        """Test getting notification count."""
        await db_store.save_watch(sample_watch)
        
        # Record multiple notifications
        for i in range(3):
            await db_store.record_notification(sample_watch.id, f"listing-{i}")
        
        # Check count
        count = await db_store.get_notification_count(sample_watch.id, hours=24)
        assert count == 3


class TestDatabaseStats:
    """Test database statistics."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, db_store, sample_watch):
        """Test getting database statistics."""
        # Initially empty
        stats = await db_store.get_stats()
        assert stats['total_watches'] == 0
        assert stats['active_watches'] == 0
        assert stats['total_seen_listings'] == 0
        assert stats['total_notifications'] == 0
        
        # Add data
        await db_store.save_watch(sample_watch)
        await db_store.mark_listing_seen(sample_watch.id, "test-listing")
        await db_store.record_notification(sample_watch.id, "test-listing")
        
        # Check updated stats
        stats = await db_store.get_stats()
        assert stats['total_watches'] == 1
        assert stats['active_watches'] == 1
        assert stats['total_seen_listings'] == 1
        assert stats['total_notifications'] == 1


if __name__ == "__main__":
    pytest.main([__file__])
