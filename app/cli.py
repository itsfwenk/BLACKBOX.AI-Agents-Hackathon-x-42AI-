"""
Command-line interface for the Vinted monitoring service.
"""

import asyncio
import click
import json
from typing import Optional, List
from pathlib import Path

from .config import ConfigManager, create_example_config_files
from .models import Watch, WatchConfig
from .store import get_db_store, close_db_store
from .scraper import BrowserManager, VintedScraper
from .notifier import DiscordNotifier
from .currency import get_currency_converter, close_currency_converter
from .scheduler import WatchScheduler
from .utils import setup_logging, logger


@click.group()
@click.option('--config-dir', default='config', help='Configuration directory')
@click.option('--env-file', default='.env', help='Environment file path')
@click.option('--log-level', default='INFO', help='Log level')
@click.option('--log-format', default='text', help='Log format (text or json)')
@click.pass_context
def cli(ctx, config_dir: str, env_file: str, log_level: str, log_format: str):
    """Vinted Monitor - Monitor Vinted listings and send Discord notifications."""
    ctx.ensure_object(dict)
    
    # Set up logging
    setup_logging(level=log_level, format_type=log_format)
    
    # Store config paths in context
    ctx.obj['config_dir'] = config_dir
    ctx.obj['env_file'] = env_file
    ctx.obj['watches_file'] = f"{config_dir}/watches.yaml"


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize configuration files."""
    try:
        create_example_config_files()
        click.echo("✅ Configuration files created successfully!")
        click.echo("\nNext steps:")
        click.echo("1. Copy .env.example to .env and configure your Discord webhook")
        click.echo("2. Copy config/watches.yaml.example to config/watches.yaml and add your watches")
        click.echo("3. Run 'vinted-monitor run' to start the service")
        
    except Exception as e:
        click.echo(f"❌ Error creating configuration files: {e}")
        raise click.Abort()


@cli.command()
@click.option('--daemon', is_flag=True, help='Run as daemon (background process)')
@click.pass_context
def run(ctx, daemon: bool):
    """Run the Vinted monitoring service."""
    if daemon:
        click.echo("❌ Daemon mode not implemented yet. Run without --daemon flag.")
        raise click.Abort()
    
    try:
        asyncio.run(_run_service(ctx.obj))
    except KeyboardInterrupt:
        click.echo("\n🛑 Service stopped by user")
    except Exception as e:
        click.echo(f"❌ Service error: {e}")
        raise click.Abort()


@cli.command()
@click.pass_context
def status(ctx):
    """Show service status and statistics."""
    try:
        asyncio.run(_show_status(ctx.obj))
    except Exception as e:
        click.echo(f"❌ Error getting status: {e}")
        raise click.Abort()


@cli.command()
@click.pass_context
def list_watches(ctx):
    """List all configured watches."""
    try:
        asyncio.run(_list_watches(ctx.obj))
    except Exception as e:
        click.echo(f"❌ Error listing watches: {e}")
        raise click.Abort()


@cli.command()
@click.argument('watch_name')
@click.option('--dry-run', is_flag=True, help='Test without sending notifications')
@click.pass_context
def test_watch(ctx, watch_name: str, dry_run: bool):
    """Test a specific watch."""
    try:
        asyncio.run(_test_watch(ctx.obj, watch_name, dry_run))
    except Exception as e:
        click.echo(f"❌ Error testing watch: {e}")
        raise click.Abort()


@cli.command()
@click.argument('watch_name')
@click.pass_context
def clear_seen(ctx, watch_name: str):
    """Clear seen listings for a watch."""
    try:
        asyncio.run(_clear_seen_listings(ctx.obj, watch_name))
    except Exception as e:
        click.echo(f"❌ Error clearing seen listings: {e}")
        raise click.Abort()


@cli.command()
@click.option('--webhook-url', help='Discord webhook URL to test')
@click.pass_context
def test_webhook(ctx, webhook_url: Optional[str]):
    """Test Discord webhook connectivity."""
    try:
        asyncio.run(_test_webhook(ctx.obj, webhook_url))
    except Exception as e:
        click.echo(f"❌ Error testing webhook: {e}")
        raise click.Abort()


@cli.command()
@click.argument('domain')
@click.pass_context
def test_domain(ctx, domain: str):
    """Test if a Vinted domain is accessible."""
    try:
        asyncio.run(_test_domain(ctx.obj, domain))
    except Exception as e:
        click.echo(f"❌ Error testing domain: {e}")
        raise click.Abort()


@cli.command()
@click.option('--days', default=30, help='Days of data to keep')
@click.pass_context
def cleanup(ctx, days: int):
    """Clean up old data from database."""
    try:
        asyncio.run(_cleanup_data(ctx.obj, days))
    except Exception as e:
        click.echo(f"❌ Error cleaning up data: {e}")
        raise click.Abort()


async def _run_service(config_paths: dict):
    """Run the main monitoring service."""
    click.echo("🚀 Starting Vinted Monitor...")
    
    # Load configuration
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}")
        return
    
    global_config = config_manager.global_config
    watch_configs = config_manager.watches
    
    if not watch_configs:
        click.echo("⚠️  No watches configured. Add watches to config/watches.yaml")
        return
    
    click.echo(f"📋 Loaded {len(watch_configs)} watches")
    
    # Initialize components
    browser_manager = BrowserManager(
        headless=global_config.headless,
        user_agent=global_config.user_agent,
        concurrency=global_config.concurrency
    )
    
    scraper = VintedScraper(
        browser_manager=browser_manager,
        min_delay_ms=global_config.min_delay_ms,
        max_delay_ms=global_config.max_delay_ms,
        max_pages_per_poll=global_config.max_pages_per_poll
    )
    
    notifier = DiscordNotifier(
        default_webhook_url=global_config.discord_webhook_url,
        disable_images=global_config.disable_images
    )
    
    currency_converter = None
    if global_config.currency_api_url:
        currency_converter = get_currency_converter(
            api_url=global_config.currency_api_url,
            api_key=global_config.currency_api_key
        )
    
    # Convert watch configs to watches
    watches = [config.to_watch() for config in watch_configs]
    
    # Create and start scheduler
    scheduler = WatchScheduler(
        global_config=global_config,
        browser_manager=browser_manager,
        scraper=scraper,
        notifier=notifier,
        currency_converter=currency_converter
    )
    
    try:
        await scheduler.start(watches)
        
        click.echo("✅ Service started successfully!")
        click.echo("📊 Press Ctrl+C to stop the service")
        
        # Keep running until interrupted
        while scheduler._running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping service...")
    finally:
        await scheduler.stop()
        await close_db_store()
        await close_currency_converter()
        click.echo("✅ Service stopped cleanly")


async def _show_status(config_paths: dict):
    """Show service status."""
    # Load configuration to get database path
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        # Get database stats
        db_store = await get_db_store(global_config.database_path)
        stats = await db_store.get_stats()
        
        click.echo("📊 Vinted Monitor Status")
        click.echo("=" * 40)
        click.echo(f"Database: {global_config.database_path}")
        click.echo(f"Total watches: {stats['total_watches']}")
        click.echo(f"Active watches: {stats['active_watches']}")
        click.echo(f"Seen listings: {stats['total_seen_listings']}")
        click.echo(f"Total notifications: {stats['total_notifications']}")
        click.echo(f"Recent notifications (24h): {stats['recent_notifications']}")
        
        await close_db_store()
        
    except Exception as e:
        click.echo(f"❌ Error getting status: {e}")


async def _list_watches(config_paths: dict):
    """List all watches."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        db_store = await get_db_store(global_config.database_path)
        watches = await db_store.get_all_watches(active_only=False)
        
        if not watches:
            click.echo("📭 No watches found")
            return
        
        click.echo(f"📋 Found {len(watches)} watches:")
        click.echo("=" * 80)
        
        for watch in watches:
            status = "🟢 Active" if watch.active else "🔴 Inactive"
            click.echo(f"{status} {watch.name}")
            click.echo(f"   Query: {watch.query}")
            click.echo(f"   Domain: {watch.vinted_domain}")
            click.echo(f"   Max Price: {watch.max_price} {watch.currency}")
            click.echo(f"   Interval: {watch.polling_interval_sec}s")
            click.echo()
        
        await close_db_store()
        
    except Exception as e:
        click.echo(f"❌ Error listing watches: {e}")


