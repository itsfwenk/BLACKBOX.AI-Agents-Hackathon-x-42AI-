"""
Configuration management for the Vinted monitoring service.
Handles .env files and YAML watch configurations.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

from .models import WatchConfig


@dataclass
class GlobalConfig:
    """Global configuration settings."""
    
    # Discord settings
    discord_webhook_url: Optional[str] = None
    
    # Polling settings
    default_poll_interval_sec: int = 30
    concurrency: int = 2
    max_pages_per_poll: int = 2
    
    # Browser settings
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headless: bool = True
    
    # Delay settings (in milliseconds)
    min_delay_ms: int = 800
    max_delay_ms: int = 2200
    
    # Currency conversion (optional)
    currency_api_url: Optional[str] = None
    currency_api_key: Optional[str] = None
    
    # Database settings
    database_path: str = "vinted_monitor.db"
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "text"  # "text" or "json"
    
    # Feature flags
    disable_images: bool = False
    enable_http_fallback: bool = False
    
    @classmethod
    def from_env(cls) -> 'GlobalConfig':
        """Load configuration from environment variables."""
        return cls(
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL'),
            default_poll_interval_sec=int(os.getenv('DEFAULT_POLL_INTERVAL_SEC', '30')),
            concurrency=int(os.getenv('CONCURRENCY', '2')),
            max_pages_per_poll=int(os.getenv('MAX_PAGES_PER_POLL', '2')),
            user_agent=os.getenv('USER_AGENT', cls.user_agent),
            headless=os.getenv('HEADLESS', 'true').lower() == 'true',
            min_delay_ms=int(os.getenv('MIN_DELAY_MS', '800')),
            max_delay_ms=int(os.getenv('MAX_DELAY_MS', '2200')),
            currency_api_url=os.getenv('CURRENCY_API_URL'),
            currency_api_key=os.getenv('CURRENCY_API_KEY'),
            database_path=os.getenv('DATABASE_PATH', 'vinted_monitor.db'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_format=os.getenv('LOG_FORMAT', 'text'),
            disable_images=os.getenv('DISABLE_IMAGES', 'false').lower() == 'true',
            enable_http_fallback=os.getenv('ENABLE_HTTP_FALLBACK', 'false').lower() == 'true'
        )


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, env_file: str = '.env', watches_file: str = 'config/watches.yaml'):
        self.env_file = env_file
        self.watches_file = watches_file
        self._global_config: Optional[GlobalConfig] = None
        self._watches: List[WatchConfig] = []
    
    def load_config(self) -> None:
        """Load all configuration."""
        self._load_env()
        self._load_global_config()
        self._load_watches()
        self._validate_config()
    
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
    
    def _load_global_config(self) -> None:
        """Load global configuration from environment."""
        self._global_config = GlobalConfig.from_env()
    
    def _load_watches(self) -> None:
        """Load watch configurations from YAML file."""
        if not os.path.exists(self.watches_file):
            print(f"Warning: Watches file {self.watches_file} not found. No watches will be loaded.")
            return
        
        try:
            with open(self.watches_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'watches' not in data:
                print("Warning: No watches found in configuration file.")
                return
            
            watches_data = data['watches']
            if not isinstance(watches_data, list):
                raise ValueError("Watches configuration must be a list")
            
            self._watches = []
            for watch_data in watches_data:
                try:
                    watch_config = WatchConfig(**watch_data)
                    self._watches.append(watch_config)
                except TypeError as e:
                    print(f"Error loading watch configuration: {e}")
                    print(f"Watch data: {watch_data}")
                    continue
            
            print(f"Loaded {len(self._watches)} watch configurations")
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {self.watches_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading watches from {self.watches_file}: {e}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        if not self._global_config:
            raise ValueError("Global configuration not loaded")
        
        # Validate Discord webhook
        if not self._global_config.discord_webhook_url and not any(w.notification_webhook for w in self._watches):
            raise ValueError("No Discord webhook URL configured globally or per-watch")
        
        # Validate watches
        for watch in self._watches:
            self._validate_watch(watch)
    
    def _validate_watch(self, watch: WatchConfig) -> None:
        """Validate a single watch configuration."""
        if not watch.name:
            raise ValueError("Watch name is required")
        
        if not watch.vinted_domain:
            raise ValueError(f"Vinted domain is required for watch '{watch.name}'")
        
        if not watch.query:
            raise ValueError(f"Query is required for watch '{watch.name}'")
        
        if watch.max_price <= 0:
            raise ValueError(f"Max price must be positive for watch '{watch.name}'")
        
        if watch.polling_interval_sec < 10:
            raise ValueError(f"Polling interval must be at least 10 seconds for watch '{watch.name}'")
        
        # Validate domain format
        valid_domains = ['vinted.fr', 'vinted.com', 'vinted.de', 'vinted.it', 'vinted.es', 'vinted.pl', 'vinted.lt', 'vinted.cz']
        if watch.vinted_domain not in valid_domains:
            print(f"Warning: Domain '{watch.vinted_domain}' for watch '{watch.name}' may not be supported")
        
        # Validate seller rating
        if watch.min_seller_rating is not None and (watch.min_seller_rating < 0 or watch.min_seller_rating > 5):
            raise ValueError(f"Seller rating must be between 0 and 5 for watch '{watch.name}'")
    
    @property
    def global_config(self) -> GlobalConfig:
        """Get global configuration."""
        if not self._global_config:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return self._global_config
    
    @property
    def watches(self) -> List[WatchConfig]:
        """Get watch configurations."""
        return self._watches.copy()
    
    def get_watch_by_name(self, name: str) -> Optional[WatchConfig]:
        """Get a watch configuration by name."""
        for watch in self._watches:
            if watch.name == name:
                return watch
        return None
    
    def reload_watches(self) -> None:
        """Reload watch configurations from file."""
        self._load_watches()
        # Re-validate only the watches
        for watch in self._watches:
            self._validate_watch(watch)


def create_example_config_files() -> None:
    """Create example configuration files."""
    
    # Create config directory
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    # Create .env.example
    env_example = """# Discord webhook URL (required)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Polling settings
