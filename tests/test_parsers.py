"""
Tests for DOM parsing utilities.
"""

import pytest
from datetime import datetime
from app.utils import normalize_price, extract_listing_id_from_url, create_search_url


class TestPriceNormalization:
    """Test price normalization functions."""
    
    def test_normalize_price_euro(self):
        """Test Euro price normalization."""
        amount, currency = normalize_price("€25.50")
        assert amount == 25.50
        assert currency == "EUR"
    
    def test_normalize_price_dollar(self):
        """Test Dollar price normalization."""
        amount, currency = normalize_price("$30.00")
        assert amount == 30.00
        assert currency == "USD"
    
    def test_normalize_price_with_comma(self):
        """Test price with comma as decimal separator."""
        amount, currency = normalize_price("25,50 €")
        assert amount == 25.50
        assert currency == "EUR"
    
    def test_normalize_price_pound(self):
        """Test Pound price normalization."""
        amount, currency = normalize_price("£15.99")
        assert amount == 15.99
        assert currency == "GBP"
    
    def test_normalize_price_invalid(self):
        """Test invalid price text."""
        amount, currency = normalize_price("invalid")
        assert amount is None
        assert currency is None
    
    def test_normalize_price_empty(self):
        """Test empty price text."""
        amount, currency = normalize_price("")
        assert amount is None
        assert currency is None
    
    def test_normalize_price_with_spaces(self):
        """Test price with extra spaces."""
        amount, currency = normalize_price("  €  25.50  ")
        assert amount == 25.50
        assert currency == "EUR"


class TestListingIdExtraction:
    """Test listing ID extraction from URLs."""
    
    def test_extract_listing_id_standard(self):
        """Test standard Vinted URL format."""
        url = "https://vinted.fr/items/123456789-nike-air-force"
        listing_id = extract_listing_id_from_url(url)
        assert listing_id == "123456789"
    
    def test_extract_listing_id_simple(self):
        """Test simple item URL."""
        url = "https://vinted.com/items/987654321"
        listing_id = extract_listing_id_from_url(url)
        assert listing_id == "987654321"
    
    def test_extract_listing_id_with_params(self):
        """Test URL with query parameters."""
        url = "https://vinted.de/items/555666777-jacket?param=value"
        listing_id = extract_listing_id_from_url(url)
        assert listing_id == "555666777"
    
    def test_extract_listing_id_invalid(self):
        """Test invalid URL."""
        url = "https://vinted.fr/catalog"
        listing_id = extract_listing_id_from_url(url)
        assert listing_id is None
    
    def test_extract_listing_id_empty(self):
        """Test empty URL."""
        listing_id = extract_listing_id_from_url("")
        assert listing_id is None


class TestSearchUrlCreation:
    """Test search URL creation."""
    
    def test_create_basic_search_url(self):
        """Test basic search URL creation."""
        url = create_search_url("vinted.fr", "nike shoes", {})
        assert "vinted.fr/catalog" in url
        assert "search_text=nike" in url and "shoes" in url
    
    def test_create_search_url_with_filters(self):
        """Test search URL with filters."""
        filters = {
            "max_price": 50.0,
            "price_from": 10.0,
            "order": "newest_first"
        }
        url = create_search_url("vinted.fr", "jacket", filters)
        
        assert "search_text=jacket" in url
        assert "price_to=50.0" in url
        assert "price_from=10.0" in url
        assert "order=newest_first" in url
    
    def test_create_search_url_with_category(self):
        """Test search URL with category filter."""
        filters = {
            "category_ids": [1234, 5678]
        }
        url = create_search_url("vinted.com", "dress", filters)
        
        assert "catalog_ids=1234%2C5678" in url
    
    def test_create_search_url_with_brand(self):
        """Test search URL with brand filter."""
        filters = {
            "brand_ids": [999]
        }
        url = create_search_url("vinted.de", "shirt", filters)
        
        assert "brand_ids=999" in url
    
    def test_create_search_url_with_size(self):
        """Test search URL with size filter."""
        filters = {
            "size_ids": [42, 43]
        }
        url = create_search_url("vinted.it", "shoes", filters)
        
        assert "size_ids=42%2C43" in url
    
    def test_create_search_url_with_condition(self):
        """Test search URL with condition filter."""
        filters = {
            "condition_ids": [1, 2, 3]
        }
        url = create_search_url("vinted.es", "bag", filters)
        
        assert "status_ids=1%2C2%2C3" in url


if __name__ == "__main__":
    pytest.main([__file__])
