#\!/bin/bash
while true; do
    CURRENT=$(tail -1 build_log.txt | grep -o '\[[0-9]*/' | tr -d '[/')
    if [ \! -z "$CURRENT" ]; then
        PERCENT=$(echo "scale=1; $CURRENT/53598*100" | bc)
        echo "$(date): Build Progress: $CURRENT/53598 ($PERCENT%)"
        
        # Check if chrome binary exists
        if [ -f "backend/chromium/src/out/AIBrowser/chrome" ]; then
            echo "🎉 CHROME BINARY FOUND\! Build complete\!"
            echo "$(date): Starting automatic packaging..."
            python3 package_browser.py
            break
        fi
    fi
    sleep 30
done
