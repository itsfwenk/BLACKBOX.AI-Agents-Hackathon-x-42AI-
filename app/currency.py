"""
Currency conversion utilities for price comparison across different currencies.
"""

import asyncio
import aiohttp
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

from .utils import logger


class CurrencyConverter:
    """Currency converter with caching and fallback support."""
    
    def __init__(self, 
                 api_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 cache_duration_hours: int = 24):
        """
        Initialize currency converter.
        
        Args:
            api_url: Currency API URL (e.g., ExchangeRate API)
            api_key: API key for currency service
            cache_duration_hours: How long to cache exchange rates
        """
        self.api_url = api_url
        self.api_key = api_key
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # In-memory cache for exchange rates
        self._rates_cache: Dict[str, Dict[str, Any]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Fallback rates (approximate, for when API is unavailable)
        self._fallback_rates = {
            'EUR': {
                'USD': 1.10,
                'GBP': 0.85,
                'PLN': 4.30,
                'CZK': 24.50,
                'JPY': 160.0
            },
            'USD': {
                'EUR': 0.91,
                'GBP': 0.77,
                'PLN': 3.90,
                'CZK': 22.30,
                'JPY': 145.0
            },
            'GBP': {
                'EUR': 1.18,
                'USD': 1.30,
                'PLN': 5.10,
                'CZK': 29.0,
                'JPY': 190.0
            }
        }
        
        logger.info(f"Currency converter initialized (API: {'enabled' if api_url else 'disabled'})")
    
    async def start(self) -> None:
        """Start the currency converter session."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("Currency converter session started")
    
    async def stop(self) -> None:
        """Stop the currency converter session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("Currency converter session stopped")
    
    async def convert(self, 
                      amount: float, 
                      from_currency: str, 
                      to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'USD')
        
        Returns:
            Converted amount or None if conversion fails
        """
        if from_currency == to_currency:
            return amount
        
        try:
            # Get exchange rate
            rate = await self._get_exchange_rate(from_currency, to_currency)
            
            if rate is not None:
                converted = amount * rate
                logger.debug(f"Converted {amount} {from_currency} to {converted:.2f} {to_currency} (rate: {rate})")
                return round(converted, 2)
            
            logger.warning(f"Could not get exchange rate for {from_currency} -> {to_currency}")
            return None
            
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return None
    
    async def _get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies."""
        # Check cache first
        cached_rate = self._get_cached_rate(from_currency, to_currency)
        if cached_rate is not None:
            return cached_rate
        
        # Try to fetch from API
        if self.api_url:
            api_rate = await self._fetch_rate_from_api(from_currency, to_currency)
            if api_rate is not None:
                self._cache_rate(from_currency, to_currency, api_rate)
                return api_rate
        
        # Fall back to hardcoded rates
        fallback_rate = self._get_fallback_rate(from_currency, to_currency)
        if fallback_rate is not None:
            logger.debug(f"Using fallback rate for {from_currency} -> {to_currency}: {fallback_rate}")
            return fallback_rate
        
        return None
    
    def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get cached exchange rate if still valid."""
        cache_key = f"{from_currency}_{to_currency}"
        
        if cache_key in self._rates_cache:
            cached_data = self._rates_cache[cache_key]
            cached_time = cached_data['timestamp']
            
            # Check if cache is still valid
            if datetime.utcnow() - cached_time < self.cache_duration:
                return cached_data['rate']
            else:
                # Remove expired cache entry
                del self._rates_cache[cache_key]
        
        return None
    
    def _cache_rate(self, from_currency: str, to_currency: str, rate: float) -> None:
        """Cache exchange rate."""
        cache_key = f"{from_currency}_{to_currency}"
        self._rates_cache[cache_key] = {
            'rate': rate,
            'timestamp': datetime.utcnow()
        }
    
    async def _fetch_rate_from_api(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Fetch exchange rate from API."""
        if not self._session:
            await self.start()
        
        try:
            # Build API URL (example for ExchangeRate API)
            if 'exchangerate-api.com' in self.api_url:
                url = f"{self.api_url}/{from_currency}"
            else:
                # Generic API format
                url = f"{self.api_url}?from={from_currency}&to={to_currency}"
            
            # Add API key if provided
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
            
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse response based on API format
                    rate = self._parse_api_response(data, from_currency, to_currency)
                    if rate is not None:
                        logger.debug(f"Fetched rate from API: {from_currency} -> {to_currency} = {rate}")
                        return rate
                else:
                    logger.warning(f"API request failed: {response.status}")
                    
        except asyncio.TimeoutError:
            logger.warning("Currency API timeout")
        except Exception as e:
            logger.warning(f"Currency API error: {e}")
        
        return None
    
    def _parse_api_response(self, data: Dict[str, Any], from_currency: str, to_currency: str) -> Optional[float]:
        """Parse API response to extract exchange rate."""
        try:
            # ExchangeRate API format
            if 'rates' in data and to_currency in data['rates']:
                return float(data['rates'][to_currency])
            
            # Alternative API formats
            if 'result' in data:
                return float(data['result'])
            
            if 'rate' in data:
                return float(data['rate'])
            
            # Direct rate value
            if isinstance(data, (int, float)):
                return float(data)
            
            logger.warning(f"Unknown API response format: {data}")
            return None
            
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing API response: {e}")
            return None
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get fallback exchange rate from hardcoded values."""
        if from_currency in self._fallback_rates:
            rates = self._fallback_rates[from_currency]
            if to_currency in rates:
                return rates[to_currency]
        
        # Try reverse conversion
        if to_currency in self._fallback_rates:
            rates = self._fallback_rates[to_currency]
            if from_currency in rates:
                return 1.0 / rates[from_currency]
        
        return None
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currencies."""
        currencies = set(['EUR', 'USD', 'GBP', 'PLN', 'CZK', 'JPY'])
        
        # Add currencies from fallback rates
        for base_currency, rates in self._fallback_rates.items():
            currencies.add(base_currency)
            currencies.update(rates.keys())
        
        return sorted(list(currencies))
    
    def is_currency_supported(self, currency: str) -> bool:
        """Check if currency is supported."""
        return currency in self.get_supported_currencies()
    
    async def update_fallback_rates(self) -> None:
        """Update fallback rates from API if available."""
        if not self.api_url:
            return
        
        logger.info("Updating fallback exchange rates...")
        
        base_currencies = ['EUR', 'USD', 'GBP']
        target_currencies = ['EUR', 'USD', 'GBP', 'PLN', 'CZK', 'JPY']
        
        updated_rates = {}
        
        for base in base_currencies:
            updated_rates[base] = {}
            
            for target in target_currencies:
                if base != target:
                    rate = await self._fetch_rate_from_api(base, target)
                    if rate is not None:
                        updated_rates[base][target] = rate
        
        # Update fallback rates if we got some data
        if updated_rates:
            self._fallback_rates.update(updated_rates)
            logger.info(f"Updated fallback rates for {len(updated_rates)} base currencies")
        else:
            logger.warning("Failed to update any fallback rates")
    
    def clear_cache(self) -> None:
        """Clear the exchange rate cache."""
        self._rates_cache.clear()
        logger.debug("Exchange rate cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow()
        valid_entries = 0
        expired_entries = 0
        
        for cache_data in self._rates_cache.values():
            if now - cache_data['timestamp'] < self.cache_duration:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._rates_cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600
        }


# Global currency converter instance
_currency_converter: Optional[CurrencyConverter] = None


def get_currency_converter(api_url: Optional[str] = None, 
                          api_key: Optional[str] = None) -> CurrencyConverter:
    """Get or create global currency converter instance."""
    global _currency_converter
    
    if _currency_converter is None:
        _currency_converter = CurrencyConverter(api_url, api_key)
    
    return _currency_converter


async def close_currency_converter() -> None:
    """Close global currency converter instance."""
    global _currency_converter
    
    if _currency_converter:
        await _currency_converter.stop()
        _currency_converter = None
