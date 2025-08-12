#!/bin/bash

# Final Chromium Build with Proper Environment
set -e

# Environment setup
export PATH="/Volumes/ssd/apple/ai_browser/temp_depot_tools:$PATH"
export DEPOT_TOOLS_UPDATE=0

CHROMIUM_SRC="/Volumes/ssd/apple/ai_browser/backend/chromium/build/src"
LOGS_DIR="/Volumes/ssd/apple/ai_browser/logs"
BUILD_LOG="$LOGS_DIR/chromium_build_final.log"

echo "========================================" | tee "$BUILD_LOG"
echo "CHROMIUM BUILD WITH AI INTEGRATION" | tee -a "$BUILD_LOG"
echo "Started: $(date)" | tee -a "$BUILD_LOG"
echo "PID: $$" | tee -a "$BUILD_LOG"  
echo "========================================" | tee -a "$BUILD_LOG"

# Save PID for monitoring
echo "$$" > "$LOGS_DIR/chromium_build.pid"

cd "$CHROMIUM_SRC" || { echo "Failed to cd to $CHROMIUM_SRC"; exit 1; }

# Apply working patches only (skip malformed ones)
echo "=== APPLYING WORKING PATCHES ===" | tee -a "$BUILD_LOG"
PATCHES_DIR="/Volumes/ssd/apple/ai_browser/backend/chromium/patches/ai-browser"

for patch_num in 006 007 008 009 011; do  # Skip 010 and 012 - malformed
    patch_file="${PATCHES_DIR}/${patch_num}"-*.patch
    if ls $patch_file 1> /dev/null 2>&1; then
        echo "Applying patch: $patch_file" | tee -a "$BUILD_LOG"
        if patch --dry-run -p1 < $patch_file >> "$BUILD_LOG" 2>&1; then
            if patch -p1 < $patch_file >> "$BUILD_LOG" 2>&1; then
                echo "✅ Patch $patch_num applied successfully" | tee -a "$BUILD_LOG"
            else
                echo "⚠️ Patch $patch_num failed to apply (conflicts)" | tee -a "$BUILD_LOG"
            fi
        else
            echo "⚠️ Patch $patch_num dry-run failed, skipping" | tee -a "$BUILD_LOG"
        fi
    fi
done

# Verify gn is available
echo "=== VERIFYING BUILD TOOLS ===" | tee -a "$BUILD_LOG"
if which gn >> "$BUILD_LOG" 2>&1; then
    echo "✅ GN build system available: $(which gn)" | tee -a "$BUILD_LOG"
else
    echo "❌ GN not found in PATH" | tee -a "$BUILD_LOG"
    exit 1
fi

if which autoninja >> "$BUILD_LOG" 2>&1; then
    echo "✅ Autoninja available: $(which autoninja)" | tee -a "$BUILD_LOG"
else
    echo "❌ Autoninja not found" | tee -a "$BUILD_LOG"
    exit 1
fi

# Configure build
echo "=== CONFIGURING BUILD ===" | tee -a "$BUILD_LOG"
BUILD_ARGS='
is_debug=false 
use_goma=false
enable_nacl=false
target_cpu="x64"
is_component_build=false
'

if gn gen out/Default --args="$BUILD_ARGS" >> "$BUILD_LOG" 2>&1; then
    echo "✅ Build configuration successful" | tee -a "$BUILD_LOG"
else
    echo "❌ Build configuration failed" | tee -a "$BUILD_LOG"
    exit 1
fi

# Start the build
echo "=== STARTING COMPILATION ===" | tee -a "$BUILD_LOG"
echo "This will take approximately 12 hours on this machine..." | tee -a "$BUILD_LOG"
echo "Build can be monitored with: tail -f $BUILD_LOG" | tee -a "$BUILD_LOG"

BUILD_START_TIME=$(date +%s)

# Run the build with progress monitoring
if autoninja -C out/Default chrome 2>&1 | while IFS= read -r line; do
    echo "$line" | tee -a "$BUILD_LOG"
    
    # Update progress periodically
    if [[ "$line" == *"[1/"* ]] || [[ "$line" == *"[2/"* ]] || [[ "$line" == *"[5/"* ]]; then
        current_time=$(date +%s)
        elapsed=$((current_time - BUILD_START_TIME))
        echo "=== PROGRESS UPDATE: $(date) - Elapsed: ${elapsed}s ===" >> "$BUILD_LOG"
    fi
done; then
    echo "========================================" | tee -a "$BUILD_LOG"
    echo "✅ BUILD COMPLETED SUCCESSFULLY!" | tee -a "$BUILD_LOG"
    echo "Finished: $(date)" | tee -a "$BUILD_LOG"
    echo "Total time: $(($(date +%s) - BUILD_START_TIME)) seconds" | tee -a "$BUILD_LOG"
    echo "Binary location: $CHROMIUM_SRC/out/Default/chrome" | tee -a "$BUILD_LOG"
    echo "========================================" | tee -a "$BUILD_LOG"
    
    # Clean up
    rm -f "$LOGS_DIR/chromium_build.pid"
else
    echo "========================================" | tee -a "$BUILD_LOG"
    echo "❌ BUILD FAILED!" | tee -a "$BUILD_LOG"
    echo "Failed at: $(date)" | tee -a "$BUILD_LOG"
    echo "Check the log above for specific errors" | tee -a "$BUILD_LOG"
    echo "========================================" | tee -a "$BUILD_LOG"
    exit 1
fi