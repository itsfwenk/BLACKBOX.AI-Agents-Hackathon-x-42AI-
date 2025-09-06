#!/usr/bin/env python3
"""
Debug script to inspect Vinted's current HTML structure and test selectors.
"""

import asyncio
from playwright.async_api import async_playwright
from app.utils import create_search_url

async def debug_vinted_structure():
    """Debug Vinted page structure to find correct selectors."""
    
    # Generate search URL
    url = create_search_url('vinted.fr', 'ETB', {'max_price': 150.0})
    print(f"Testing URL: {url}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)  # Headless for server environment
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        try:
            print("Navigating to Vinted...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(3000)
            
            print("Page loaded, analyzing structure...")
            
            # Try to find any item containers
            possible_selectors = [
                'article',
                '[data-testid*="item"]',
                '[class*="item"]',
                '[class*="card"]',
                '[class*="product"]',
                '.c-item-box',
                '.item-card',
                '.listing',
                'div[data-item-id]',
                'a[href*="/items/"]'
            ]
            
            for selector in possible_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ Found {len(elements)} elements with selector: {selector}")
                        
                        # Get HTML of first element for analysis
                        if elements:
                            html = await elements[0].inner_html()
                            print(f"Sample HTML (first 500 chars): {html[:500]}...")
                            print("-" * 50)
                    else:
                        print(f"❌ No elements found with selector: {selector}")
                except Exception as e:
                    print(f"❌ Error with selector {selector}: {e}")
            
            # Try to get page title and check if we're on the right page
            title = await page.title()
            print(f"Page title: {title}")
            
            # Get page content to see if there are any listings
            content = await page.content()
            if 'ETB' in content:
                print("✅ Page contains 'ETB' - search seems to work")
            else:
                print("❌ Page doesn't contain 'ETB' - search might not work")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_vinted_structure())
