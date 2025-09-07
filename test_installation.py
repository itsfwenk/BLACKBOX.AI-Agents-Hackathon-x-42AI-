#!/usr/bin/env python3
"""
Quick installation test for Vinted Monitor
"""

import sys
import os
import asyncio
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing Python imports...")
    
    required_modules = [
        'playwright',
        'aiosqlite', 
        'pydantic',
        'yaml',
        'aiohttp',
        'click',
        'dotenv',
        'openai',
        'anthropic',
        'google.generativeai',
        'gspread',
        'google.auth'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module} - {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All imports successful!")
    return True

def test_app_structure():
    """Test if app structure is correct"""
    print("\n🏗️  Testing app structure...")
    
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/cli.py',
        'app/config.py',
        'app/models.py',
        'app/store.py',
        'app/scheduler.py',
        'app/ai_analyzer.py',
        'app/sheets_integration.py',
        'app/scraper/__init__.py',
        'app/scraper/browser.py',
        'app/scraper/vinted_scraper.py',
        'app/notifier/__init__.py',
        'app/notifier/discord.py',
        'requirements.txt',
        '.env.example',
        'config/watches.yaml.example'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ App structure correct!")
    return True

def test_configuration():
    """Test configuration files"""
    print("\n⚙️  Testing configuration...")
    
    config_ok = True
    
    # Check .env file
    if Path('.env').exists():
        print("   ✅ .env file exists")
        
        with open('.env', 'r') as f:
            env_content = f.read()
            
        if 'DISCORD_WEBHOOK_URL=' in env_content:
            if 'https://discord.com/api/webhooks/' in env_content:
                print("   ✅ Discord webhook configured")
            else:
                print("   ⚠️  Discord webhook not properly configured")
                config_ok = False
        else:
            print("   ❌ Discord webhook not found in .env")
            config_ok = False
            
        if any(key in env_content for key in ['OPENAI_API_KEY=', 'ANTHROPIC_API_KEY=', 'GEMINI_API_KEY=']):
            print("   ✅ AI API key found")
        else:
            print("   ⚠️  No AI API key found (AI features will be disabled)")
    else:
        print("   ❌ .env file not found")
        print("   Run: cp .env.example .env")
        config_ok = False
    
    # Check watches.yaml
    if Path('config/watches.yaml').exists():
        print("   ✅ watches.yaml exists")
        try:
            import yaml
            with open('config/watches.yaml', 'r') as f:
                watches_data = yaml.safe_load(f)
            
            if 'watches' in watches_data and len(watches_data['watches']) > 0:
                print(f"   ✅ {len(watches_data['watches'])} watches configured")
            else:
                print("   ⚠️  No watches configured")
                config_ok = False
        except Exception as e:
            print(f"   ❌ Error reading watches.yaml: {e}")
            config_ok = False
    else:
        print("   ❌ watches.yaml not found")
        print("   Run: cp config/watches.yaml.example config/watches.yaml")
        config_ok = False
    
    return config_ok

async def test_app_startup():
    """Test if the app can start"""
    print("\n🚀 Testing app startup...")
    
    try:
        # Try to import the main CLI
        from app.cli import cli
        print("   ✅ CLI import successful")
        
        # Try to import core components
        from app.config import ConfigManager
        from app.models import Watch
        from app.store import get_db_store
        print("   ✅ Core components import successful")
        
        # Test AI components
        try:
            from app.ai_analyzer import create_ai_analyzer
            print("   ✅ AI analyzer import successful")
        except Exception as e:
            print(f"   ⚠️  AI analyzer import failed: {e}")
        
        # Test Sheets components
        try:
            from app.sheets_integration import create_sheets_manager
            print("   ✅ Sheets integration import successful")
        except Exception as e:
            print(f"   ⚠️  Sheets integration import failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ App startup test failed: {e}")
        return False

def test_playwright():
    """Test Playwright installation"""
    print("\n🎭 Testing Playwright...")
    
    try:
        from playwright.async_api import async_playwright
        print("   ✅ Playwright import successful")
        
        # Check if chromium is installed
        import subprocess
        result = subprocess.run(['playwright', 'install', '--dry-run', 'chromium'], 
                              capture_output=True, text=True)
        
        if 'chromium' in result.stdout.lower():
            print("   ✅ Chromium browser available")
        else:
            print("   ⚠️  Chromium might not be installed")
            print("   Run: playwright install chromium")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Playwright test failed: {e}")
        print("   Run: pip install playwright && playwright install chromium")
        return False

def main():
    """Run all tests"""
    print("🔍 VINTED MONITOR - INSTALLATION TEST")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_structure,
        test_configuration,
        test_playwright
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result if result is not None else False)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Test async components
    try:
        result = asyncio.run(test_app_startup())
        results.append(result if result is not None else False)
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ Your Vinted Monitor installation is ready!")
        print("🚀 Run: ./start_monitor.sh")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("\n❌ Please fix the issues above before running the monitor.")
        
        if not Path('.env').exists():
            print("\n🔧 Quick fix:")
            print("   cp .env.example .env")
            print("   # Edit .env with your Discord webhook and API keys")
        
        if not Path('config/watches.yaml').exists():
            print("   cp config/watches.yaml.example config/watches.yaml")
            print("   # Edit watches.yaml with your searches")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
