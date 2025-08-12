#!/bin/bash

# Simple Chromium build script with proper logging
set -x  # Enable debug output

CHROMIUM_SRC="/Volumes/ssd/apple/ai_browser/backend/chromium/build/src"
LOGS_DIR="/Volumes/ssd/apple/ai_browser/logs"
BUILD_LOG="$LOGS_DIR/chromium_build.log"

echo "Starting Chromium build at $(date)" | tee "$BUILD_LOG"
echo "Chromium source: $CHROMIUM_SRC" | tee -a "$BUILD_LOG"

# Check if source directory exists
if [ ! -d "$CHROMIUM_SRC" ]; then
    echo "ERROR: Chromium source directory not found: $CHROMIUM_SRC" | tee -a "$BUILD_LOG"
    exit 1
fi

cd "$CHROMIUM_SRC" || exit 1
echo "Changed to directory: $(pwd)" | tee -a "$BUILD_LOG"

# Apply patches
echo "=== APPLYING PATCHES ===" | tee -a "$BUILD_LOG"
PATCHES_DIR="/Volumes/ssd/apple/ai_browser/backend/chromium/patches/ai-browser"

for patch_num in 006 007 008 009 010 011 012; do
    patch_file="${PATCHES_DIR}/${patch_num}"-*.patch
    if ls $patch_file 1> /dev/null 2>&1; then
        echo "Applying patch: $patch_file" | tee -a "$BUILD_LOG"
        if patch -p1 < $patch_file >> "$BUILD_LOG" 2>&1; then
            echo "✅ Patch $patch_num applied successfully" | tee -a "$BUILD_LOG"
        else
            echo "❌ Failed to apply patch $patch_num" | tee -a "$BUILD_LOG"
            echo "Continuing with remaining patches..." | tee -a "$BUILD_LOG"
        fi
    else
        echo "⚠️ Patch file not found: $patch_file" | tee -a "$BUILD_LOG"
    fi
done

# Configure build
echo "=== CONFIGURING BUILD ===" | tee -a "$BUILD_LOG"
if gn gen out/Default --args='is_debug=false use_goma=false' >> "$BUILD_LOG" 2>&1; then
    echo "✅ Build configuration successful" | tee -a "$BUILD_LOG"
else
    echo "❌ Build configuration failed" | tee -a "$BUILD_LOG"
    exit 1
fi

# Build
echo "=== STARTING COMPILATION ===" | tee -a "$BUILD_LOG"
echo "This will take approximately 12 hours..." | tee -a "$BUILD_LOG"

if autoninja -C out/Default chrome >> "$BUILD_LOG" 2>&1; then
    echo "✅ BUILD COMPLETED SUCCESSFULLY!" | tee -a "$BUILD_LOG"
    echo "Build finished at $(date)" | tee -a "$BUILD_LOG"
else
    echo "❌ BUILD FAILED!" | tee -a "$BUILD_LOG"
    exit 1
fi