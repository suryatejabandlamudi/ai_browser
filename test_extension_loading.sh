#!/bin/bash

# Test Chrome extension loading with error capture
echo "Testing Chrome extension loading..."

# Create temp profile
PROFILE_DIR="/tmp/ai_browser_test_profile"
rm -rf "$PROFILE_DIR"
mkdir -p "$PROFILE_DIR"

# Start Chrome with extension and capture errors
EXTENSION_DIR="/Volumes/ssd/apple/ai_browser/extension"

echo "Starting Chrome with extension..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --load-extension="$EXTENSION_DIR" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  --enable-logging \
  --log-level=0 \
  --v=1 \
  --enable-extension-activity-logging \
  --new-window \
  "chrome://extensions/" \
  > /tmp/chrome_debug.log 2>&1 &

CHROME_PID=$!
echo "Chrome PID: $CHROME_PID"

# Wait a bit then check the chrome logs
sleep 10

echo "Checking Chrome logs for extension errors..."
if [ -f "/tmp/chrome_debug.log" ]; then
    grep -i "extension\|error\|fail" /tmp/chrome_debug.log || echo "No extension errors found in logs"
else
    echo "Chrome debug log not found"
fi

# Check system console for Chrome messages
echo "Checking system console for Chrome extension messages..."
log show --predicate 'process == "Google Chrome"' --info --last 30s | grep -i "extension\|ai browser" || echo "No extension messages in system console"

echo "Chrome is running. Check chrome://extensions/ to see if AI Browser extension loaded."
echo "Look for any error messages in the extension card."
echo "Press Enter when done testing..."
read

# Cleanup
kill $CHROME_PID 2>/dev/null
rm -rf "$PROFILE_DIR"