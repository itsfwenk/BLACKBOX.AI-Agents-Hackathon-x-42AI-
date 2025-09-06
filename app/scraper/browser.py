"""
Browser management for Playwright-based scraping.
Handles browser lifecycle, stealth mode, and anti-detection measures.
"""

import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from contextlib import asynccontextmanager

from ..utils import logger, RateLimiter, ExponentialBackoff


class BrowserManager:
    """Manages Playwright browser instances with anti-detection measures."""
    
    def __init__(self, 
                 headless: bool = True,
                 user_agent: str = None,
                 concurrency: int = 2):
        """
        Initialize browser manager.
        
        Args:
            headless: Run browser in headless mode
            user_agent: Custom user agent string
            concurrency: Maximum concurrent browser contexts
        """
        self.headless = headless
        self.user_agent = user_agent or self._get_default_user_agent()
        self.concurrency = concurrency
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: List[BrowserContext] = []
        self._rate_limiter = RateLimiter(max_requests=concurrency, time_window=1.0)
        self._lock = asyncio.Lock()
        
        logger.info(f"Browser manager initialized (headless={headless}, concurrency={concurrency})")
    
    def _get_default_user_agent(self) -> str:
        """Get default user agent string."""
        return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    async def start(self) -> None:
        """Start the browser."""
        async with self._lock:
            if self._browser:
                logger.warning("Browser already started")
                return
            
            try:
                self._playwright = await async_playwright().start()
                
                # Launch browser with stealth settings
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-default-apps',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        '--window-size=1920,1080'
                    ]
                )
                
                logger.info("Browser started successfully")
                
            except Exception as e:
                logger.error(f"Failed to start browser: {e}")
                await self._cleanup()
                raise
    
    async def stop(self) -> None:
        """Stop the browser and cleanup resources."""
        async with self._lock:
            await self._cleanup()
            logger.info("Browser stopped")
    
    async def _cleanup(self) -> None:
        """Internal cleanup method."""
        # Close all contexts
        for context in self._contexts:
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        self._contexts.clear()
        
        # Close browser
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self._browser = None
        
        # Stop playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
            self._playwright = None
    
    @asynccontextmanager
    async def get_page(self, domain: str = None):
        """
        Get a browser page with anti-detection measures.
        
        Args:
            domain: Domain for domain-specific settings
        
        Yields:
            Page: Playwright page instance
        """
        await self._rate_limiter.acquire()
        
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        context = None
        page = None
        
        try:
            # Create new context with stealth settings
            context = await self._browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                permissions=[],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Denoted.denied }) :
                        originalQuery(parameters)
                );
                
                // Hide automation indicators
                window.chrome = {
                    runtime: {},
                };
                
                // Mock screen properties
                Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
                Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
            """)
            
            self._contexts.append(context)
            
            # Create page
            page = await context.new_page()
            
            # Set additional page properties
            await page.set_extra_http_headers({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })
            
            # Enable request interception for additional stealth
            await page.route('**/*', self._handle_request)
            
            logger.debug(f"Created new page for domain: {domain}")
            
            yield page
            
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            raise
        
        finally:
            # Cleanup
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
            
            if context:
                try:
                    await context.close()
                    if context in self._contexts:
                        self._contexts.remove(context)
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
    
    async def _handle_request(self, route, request):
        """Handle requests for additional stealth measures."""
        # Block unnecessary resources to speed up loading
        resource_type = request.resource_type
        
        if resource_type in ['image', 'media', 'font', 'stylesheet']:
            # Block images and media for faster loading (can be configured)
            await route.abort()
            return
        
        # Add realistic headers
        headers = dict(request.headers)
        headers.update({
            'sec-fetch-dest': 'document' if resource_type == 'document' else 'empty',
            'sec-fetch-mode': 'navigate' if resource_type == 'document' else 'cors',
            'sec-fetch-site': 'same-origin'
        })
        
        await route.continue_(headers=headers)
    
    async def navigate_with_retry(self, 
                                  page: Page, 
                                  url: str, 
                                  max_retries: int = 3,
                                  wait_for_selector: str = None,
                                  timeout: int = 30000) -> bool:
        """
        Navigate to URL with retry logic and exponential backoff.
        
        Args:
            page: Playwright page
            url: URL to navigate to
            max_retries: Maximum retry attempts
            wait_for_selector: CSS selector to wait for after navigation
            timeout: Navigation timeout in milliseconds
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        backoff = ExponentialBackoff(initial_delay=1.0, max_delay=10.0)
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Navigating to {url} (attempt {attempt + 1})")
                
                # Navigate to page
                response = await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=timeout
                )
                
                if not response or response.status >= 400:
                    raise Exception(f"HTTP {response.status if response else 'No response'}")
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=10000)
                
                logger.debug(f"Successfully navigated to {url}")
                return True
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < max_retries:
                    await backoff.wait()
                else:
                    logger.error(f"All navigation attempts failed for {url}")
                    return False
        
        return False
    
    async def wait_for_listings(self, page: Page, timeout: int = 15000) -> bool:
        """
        Wait for listings to load on the page.
        
        Args:
            page: Playwright page
            timeout: Timeout in milliseconds
        
        Returns:
            bool: True if listings found, False otherwise
        """
        # Common selectors for Vinted listings
        selectors = [
            '[data-testid="item-box"]',
            '.feed-grid__item',
            '.item-box',
            '[data-item-id]',
            '.catalog-item',
            '.item'
        ]
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=timeout)
                logger.debug(f"Found listings with selector: {selector}")
                return True
            except Exception:
                continue
        
        logger.warning("No listings found with any known selector")
        return False
    
    async def scroll_page(self, page: Page, max_scrolls: int = 3) -> None:
        """
        Scroll page to load more content.
        
        Args:
            page: Playwright page
            max_scrolls: Maximum number of scrolls
        """
        for i in range(max_scrolls):
            try:
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait a bit for content to load
                await asyncio.sleep(1)
                
                # Check if we can scroll more
                can_scroll = await page.evaluate("""
                    window.innerHeight + window.scrollY >= document.body.scrollHeight - 100
                """)
                
                if can_scroll:
                    break
                    
            except Exception as e:
                logger.warning(f"Error during scroll {i + 1}: {e}")
                break
    
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._browser is not None and self._browser.is_connected()
    
    async def get_page_count(self) -> int:
        """Get current number of open pages across all contexts."""
        count = 0
        for context in self._contexts:
            try:
                count += len(context.pages)
            except Exception:
                pass
        return count