async def _test_watch(config_paths: dict, watch_name: str, dry_run: bool):
    """Test a specific watch."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        # Find watch by name
        watch_config = config_manager.get_watch_by_name(watch_name)
        if not watch_config:
            click.echo(f"❌ Watch '{watch_name}' not found")
            return
        
        watch = watch_config.to_watch()
        
        click.echo(f"🧪 Testing watch: {watch.name}")
        click.echo(f"   Query: {watch.query}")
        click.echo(f"   Domain: {watch.vinted_domain}")
        click.echo(f"   Max Price: {watch.max_price} {watch.currency}")
        
        # Initialize components
        browser_manager = BrowserManager(
            headless=global_config.headless,
            user_agent=global_config.user_agent,
            concurrency=1
        )
        
        scraper = VintedScraper(
            browser_manager=browser_manager,
            min_delay_ms=global_config.min_delay_ms,
            max_delay_ms=global_config.max_delay_ms,
            max_pages_per_poll=1  # Only test first page
        )
        
        try:
            await browser_manager.start()
            
            # Test scrape
            result = await scraper.test_scrape(watch, dry_run=dry_run)
            
            if result['success']:
                click.echo(f"✅ Test completed in {result['duration_seconds']}s")
                click.echo(f"📦 Found {result['listings_found']} listings")
                
                if result.get('price_stats'):
                    stats = result['price_stats']
                    click.echo(f"💰 Price range: {stats['min_price']} - {stats['max_price']} (avg: {stats['avg_price']})")
                
                if result.get('sample_listings'):
                    click.echo("\n📋 Sample listings:")
                    for i, listing in enumerate(result['sample_listings'][:3], 1):
                        click.echo(f"   {i}. {listing['title'][:60]}...")
                        click.echo(f"      Price: {listing['price']} | {listing['url']}")
            else:
                click.echo(f"❌ Test failed: {result.get('error', 'Unknown error')}")
                
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        click.echo(f"❌ Error testing watch: {e}")


async def _clear_seen_listings(config_paths: dict, watch_name: str):
    """Clear seen listings for a watch."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        # Find watch by name
        watch_config = config_manager.get_watch_by_name(watch_name)
        if not watch_config:
            click.echo(f"❌ Watch '{watch_name}' not found")
            return
        
        db_store = await get_db_store(global_config.database_path)
        
        # Find watch in database
        watches = await db_store.get_all_watches(active_only=False)
        target_watch = None
        
        for watch in watches:
            if watch.name == watch_name:
                target_watch = watch
                break
        
        if not target_watch:
            click.echo(f"❌ Watch '{watch_name}' not found in database")
            return
        
        # Clear seen listings
        count = await db_store.clear_seen_listings(target_watch.id)
        click.echo(f"✅ Cleared {count} seen listings for watch '{watch_name}'")
        
        await close_db_store()
        
    except Exception as e:
        click.echo(f"❌ Error clearing seen listings: {e}")


