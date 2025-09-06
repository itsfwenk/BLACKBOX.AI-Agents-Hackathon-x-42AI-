#!/usr/bin/env python3
"""
Debug script to analyze Vinted search results for ETB aventures ensemble
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_etb_search():
    """Debug the ETB search specifically"""
    
    # Build the search URL for ETB aventures ensemble
    query = "ETB aventures ensemble"
    max_price = 150.0
    url = f"https://vinted.fr/catalog?search_text={query.replace(' ', '%20')}&price_to={max_price}"
    
    print(f"Testing ETB search URL: {url}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        try:
            print("Navigating to Vinted...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            print("Page loaded, analyzing structure...")
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(3000)
            
            # Check page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check if we're on the right page
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Check for search results container
            search_containers = [
                '.feed-grid',
                '.catalog-grid',
                '.search-results',
                '[data-testid="search-results"]',
                '.items-container'
            ]
            
            for container in search_containers:
                elements = await page.query_selector_all(container)
                if elements:
                    print(f"✅ Found search container: {container} ({len(elements)} elements)")
                else:
                    print(f"❌ No container found: {container}")
            
            # Test our updated selectors
            selectors_to_test = [
                'div[data-testid*="item-"]:not([data-testid*="--image"])',
                'div[data-testid*="product-item-id-"]',
                'div.new-item-box__container',
                'article',
                'a[href*="/items/"]'
            ]
            
            for selector in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ Found {len(elements)} elements with selector: {selector}")
                        
                        # Get sample HTML from first element
                        if elements:
                            html = await elements[0].inner_html()
                            print(f"Sample HTML (first 500 chars): {html[:500]}...")
                            print("-" * 50)
                    else:
                        print(f"❌ No elements found with selector: {selector}")
                except Exception as e:
                    print(f"❌ Error with selector {selector}: {e}")
            
            # Check for "no results" messages
            no_results_selectors = [
                '.no-results',
                '.empty-state',
                '[data-testid="no-results"]',
                '.search-no-results'
            ]
            
            for selector in no_results_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    text = await elements[0].inner_text()
                    print(f"⚠️ Found no-results message: {text}")
            
            # Check if page contains ETB text
            page_content = await page.content()
            if 'ETB' in page_content:
                print("✅ Page contains 'ETB' - search seems to work")
            else:
                print("❌ Page does not contain 'ETB' - search might not be working")
            
            # Take a screenshot for debugging
            await page.screenshot(path='debug_etb_search.png')
            print("📸 Screenshot saved as debug_etb_search.png")
            
        except Exception as e:
            print(f"❌ Error during page analysis: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_etb_search())
