"""
Utility functions for logging, timing, and other common operations.
"""

import logging
import json
import random
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO", format_type: str = "text", log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration."""
    
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter based on format type
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create application logger
    logger = logging.getLogger('vinted_monitor')
    
    # Suppress noisy third-party loggers
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    return logger


def get_random_delay(min_ms: int, max_ms: int) -> float:
    """Get a random delay in seconds with jitter."""
    delay_ms = random.randint(min_ms, max_ms)
    return delay_ms / 1000.0


async def sleep_with_jitter(min_ms: int, max_ms: int) -> None:
    """Sleep for a random duration with jitter."""
    delay = get_random_delay(min_ms, max_ms)
    await asyncio.sleep(delay)


def normalize_price(price_text: str) -> tuple[Optional[float], Optional[str]]:
    """
    Extract price amount and currency from price text.
    
    Args:
        price_text: Price text like "€25.50", "$30.00", "25,50 €"
    
    Returns:
        Tuple of (amount, currency) or (None, None) if parsing fails
    """
    if not price_text:
        return None, None
    
    # Clean the text
    price_text = price_text.strip().replace('\xa0', ' ')  # Replace non-breaking space
    
    # Currency symbols mapping
    currency_symbols = {
        '€': 'EUR',
        '$': 'USD',
        '£': 'GBP',
        '¥': 'JPY',
        'zł': 'PLN',
        'Kč': 'CZK'
    }
    
    # Try to find currency symbol
    currency = None
    for symbol, code in currency_symbols.items():
        if symbol in price_text:
            currency = code
            price_text = price_text.replace(symbol, '').strip()
            break
    
    # If no symbol found, look for currency codes
    if not currency:
        for code in ['EUR', 'USD', 'GBP', 'JPY', 'PLN', 'CZK']:
            if code in price_text.upper():
                currency = code
                price_text = price_text.replace(code, '').replace(code.lower(), '').strip()
                break
    
    # Extract numeric value
    # Replace comma with dot for decimal separator
    price_text = price_text.replace(',', '.')
    
    # Remove any remaining non-numeric characters except dots
    import re
    numeric_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
    
    if not numeric_match:
        return None, None
    
    try:
        amount = float(numeric_match.group(1))
        return amount, currency
    except ValueError:
        return None, None


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    if not dt:
        return "Unknown"
    
    now = datetime.utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self) -> None:
        """Acquire permission to make a request, waiting if necessary."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # If we're at the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()  # Recursive call after waiting
        
        # Add current request
        self.requests.append(now)


class ExponentialBackoff:
    """Exponential backoff for retry logic."""
    
    def __init__(self, initial_delay: float = 1.0, max_delay: float = 60.0, multiplier: float = 2.0):
        """
        Initialize exponential backoff.
        
        Args:
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Backoff multiplier
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.current_delay = initial_delay
    
    async def wait(self) -> None:
        """Wait for the current delay and increase it."""
        await asyncio.sleep(self.current_delay)
        self.current_delay = min(self.current_delay * self.multiplier, self.max_delay)
    
    def reset(self) -> None:
        """Reset the delay to initial value."""
        self.current_delay = self.initial_delay


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def create_search_url(domain: str, query: str, filters: Dict[str, Any]) -> str:
    """
    Create Vinted search URL with query and filters.
    
    Args:
        domain: Vinted domain (e.g., 'vinted.fr')
        query: Search query
        filters: Dictionary of filters
    
    Returns:
        Complete search URL
    """
    from urllib.parse import urlencode, quote
    
    base_url = f"https://{domain}/catalog"
    
    params = {
        'search_text': query
    }
    
    # Add filters
    if 'max_price' in filters:
        params['price_to'] = filters['max_price']
    
    if 'price_from' in filters:
        params['price_from'] = filters['price_from']
    
    if 'order' in filters:
        params['order'] = filters['order']
    
    if 'category_ids' in filters and filters['category_ids']:
        params['catalog_ids'] = ','.join(map(str, filters['category_ids']))
    
    if 'brand_ids' in filters and filters['brand_ids']:
        params['brand_ids'] = ','.join(map(str, filters['brand_ids']))
    
    if 'size_ids' in filters and filters['size_ids']:
        params['size_ids'] = ','.join(map(str, filters['size_ids']))
    
    if 'condition_ids' in filters and filters['condition_ids']:
        params['status_ids'] = ','.join(map(str, filters['condition_ids']))
    
    # Build URL
    query_string = urlencode(params, quote_via=quote)
    return f"{base_url}?{query_string}"


def extract_listing_id_from_url(url: str) -> Optional[str]:
    """Extract listing ID from Vinted URL."""
    import re
    
    # Pattern for Vinted item URLs: /items/123456789-item-title
    match = re.search(r'/items/(\d+)', url)
    if match:
        return match.group(1)
    
    # Alternative pattern: data-item-id or similar
    match = re.search(r'item[_-]?id[_-]?(\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


def is_valid_webhook_url(url: str) -> bool:
    """Validate Discord webhook URL format."""
    import re
    
    if not url:
        return False
    
    # Discord webhook URL pattern
    pattern = r'https://discord\.com/api/webhooks/\d+/[\w-]+'
    return bool(re.match(pattern, url))


# Global logger instance
logger = setup_logging()