async def _test_webhook(config_paths: dict, webhook_url: Optional[str]):
    """Test Discord webhook."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        # Use provided URL or default
        test_url = webhook_url or global_config.discord_webhook_url
        
        if not test_url:
            click.echo("❌ No webhook URL provided. Use --webhook-url or set DISCORD_WEBHOOK_URL")
            return
        
        click.echo(f"🧪 Testing webhook: {test_url[:50]}...")
        
        notifier = DiscordNotifier(default_webhook_url=test_url)
        
        try:
            await notifier.start()
            success = await notifier.test_webhook()
            
            if success:
                click.echo("✅ Webhook test successful!")
            else:
                click.echo("❌ Webhook test failed")
                
        finally:
            await notifier.stop()
        
    except Exception as e:
        click.echo(f"❌ Error testing webhook: {e}")


async def _test_domain(config_paths: dict, domain: str):
    """Test Vinted domain accessibility."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        click.echo(f"🧪 Testing domain: {domain}")
        
        browser_manager = BrowserManager(
            headless=global_config.headless,
            user_agent=global_config.user_agent,
            concurrency=1
        )
        
        scraper = VintedScraper(
            browser_manager=browser_manager,
            min_delay_ms=global_config.min_delay_ms,
            max_delay_ms=global_config.max_delay_ms
        )
        
        try:
            await browser_manager.start()
            
            domain_info = await scraper.get_domain_info(domain)
            
            if domain_info['accessible']:
                click.echo(f"✅ Domain {domain} is accessible")
                click.echo(f"   Base URL: {domain_info['base_url']}")
                click.echo(f"   Default Currency: {domain_info['default_currency']}")
            else:
                click.echo(f"❌ Domain {domain} is not accessible")
                if 'error' in domain_info:
                    click.echo(f"   Error: {domain_info['error']}")
                    
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        click.echo(f"❌ Error testing domain: {e}")


async def _cleanup_data(config_paths: dict, days: int):
    """Clean up old data."""
    config_manager = ConfigManager(
        env_file=config_paths['env_file'],
        watches_file=config_paths['watches_file']
    )
    
    try:
        config_manager.load_config()
        global_config = config_manager.global_config
        
        click.echo(f"🧹 Cleaning up data older than {days} days...")
        
        db_store = await get_db_store(global_config.database_path)
        cleaned = await db_store.cleanup_old_seen_listings(days)
        
        click.echo(f"✅ Cleaned up {cleaned} old seen listings")
        
        await close_db_store()
        
    except Exception as e:
        click.echo(f"❌ Error cleaning up data: {e}")


if __name__ == '__main__':
    cli()
