"""
Data models for the Vinted monitoring service.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
import json


@dataclass
class Watch:
    """Represents a watch configuration for monitoring Vinted listings."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    vinted_domain: str = ""
    query: str = ""
    max_price: float = 0.0
    currency: str = "EUR"
    filters_json: str = field(default_factory=lambda: "{}")
    polling_interval_sec: int = 30
    notification_webhook: Optional[str] = None
    min_seller_feedback_count: Optional[int] = None
    min_seller_rating: Optional[float] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def filters(self) -> Dict[str, Any]:
        """Parse filters from JSON string."""
        try:
            return json.loads(self.filters_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @filters.setter
    def filters(self, value: Dict[str, Any]):
        """Set filters as JSON string."""
        self.filters_json = json.dumps(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'name': self.name,
            'vinted_domain': self.vinted_domain,
            'query': self.query,
            'max_price': self.max_price,
            'currency': self.currency,
            'filters_json': self.filters_json,
            'polling_interval_sec': self.polling_interval_sec,
            'notification_webhook': self.notification_webhook,
            'min_seller_feedback_count': self.min_seller_feedback_count,
            'min_seller_rating': self.min_seller_rating,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Watch':
        """Create Watch from dictionary."""
        # Convert datetime strings back to datetime objects
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


@dataclass
class Listing:
    """Represents a Vinted listing."""
    
    listing_id: str
    title: str
    price_amount: float
    price_currency: str
    url: str
    thumbnail_url: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    condition: Optional[str] = None
    posted_time: Optional[datetime] = None
    seller_rating: Optional[float] = None
    seller_feedback_count: Optional[int] = None
    domain: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'listing_id': self.listing_id,
            'title': self.title,
            'price_amount': self.price_amount,
            'price_currency': self.price_currency,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'brand': self.brand,
            'size': self.size,
            'condition': self.condition,
            'posted_time': self.posted_time.isoformat() if self.posted_time else None,
            'seller_rating': self.seller_rating,
            'seller_feedback_count': self.seller_feedback_count,
            'domain': self.domain
        }


@dataclass
class SeenListing:
    """Represents a seen listing to prevent duplicate notifications."""
    
    id: Optional[int] = None
    watch_id: str = ""
    listing_id: str = ""
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    last_seen_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'watch_id': self.watch_id,
            'listing_id': self.listing_id,
            'first_seen_at': self.first_seen_at.isoformat(),
            'last_seen_at': self.last_seen_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SeenListing':
        """Create SeenListing from dictionary."""
        if isinstance(data.get('first_seen_at'), str):
            data['first_seen_at'] = datetime.fromisoformat(data['first_seen_at'])
        if isinstance(data.get('last_seen_at'), str):
            data['last_seen_at'] = datetime.fromisoformat(data['last_seen_at'])
        
        return cls(**data)


@dataclass
class Notification:
    """Represents a notification record for audit purposes."""
    
    id: Optional[int] = None
    watch_id: str = ""
    listing_id: str = ""
    notified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'watch_id': self.watch_id,
            'listing_id': self.listing_id,
            'notified_at': self.notified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create Notification from dictionary."""
        if isinstance(data.get('notified_at'), str):
            data['notified_at'] = datetime.fromisoformat(data['notified_at'])
        
        return cls(**data)


@dataclass
class WatchConfig:
    """Configuration for a watch loaded from YAML."""
    
    name: str
    vinted_domain: str
    query: str
    max_price: float
    currency: str = "EUR"
    polling_interval_sec: int = 30
    filters: Dict[str, Any] = field(default_factory=dict)
    notification_webhook: Optional[str] = None
    min_seller_feedback_count: Optional[int] = None
    min_seller_rating: Optional[float] = None
    
    def to_watch(self) -> Watch:
        """Convert to Watch model."""
        watch = Watch(
            name=self.name,
            vinted_domain=self.vinted_domain,
            query=self.query,
            max_price=self.max_price,
            currency=self.currency,
            polling_interval_sec=self.polling_interval_sec,
            notification_webhook=self.notification_webhook,
            min_seller_feedback_count=self.min_seller_feedback_count,
            min_seller_rating=self.min_seller_rating
        )
        watch.filters = self.filters
        return watch
