"""
Tests for filtering and currency conversion logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models import Watch, Listing
from app.currency import CurrencyConverter
from app.scheduler import WatchScheduler


@pytest.fixture
def sample_watch():
    """Create a sample watch for testing."""
    return Watch(
        id="test-watch",
        name="Test Watch",
        vinted_domain="vinted.fr",
        query="test item",
        max_price=50.0,
        currency="EUR",
        min_seller_rating=4.0,
        min_seller_feedback_count=10,
        active=True
    )


@pytest.fixture
def sample_listing():
    """Create a sample listing for testing."""
    return Listing(
        listing_id="123456",
        title="Test Item",
        price_amount=30.0,
        price_currency="EUR",
        url="https://vinted.fr/items/123456",
        seller_rating=4.5,
        seller_feedback_count=25,
        domain="vinted.fr"
    )


class TestPriceFiltering:
    """Test price filtering logic."""
    
    @pytest.mark.asyncio
    async def test_price_filter_same_currency_pass(self, sample_watch, sample_listing):
        """Test price filter with same currency - should pass."""
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = None
        
        # Listing price (30) is less than max price (50)
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_price_filter_same_currency_fail(self, sample_watch, sample_listing):
        """Test price filter with same currency - should fail."""
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = None
        
        # Set listing price higher than max price
        sample_listing.price_amount = 60.0
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_price_filter_same_currency_exact(self, sample_watch, sample_listing):
        """Test price filter with exact max price - should pass."""
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = None
        
        # Set listing price equal to max price
        sample_listing.price_amount = 50.0
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_price_filter_different_currency_no_converter(self, sample_watch, sample_listing):
        """Test price filter with different currency and no converter - should fail."""
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = None
        
        # Set different currency
        sample_listing.price_currency = "USD"
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_price_filter_with_currency_conversion_pass(self, sample_watch, sample_listing):
        """Test price filter with currency conversion - should pass."""
        # Create mock converter
        mock_converter = AsyncMock()
        mock_converter.convert.return_value = 35.0  # Converted price within limit
        
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = mock_converter
        
        # Set different currency
        sample_listing.price_currency = "USD"
        sample_listing.price_amount = 40.0
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is True
        
        # Verify conversion was called
        mock_converter.convert.assert_called_once_with(40.0, "USD", "EUR")
    
    @pytest.mark.asyncio
    async def test_price_filter_with_currency_conversion_fail(self, sample_watch, sample_listing):
        """Test price filter with currency conversion - should fail."""
        # Create mock converter
        mock_converter = AsyncMock()
        mock_converter.convert.return_value = 60.0  # Converted price over limit
        
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = mock_converter
        
        # Set different currency
        sample_listing.price_currency = "USD"
        sample_listing.price_amount = 55.0
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_price_filter_conversion_failure(self, sample_watch, sample_listing):
        """Test price filter when currency conversion fails."""
        # Create mock converter that returns None (conversion failed)
        mock_converter = AsyncMock()
        mock_converter.convert.return_value = None
        
        # Create mock scheduler
        scheduler = MagicMock()
        scheduler.currency_converter = mock_converter
        
        # Set different currency
        sample_listing.price_currency = "USD"
        
        result = await WatchScheduler._check_price_filter(scheduler, sample_watch, sample_listing)
        assert result is False


class TestSellerFiltering:
    """Test seller filtering logic."""
    
    def test_seller_filter_rating_pass(self, sample_watch, sample_listing):
        """Test seller rating filter - should pass."""
        # Listing rating (4.5) is higher than min rating (4.0)
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is True
    
    def test_seller_filter_rating_fail(self, sample_watch, sample_listing):
        """Test seller rating filter - should fail."""
        # Set listing rating lower than minimum
        sample_listing.seller_rating = 3.5
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is False
    
    def test_seller_filter_rating_exact(self, sample_watch, sample_listing):
        """Test seller rating filter with exact minimum - should pass."""
        # Set listing rating equal to minimum
        sample_listing.seller_rating = 4.0
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is True
    
    def test_seller_filter_feedback_count_pass(self, sample_watch, sample_listing):
        """Test seller feedback count filter - should pass."""
        # Listing feedback count (25) is higher than min count (10)
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is True
    
    def test_seller_filter_feedback_count_fail(self, sample_watch, sample_listing):
        """Test seller feedback count filter - should fail."""
        # Set listing feedback count lower than minimum
        sample_listing.seller_feedback_count = 5
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is False
    
    def test_seller_filter_feedback_count_exact(self, sample_watch, sample_listing):
        """Test seller feedback count filter with exact minimum - should pass."""
        # Set listing feedback count equal to minimum
        sample_listing.seller_feedback_count = 10
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is True
    
    def test_seller_filter_no_rating_data(self, sample_watch, sample_listing):
        """Test seller filter when listing has no rating data - should fail."""
        # Remove rating data from listing
        sample_listing.seller_rating = None
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is False
    
    def test_seller_filter_no_feedback_data(self, sample_watch, sample_listing):
        """Test seller filter when listing has no feedback data - should fail."""
        # Remove feedback data from listing
        sample_listing.seller_feedback_count = None
        
        result = WatchScheduler._check_seller_filters(None, sample_watch, sample_listing)
        assert result is False
    
    def test_seller_filter_no_requirements(self, sample_listing):
        """Test seller filter when watch has no seller requirements - should pass."""
        # Create watch without seller requirements
        watch = Watch(
            id="test-watch",
            name="Test Watch",
            vinted_domain="vinted.fr",
            query="test item",
            max_price=50.0,
            currency="EUR",
            min_seller_rating=None,
            min_seller_feedback_count=None,
            active=True
        )
        
        result = WatchScheduler._check_seller_filters(None, watch, sample_listing)
        assert result is True
    
    def test_seller_filter_partial_requirements(self, sample_listing):
        """Test seller filter with only rating requirement."""
        # Create watch with only rating requirement
        watch = Watch(
            id="test-watch",
            name="Test Watch",
            vinted_domain="vinted.fr",
            query="test item",
            max_price=50.0,
            currency="EUR",
            min_seller_rating=4.0,
            min_seller_feedback_count=None,
            active=True
        )
        
        # Should pass rating check, ignore feedback count
        result = WatchScheduler._check_seller_filters(None, watch, sample_listing)
        assert result is True


class TestCurrencyConverter:
    """Test currency conversion functionality."""
    
    @pytest.mark.asyncio
    async def test_same_currency_conversion(self):
        """Test conversion between same currencies."""
        converter = CurrencyConverter()
        
        result = await converter.convert(100.0, "EUR", "EUR")
        assert result == 100.0
    
    @pytest.mark.asyncio
    async def test_fallback_rate_conversion(self):
        """Test conversion using fallback rates."""
        converter = CurrencyConverter()
        
        # Should use fallback rate EUR -> USD (approximately 1.10)
        result = await converter.convert(100.0, "EUR", "USD")
        assert result is not None
        assert result > 100.0  # USD should be higher value
    
    @pytest.mark.asyncio
    async def test_reverse_fallback_rate_conversion(self):
        """Test conversion using reverse fallback rates."""
        converter = CurrencyConverter()
        
        # Should use reverse fallback rate USD -> EUR (1 / 1.10)
        result = await converter.convert(110.0, "USD", "EUR")
        assert result is not None
        assert result < 110.0  # EUR should be lower value
    
    @pytest.mark.asyncio
    async def test_unsupported_currency_conversion(self):
        """Test conversion with unsupported currency."""
        converter = CurrencyConverter()
        
        result = await converter.convert(100.0, "XYZ", "EUR")
        assert result is None
    
    def test_supported_currencies(self):
        """Test getting supported currencies."""
        converter = CurrencyConverter()
        
        currencies = converter.get_supported_currencies()
        assert "EUR" in currencies
        assert "USD" in currencies
        assert "GBP" in currencies
        assert "PLN" in currencies
    
    def test_currency_support_check(self):
        """Test checking if currency is supported."""
        converter = CurrencyConverter()
        
        assert converter.is_currency_supported("EUR") is True
        assert converter.is_currency_supported("USD") is True
        assert converter.is_currency_supported("XYZ") is False


if __name__ == "__main__":
    pytest.main([__file__])
