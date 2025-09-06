#!/usr/bin/env python3
"""
Check if Vinted has banned your IP or if there are network connectivity issues
"""

import asyncio
import sys
from pathlib import Path
import aiohttp
import time

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.scraper import BrowserManager

async def check_vinted_access():
    print("🔍 CHECKING VINTED ACCESS & BAN STATUS")
    print("=" * 50)
    
    # Test 1: Basic HTTP connectivity
    print("\n1️⃣ TESTING BASIC HTTP ACCESS")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test main Vinted page
            async with session.get('https://vinted.fr', timeout=10) as response:
                print(f"✅ HTTP Status: {response.status}")
                if response.status == 200:
                    print("✅ Basic HTTP access works")
                elif response.status == 403:
                    print("❌ HTTP 403 Forbidden - Likely IP banned!")
                elif response.status == 429:
                    print("❌ HTTP 429 Too Many Requests - Rate limited!")
                else:
                    print(f"⚠️  Unusual status code: {response.status}")
                    
                # Check response headers for ban indicators
                headers = dict(response.headers)
                if 'cf-ray' in headers:
                    print("✅ Cloudflare protection detected (normal)")
                if 'server' in headers and 'cloudflare' in headers['server'].lower():
                    print("✅ Behind Cloudflare (normal)")
                    
    except asyncio.TimeoutError:
        print("❌ Connection timeout - Network issue or blocking")
    except Exception as e:
        print(f"❌ HTTP Error: {e}")
    
    # Test 2: Browser-based access (what the scraper uses)
    print("\n2️⃣ TESTING BROWSER ACCESS (SCRAPER METHOD)")
    print("-" * 30)
    
    try:
        browser_manager = BrowserManager(headless=True, concurrency=1)
        await browser_manager.start()
        print("✅ Browser started successfully")
        
        # Get a browser page
        page = await browser_manager.get_page()
        print("✅ Browser page acquired")
        
        # Try to navigate to Vinted
        start_time = time.time()
        try:
            response = await page.goto('https://vinted.fr', wait_until='networkidle', timeout=15000)
            duration = time.time() - start_time
            
            print(f"✅ Navigation successful in {duration:.1f}s")
            print(f"✅ Final URL: {page.url}")
            print(f"✅ Status: {response.status}")
            
            # Check if we're on the actual Vinted page or a block page
            title = await page.title()
            print(f"✅ Page title: {title}")
            
            if 'vinted' in title.lower():
                print("✅ Successfully reached Vinted homepage")
            elif 'blocked' in title.lower() or 'access denied' in title.lower():
                print("❌ BLOCKED! You may be banned")
            else:
                print(f"⚠️  Unexpected page: {title}")
            
            # Try to access a search page (what the scraper actually does)
            print("\n🔍 Testing search page access...")
            search_url = 'https://vinted.fr/catalog?search_text=test'
            try:
                search_response = await page.goto(search_url, wait_until='networkidle', timeout=15000)
                search_duration = time.time() - start_time
                
                print(f"✅ Search page accessible in {search_duration:.1f}s")
                print(f"✅ Search status: {search_response.status}")
                
                # Check for CAPTCHA or block indicators
                page_content = await page.content()
                if 'captcha' in page_content.lower():
                    print("❌ CAPTCHA detected - You're being challenged!")
                elif 'blocked' in page_content.lower():
                    print("❌ Block page detected - You may be banned!")
                elif 'items' in page_content.lower() or 'article' in page_content.lower():
                    print("✅ Search results page loaded successfully")
                else:
                    print("⚠️  Unusual page content")
                    
            except Exception as e:
                print(f"❌ Search page failed: {e}")
        
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            if 'ERR_NETWORK_CHANGED' in str(e):
                print("💡 ERR_NETWORK_CHANGED suggests network instability")
            elif 'timeout' in str(e).lower():
                print("💡 Timeout suggests slow connection or blocking")
        
        await browser_manager.stop()
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
    
    # Test 3: Check different user agents
    print("\n3️⃣ TESTING DIFFERENT USER AGENTS")
    print("-" * 30)
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    for i, ua in enumerate(user_agents, 1):
        try:
            async with aiohttp.ClientSession(headers={'User-Agent': ua}) as session:
                async with session.get('https://vinted.fr', timeout=5) as response:
                    print(f"✅ User-Agent {i}: Status {response.status}")
        except Exception as e:
            print(f"❌ User-Agent {i}: {e}")
    
    # Recommendations
    print("\n4️⃣ RECOMMENDATIONS")
    print("-" * 30)
    
    print("\n🛠️  SOLUTIONS TO TRY:")
    print("1. **Wait and Retry**: If rate-limited, wait 1-2 hours")
    print("2. **Change IP**: Restart router/modem or use VPN")
    print("3. **Increase Delays**: Edit .env file:")
    print("   MIN_DELAY_MS=2000")
    print("   MAX_DELAY_MS=5000")
    print("4. **Reduce Frequency**: Edit watches.yaml:")
    print("   polling_interval_sec: 60  # Instead of 30")
    print("5. **Use Docker**: Often has better network handling")
    
    print("\n🚨 IF YOU'RE BANNED:")
    print("- Wait 24-48 hours before trying again")
    print("- Use a VPN to change your IP address")
    print("- Reduce scraping frequency when you resume")
    print("- Consider using Docker with different network settings")

if __name__ == '__main__':
    asyncio.run(check_vinted_access())
