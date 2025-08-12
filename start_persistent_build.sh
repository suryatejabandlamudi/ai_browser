#!/bin/bash

# Start persistent Chromium build with proper environment
echo "🚀 Starting persistent Chromium build..."

# Set up environment
export PATH="/Volumes/ssd/apple/ai_browser/temp_depot_tools:$PATH"
export DEPOT_TOOLS_UPDATE=0

# Initialize depot_tools if needed
if [ ! -f "/Volumes/ssd/apple/ai_browser/temp_depot_tools/python3_bin_reldir.txt" ]; then
    echo "Initializing depot_tools..."
    cd /Volumes/ssd/apple/ai_browser/temp_depot_tools
    ./ensure_bootstrap
fi

# Start the build in background with nohup
cd /Volumes/ssd/apple/ai_browser
nohup ./final_build.sh > /dev/null 2>&1 &
BUILD_PID=$!

echo "BUILD STARTED!"
echo "PID: $BUILD_PID"
echo "$BUILD_PID" > logs/chromium_build.pid

echo ""
echo "📊 HOW TO MONITOR THE BUILD:"
echo "1. View logs: tail -f logs/chromium_build_final.log"
echo "2. Monitor tool: python3 monitor_build.py" 
echo "3. Check process: ps -p $BUILD_PID"
echo "4. Kill build: kill $BUILD_PID"
echo ""
echo "Build will take ~12 hours and survives terminal disconnection!"