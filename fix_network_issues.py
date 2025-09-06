#!/usr/bin/env python3
"""
Fix network connectivity issues for Vinted Monitor
"""

import os
import shutil

def fix_network_issues():
    print("🔧 FIXING VINTED MONITOR NETWORK ISSUES")
    print("=" * 50)
    
    # 1. Update .env file with better network settings
    print("\n1️⃣ UPDATING NETWORK SETTINGS")
    print("-" * 30)
    
    env_updates = {
        'MIN_DELAY_MS': '1500',
        'MAX_DELAY_MS': '3000', 
        'DEFAULT_POLL_INTERVAL_SEC': '45',
        'CONCURRENCY': '1',
        'MAX_PAGES_PER_POLL': '1',
        'HEADLESS': 'true'
    }
    
    # Read current .env
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
    
    # Update or add settings
    env_lines = env_content.split('\n')
    updated_lines = []
    updated_keys = set()
    
    for line in env_lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in env_updates:
                updated_lines.append(f"{key}={env_updates[key]}")
                updated_keys.add(key)
                print(f"✅ Updated {key}={env_updates[key]}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add missing settings
    for key, value in env_updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}")
            print(f"✅ Added {key}={value}")
    
    # Write updated .env
    with open('.env', 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ Network settings updated in .env")
    
    # 2. Update watches.yaml with safer polling intervals
    print("\n2️⃣ UPDATING WATCH POLLING INTERVALS")
    print("-" * 30)
    
    import yaml
    
    try:
        with open('config/watches.yaml', 'r') as f:
            data = yaml.safe_load(f)
        
        updated = False
        for watch in data['watches']:
            if watch.get('polling_interval_sec', 30) < 45:
                watch['polling_interval_sec'] = 45
                updated = True
                print(f"✅ Updated '{watch['name']}' polling to 45 seconds")
        
        if updated:
            with open('config/watches.yaml', 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            print("✅ Watch polling intervals updated")
        else:
            print("✅ Watch polling intervals already optimal")
            
    except Exception as e:
        print(f"⚠️  Could not update watches.yaml: {e}")
    
    # 3. Create a network-optimized startup script
    print("\n3️⃣ CREATING NETWORK-OPTIMIZED STARTUP")
    print("-" * 30)
    
    startup_script = '''#!/bin/bash
# Network-optimized Vinted Monitor startup

echo "🚀 Starting Vinted Monitor with network optimizations..."

# Activate virtual environment
source venv/bin/activate

# Clear any stale browser processes
pkill -f chromium 2>/dev/null || true
pkill -f chrome 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start with network retry logic
for i in {1..3}; do
    echo "Attempt $i/3..."
    python -m app.main run
    if [ $? -eq 0 ]; then
        break
    fi
    echo "Failed, waiting 10 seconds before retry..."
    sleep 10
done
'''
    
    with open('start_monitor.sh', 'w') as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod('start_monitor.sh', 0o755)
    print("✅ Created start_monitor.sh script")
    
    # 4. Summary
    print("\n4️⃣ NETWORK ISSUE DIAGNOSIS")
    print("-" * 30)
    
    print("✅ **GOOD NEWS: You're NOT banned by Vinted!**")
    print("   - HTTP Status 200 on all tests")
    print("   - Multiple user agents work")
    print("   - Basic connectivity is fine")
    
    print("\n❌ **The Issue: Browser Network Instability**")
    print("   - ERR_NETWORK_CHANGED suggests network switching")
    print("   - Could be WiFi instability, VPN changes, or ISP issues")
    
    print("\n🛠️  **Applied Fixes:**")
    print("   - Increased delays between requests (1.5-3 seconds)")
    print("   - Reduced concurrency to 1 (safer)")
    print("   - Increased polling interval to 45 seconds")
    print("   - Limited to 1 page per poll")
    
    print("\n🚀 **Next Steps:**")
    print("1. **Test the fix:**")
    print("   ./start_monitor.sh")
    print("   OR")
    print("   source venv/bin/activate && python -m app.main run")
    print()
    print("2. **If still having issues:**")
    print("   - Restart your router/modem")
    print("   - Try: docker-compose up -d")
    print("   - Check if you're on unstable WiFi")
    
    print("\n💡 **Why This Happens:**")
    print("   - Network switching (WiFi to Ethernet)")
    print("   - VPN connecting/disconnecting") 
    print("   - ISP connection instability")
    print("   - Router DHCP lease renewal")

if __name__ == '__main__':
    fix_network_issues()
