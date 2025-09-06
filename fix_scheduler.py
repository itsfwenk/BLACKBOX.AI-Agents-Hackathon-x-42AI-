#!/usr/bin/env python3
"""
Script to fix the scheduler to prevent duplicate watches
"""

# This is the fix we need to apply to scheduler.py in the start method:

ORIGINAL_CODE = '''
# Save watches to database
for watch in watches:
    await self._db_store.save_watch(watch)
    self._watches[watch.id] = watch
'''

FIXED_CODE = '''
# Check for existing watches and avoid duplicates
for watch_config in watches:
    # Check if a watch with this name already exists
    existing_watches = await self._db_store.get_all_watches(active_only=False)
    existing_watch = None
    
    for existing in existing_watches:
        if existing.name == watch_config.name and existing.vinted_domain == watch_config.vinted_domain:
            existing_watch = existing
            break
    
    if existing_watch:
        # Update existing watch with new config
        existing_watch.query = watch_config.query
        existing_watch.max_price = watch_config.max_price
        existing_watch.currency = watch_config.currency
        existing_watch.polling_interval_sec = watch_config.polling_interval_sec
        existing_watch.notification_webhook = watch_config.notification_webhook
        existing_watch.min_seller_rating = watch_config.min_seller_rating
        existing_watch.min_seller_feedback_count = watch_config.min_seller_feedback_count
        existing_watch.filters = watch_config.filters
        existing_watch.active = True  # Ensure it's active
        
        await self._db_store.save_watch(existing_watch)
        self._watches[existing_watch.id] = existing_watch
        logger.info(f"Updated existing watch: {existing_watch.name}")
    else:
        # Create new watch
        await self._db_store.save_watch(watch_config)
        self._watches[watch_config.id] = watch_config
        logger.info(f"Created new watch: {watch_config.name}")
'''

print("🔧 Fix needed in app/scheduler.py")
print("📍 Location: start() method, around line 73-76")
print("\n🔴 Current problematic code:")
print(ORIGINAL_CODE)
print("\n🟢 Fixed code:")
print(FIXED_CODE)
print("\n💡 This will prevent duplicate watches from being created on each restart.")