DEFAULT_POLL_INTERVAL_SEC=30
CONCURRENCY=2
MAX_PAGES_PER_POLL=2

# Browser settings
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
HEADLESS=true

# Delay settings (milliseconds)
MIN_DELAY_MS=800
MAX_DELAY_MS=2200

# Currency conversion (optional)
# CURRENCY_API_URL=https://api.exchangerate-api.com/v4/latest/
# CURRENCY_API_KEY=your_api_key_here

# Database
DATABASE_PATH=vinted_monitor.db

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text

# Feature flags
DISABLE_IMAGES=false
ENABLE_HTTP_FALLBACK=false
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_example)
    
    # Create watches.yaml.example
    watches_example = """watches:
  - name: "Nike Air Force 1"
    vinted_domain: "vinted.fr"
    query: "nike air force 1"
    max_price: 50.0
    currency: "EUR"
    polling_interval_sec: 30
    filters:
      order: "newest_first"
      price_from: 10
      # Optional filters:
      # category_ids: [1234]
      # brand_ids: [5678]
      # size_ids: [42]
      # condition_ids: [1, 2, 3]  # 1=New, 2=Very good, 3=Good, etc.
    min_seller_feedback_count: 5
    min_seller_rating: 4.0
    notification_webhook: null  # Use global webhook

  - name: "Vintage Denim Jacket"
    vinted_domain: "vinted.com"
    query: "vintage denim jacket"
    max_price: 30.0
    currency: "USD"
    polling_interval_sec: 45
    filters:
      order: "price_low_to_high"
      price_from: 15
    min_seller_feedback_count: 10
    min_seller_rating: 4.5
    # notification_webhook: "https://discord.com/api/webhooks/DIFFERENT_WEBHOOK"
"""
    
    with open('config/watches.yaml.example', 'w') as f:
        f.write(watches_example)
    
    print("Created example configuration files:")
    print("- .env.example")
    print("- config/watches.yaml.example")
    print("\nCopy these to .env and config/watches.yaml and customize them.")


if __name__ == "__main__":
    create_example_config_files()
