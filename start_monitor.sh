#!/bin/bash
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
