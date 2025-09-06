"""
DOM parsing utilities for extracting data from Vinted pages.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from playwright.async_api import Page, ElementHandle

from ..models import Listing
from ..utils import logger, normalize_price, extract_listing_id_from_url


class VintedParser:
    """Parser for extracting listing data from Vinted pages."""
    
    # CSS selectors for current Vinted page structure (2024)
    LISTING_SELECTORS = [
        # Primary selectors based on current Vinted structure
        'div[data-testid*="item-"]:not([data-testid*="--image"])',  # e.g., data-testid="item-7012633230"
        'div[data-testid*="product-item-id-"]',  # e.g., data-testid="product-item-id-7024822502"
        'div.new-item-box__container',  # Current container class
        'article',  # Article elements containing items
        # Fallback selectors
        'a[href*="/items/"]',
        '[data-testid*="closet-item-"]',
        '.feed-grid__item',
        # Legacy selectors (kept for compatibility)
        '[data-testid="item-box"]',
        '.item-box',
        '[data-item-id]'
    ]
    
    TITLE_SELECTORS = [
        # Current Vinted title selectors
        'img[alt]',  # Title is often in img alt attribute
        'a[title]',  # Title in link title attribute
        'h3',
        'h2',
        'h4',
        '[data-testid*="title"]',
        '.web_ui__Text__text',  # Common text class in current Vinted
        # Legacy selectors
        '[data-testid="item-title"]',
        '.item-box__title',
        '.item__title',
        '.title'
    ]
    
    PRICE_SELECTORS = [
        # Current Vinted price selectors
        '.web_ui__Text__text',  # Price is often in this class
        '[data-testid*="price"]',
        'span[class*="price"]',
        'div[class*="price"]',
        '.price',
        # Legacy selectors
        '[data-testid="item-price"]',
        '.item-box__price',
        '.item__price'
    ]
    
    IMAGE_SELECTORS = [
        # Current Vinted image selectors
        '.web_ui__Image__content',  # Current image class
        'img[alt*="Solro"]',  # Based on debug output
        'img[src*="vinted"]',
        '[data-testid*="--image"] img',
        '.new-item-box__image img',
        # Legacy selectors
        '[data-testid="item-photo"] img',
        '.item-box__photo img',
        '.item__photo img',
        '.photo img'
    ]
    
    BRAND_SELECTORS = [
        '[data-testid="item-brand"]',
        '.item-box__brand',
        '.item__brand',
        '.brand'
    ]
    
    SIZE_SELECTORS = [
        '[data-testid="item-size"]',
        '.item-box__size',
        '.item__size',
        '.size'
    ]
    
    CONDITION_SELECTORS = [
        '[data-testid="item-status"]',
        '.item-box__status',
        '.item__status',
        '.status',
        '.condition'
    ]
    
    SELLER_SELECTORS = [
        '[data-testid="item-user"]',
        '.item-box__user',
        '.item__user',
        '.user',
        '.seller'
    ]
    
    def __init__(self, domain: str):
        """
        Initialize parser for specific domain.
        
        Args:
            domain: Vinted domain (e.g., 'vinted.fr')
        """
        self.domain = domain
        self.base_url = f"https://{domain}"
        
        # Domain-specific configurations
        self.currency_map = {
            'vinted.fr': 'EUR',
            'vinted.de': 'EUR',
            'vinted.it': 'EUR',
            'vinted.es': 'EUR',
            'vinted.com': 'USD',
            'vinted.pl': 'PLN',
            'vinted.lt': 'EUR',
            'vinted.cz': 'CZK'
        }
        
        self.default_currency = self.currency_map.get(domain, 'EUR')
        logger.debug(f"Parser initialized for {domain} (default currency: {self.default_currency})")
    
    async def extract_listings(self, page: Page) -> List[Listing]:
        """
        Extract all listings from the current page.
        
        Args:
            page: Playwright page
        
        Returns:
            List of Listing objects
        """
        listings = []
        
        try:
            # Find listing containers
            listing_elements = await self._find_listing_elements(page)
            
            if not listing_elements:
                logger.warning("No listing elements found on page")
                return listings
            
            logger.debug(f"Found {len(listing_elements)} listing elements")
            
            # Extract data from each listing
            for i, element in enumerate(listing_elements):
                try:
                    listing = await self._extract_listing_data(element, page)
                    if listing:
                        listings.append(listing)
                        logger.debug(f"Extracted listing {i + 1}: {listing.title[:50]}...")
                    else:
                        logger.debug(f"Failed to extract listing {i + 1}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting listing {i + 1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(listings)} listings from page")
            
        except Exception as e:
            logger.error(f"Error extracting listings: {e}")
        
        return listings
    
    async def _find_listing_elements(self, page: Page) -> List[ElementHandle]:
        """Find listing elements on the page."""
        for selector in self.LISTING_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return []
    
    async def _extract_listing_data(self, element: ElementHandle, page: Page) -> Optional[Listing]:
        """Extract data from a single listing element."""
        try:
            # Extract URL and listing ID
            url = await self._extract_url(element)
            if not url:
                return None
            
            listing_id = extract_listing_id_from_url(url)
            if not listing_id:
                # Try to extract from data attributes
                listing_id = await self._extract_listing_id_from_element(element)
                if not listing_id:
                    logger.debug(f"Could not extract listing ID from URL: {url}")
                    return None
            
            # Extract title
            title = await self._extract_text_by_selectors(element, self.TITLE_SELECTORS)
            if not title:
                logger.debug(f"Could not extract title for listing {listing_id}")
                return None
            
            # Extract price
            price_amount, price_currency = await self._extract_price(element)
            if price_amount is None:
                logger.debug(f"Could not extract price for listing {listing_id}")
                return None
            
            # Extract optional fields
            thumbnail_url = await self._extract_image_url(element)
            brand = await self._extract_text_by_selectors(element, self.BRAND_SELECTORS)
            size = await self._extract_text_by_selectors(element, self.SIZE_SELECTORS)
            condition = await self._extract_text_by_selectors(element, self.CONDITION_SELECTORS)
            
            # Extract seller info (if available on listing card)
            seller_rating, seller_feedback_count = await self._extract_seller_info(element)
            
            # Create listing object
            listing = Listing(
                listing_id=listing_id,
                title=title.strip(),
                price_amount=price_amount,
                price_currency=price_currency or self.default_currency,
                url=url,
                thumbnail_url=thumbnail_url,
                brand=brand.strip() if brand else None,
                size=size.strip() if size else None,
                condition=condition.strip() if condition else None,
                posted_time=None,  # Usually not available on listing cards
                seller_rating=seller_rating,
                seller_feedback_count=seller_feedback_count,
                domain=self.domain
            )
            
            return listing
            
        except Exception as e:
            logger.warning(f"Error extracting listing data: {e}")
            return None
    
    async def _extract_url(self, element: ElementHandle) -> Optional[str]:
        """Extract listing URL from element."""
        try:
            # Try to find link element - prioritize item links
            link_selectors = [
                'a[href*="/items/"]',  # Direct item links
                'a[href*="/item/"]',   # Alternative item links
                'a'                    # Any link as fallback
            ]
            
            for selector in link_selectors:
                links = await element.query_selector_all(selector)
                for link in links:
                    href = await link.get_attribute('href')
                    if href and ('/items/' in href or '/item/' in href):
                        # Make absolute URL
                        if href.startswith('/'):
                            return f"{self.base_url}{href}"
                        elif href.startswith('http'):
                            return href
            
            # Try to get href from the element itself
            href = await element.get_attribute('href')
            if href and ('/items/' in href or '/item/' in href):
                if href.startswith('/'):
                    return f"{self.base_url}{href}"
                elif href.startswith('http'):
                    return href
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting URL: {e}")
            return None
    
    async def _extract_listing_id_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract listing ID from element attributes."""
        try:
            # Try common data attributes
            attributes = ['data-item-id', 'data-id', 'id', 'data-testid']
            
            for attr in attributes:
                value = await element.get_attribute(attr)
                if value and value.isdigit():
                    return value
                elif value and 'item' in value.lower():
                    # Extract digits from attribute value
                    match = re.search(r'(\d+)', value)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting listing ID from element: {e}")
            return None
    
    async def _extract_text_by_selectors(self, element: ElementHandle, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors as fallbacks."""
        for selector in selectors:
            try:
                target = await element.query_selector(selector)
                if target:
                    text = await target.inner_text()
                    if text and text.strip():
                        return text.strip()
                    
                    # Try title attribute as fallback
                    title = await target.get_attribute('title')
                    if title and title.strip():
                        return title.strip()
                        
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return None
    
    async def _extract_price(self, element: ElementHandle) -> Tuple[Optional[float], Optional[str]]:
        """Extract price amount and currency from element."""
        for selector in self.PRICE_SELECTORS:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    if price_text:
                        amount, currency = normalize_price(price_text)
                        if amount is not None:
                            return amount, currency
                        
            except Exception as e:
                logger.debug(f"Price selector {selector} failed: {e}")
                continue
        
        return None, None
    
    async def _extract_image_url(self, element: ElementHandle) -> Optional[str]:
        """Extract thumbnail image URL from element."""
        for selector in self.IMAGE_SELECTORS:
            try:
                img = await element.query_selector(selector)
                if img:
                    src = await img.get_attribute('src')
                    if src:
                        # Make absolute URL
                        if src.startswith('//'):
                            return f"https:{src}"
                        elif src.startswith('/'):
                            return f"{self.base_url}{src}"
                        elif src.startswith('http'):
                            return src
                    
                    # Try data-src for lazy loaded images
                    data_src = await img.get_attribute('data-src')
                    if data_src:
                        if data_src.startswith('//'):
                            return f"https:{data_src}"
                        elif data_src.startswith('/'):
                            return f"{self.base_url}{data_src}"
                        elif data_src.startswith('http'):
                            return data_src
                            
            except Exception as e:
                logger.debug(f"Image selector {selector} failed: {e}")
                continue
        
        return None
    
    async def _extract_seller_info(self, element: ElementHandle) -> Tuple[Optional[float], Optional[int]]:
        """Extract seller rating and feedback count if available on listing card."""
        try:
            # Look for seller section
            for selector in self.SELLER_SELECTORS:
                seller_element = await element.query_selector(selector)
                if seller_element:
                    seller_text = await seller_element.inner_text()
                    if seller_text:
                        # Try to extract rating (e.g., "4.8★" or "4.8/5")
                        rating_match = re.search(r'(\d+\.?\d*)\s*[★⭐/]', seller_text)
                        rating = float(rating_match.group(1)) if rating_match else None
                        
                        # Try to extract feedback count (e.g., "(123)" or "123 reviews")
                        feedback_match = re.search(r'\(?(\d+)\)?(?:\s*(?:reviews?|feedback|évaluations?))?', seller_text)
                        feedback_count = int(feedback_match.group(1)) if feedback_match else None
                        
                        if rating is not None or feedback_count is not None:
                            return rating, feedback_count
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Error extracting seller info: {e}")
            return None, None
    
    async def has_next_page(self, page: Page) -> bool:
        """Check if there's a next page available."""
        next_selectors = [
            'a[data-testid="pagination-next"]',
            '.pagination__next:not(.pagination__next--disabled)',
            'a[aria-label*="Next"]',
            'a[title*="Next"]',
            '.next-page:not(.disabled)',
            'a.pagination-next:not(.disabled)'
        ]
        
        for selector in next_selectors:
            try:
                next_button = await page.query_selector(selector)
                if next_button:
                    # Check if button is enabled
                    is_disabled = await next_button.get_attribute('disabled')
                    class_name = await next_button.get_attribute('class')
                    
                    if not is_disabled and (not class_name or 'disabled' not in class_name.lower()):
                        return True
                        
            except Exception as e:
                logger.debug(f"Next page selector {selector} failed: {e}")
                continue
        
        return False
    
    async def click_next_page(self, page: Page) -> bool:
        """Click the next page button."""
        next_selectors = [
            'a[data-testid="pagination-next"]',
            '.pagination__next:not(.pagination__next--disabled)',
            'a[aria-label*="Next"]',
            'a[title*="Next"]',
            '.next-page:not(.disabled)',
            'a.pagination-next:not(.disabled)'
        ]
        
        for selector in next_selectors:
            try:
                next_button = await page.query_selector(selector)
                if next_button:
                    # Check if button is enabled
                    is_disabled = await next_button.get_attribute('disabled')
                    class_name = await next_button.get_attribute('class')
                    
                    if not is_disabled and (not class_name or 'disabled' not in class_name.lower()):
                        await next_button.click()
                        
                        # Wait for navigation
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        return True
                        
            except Exception as e:
                logger.debug(f"Error clicking next page with selector {selector}: {e}")
                continue
        
        return False
    
    def get_domain_currency(self) -> str:
        """Get default currency for the domain."""
        return self.default_currency
    
    def is_valid_listing_url(self, url: str) -> bool:
        """Check if URL is a valid Vinted listing URL."""
        if not url:
            return False
        
        return (
            self.domain in url and
            ('/items/' in url or '/item/' in url) and
            re.search(r'/items?/\d+', url) is not None
        )
