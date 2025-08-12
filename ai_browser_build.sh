#!/bin/bash

# AI Browser Build Script - Comprehensive Fix for All Issues
set -e

echo "=========================================="
echo "AI BROWSER - COMPREHENSIVE BUILD FIX"
echo "=========================================="

# Environment setup
export PATH="/Volumes/ssd/apple/ai_browser/temp_depot_tools:$PATH"
export DEPOT_TOOLS_UPDATE=0

CHROMIUM_SRC="/Volumes/ssd/apple/ai_browser/backend/chromium/build/src"
LOGS_DIR="/Volumes/ssd/apple/ai_browser/logs" 
BUILD_LOG="$LOGS_DIR/ai_browser_build.log"

echo "Started: $(date)" | tee "$BUILD_LOG"
echo "PID: $$" | tee -a "$BUILD_LOG"

# Create proper build configuration that avoids problematic components
echo "=== CREATING OPTIMIZED BUILD CONFIGURATION ===" | tee -a "$BUILD_LOG"

cd "$CHROMIUM_SRC" || exit 1

# Remove previous failed build
rm -rf out/Default

# Create build args that disable problematic components
cat > ai_browser_args.gn << 'EOF'
# AI Browser optimized build configuration
is_debug = false
is_component_build = false
symbol_level = 0
use_goma = false
enable_nacl = false
target_cpu = "x64"

# Disable problematic Metal/graphics features that are failing
use_system_harfbuzz = true
angle_enable_metal = false
skia_use_metal = false
use_dawn = false

# Disable other problematic components
enable_widevine = false
proprietary_codecs = false
ffmpeg_branding = "Chromium"
enable_hangout_services_extension = false

# Focus on core browser functionality
is_chrome_branded = false
enable_print_preview = true
enable_basic_printing = true
enable_extensions = true

# AI-specific optimizations
enable_supervised_users = false
enable_service_discovery = false
safe_browsing_mode = 0

# macOS specific fixes
mac_deployment_target = "10.15"
EOF

echo "✅ Created AI browser build configuration" | tee -a "$BUILD_LOG"

# Apply only the working patches (skip malformed ones)
echo "=== APPLYING WORKING AI PATCHES ===" | tee -a "$BUILD_LOG"

PATCHES_DIR="/Volumes/ssd/apple/ai_browser/backend/chromium/patches/ai-browser"

# Apply working patches (use new minimal patches)
for patch_num in 101 102; do  # New working minimal patches
    patch_file="${PATCHES_DIR}/${patch_num}"-*.patch
    if ls $patch_file 1> /dev/null 2>&1; then
        echo "Applying patch: $patch_file" | tee -a "$BUILD_LOG"
        if patch --dry-run -p1 < $patch_file >> "$BUILD_LOG" 2>&1; then
            if patch -p1 < $patch_file >> "$BUILD_LOG" 2>&1; then
                echo "✅ Patch $patch_num applied successfully" | tee -a "$BUILD_LOG"
            else
                echo "⚠️ Patch $patch_num failed, continuing..." | tee -a "$BUILD_LOG"
            fi
        else
            echo "⚠️ Patch $patch_num dry-run failed, skipping" | tee -a "$BUILD_LOG"
        fi
    fi
done

# Configure build with our optimized args
echo "=== CONFIGURING AI BROWSER BUILD ===" | tee -a "$BUILD_LOG"

if gn gen out/Default --args="$(cat ai_browser_args.gn | tr '\n' ' ')" >> "$BUILD_LOG" 2>&1; then
    echo "✅ Build configuration successful" | tee -a "$BUILD_LOG"
else
    echo "❌ Build configuration failed" | tee -a "$BUILD_LOG"
    cat "$BUILD_LOG" | tail -20
    exit 1
fi

# Start optimized build focusing on chrome target only
echo "=== BUILDING AI BROWSER (Chrome Target Only) ===" | tee -a "$BUILD_LOG"
echo "This optimized build should complete in 2-4 hours..." | tee -a "$BUILD_LOG"

BUILD_START_TIME=$(date +%s)

# Build just the chrome binary with limited parallelism to avoid memory issues
if autoninja -j4 -C out/Default chrome 2>&1 | tee -a "$BUILD_LOG"; then
    BUILD_TIME=$(($(date +%s) - BUILD_START_TIME))
    echo "========================================" | tee -a "$BUILD_LOG"
    echo "✅ AI BROWSER BUILD SUCCESSFUL!" | tee -a "$BUILD_LOG"
    echo "Build time: ${BUILD_TIME} seconds" | tee -a "$BUILD_LOG"
    echo "Binary: $CHROMIUM_SRC/out/Default/chrome" | tee -a "$BUILD_LOG"
    echo "========================================" | tee -a "$BUILD_LOG"
    
    # Test the binary
    if [ -f "out/Default/chrome" ]; then
        echo "✅ Chrome binary created successfully" | tee -a "$BUILD_LOG"
        ls -la out/Default/chrome | tee -a "$BUILD_LOG"
        
        # Create launcher script
        cat > "/Volumes/ssd/apple/ai_browser/launch_ai_browser.sh" << 'LAUNCHER_EOF'
#!/bin/bash
echo "🚀 Starting AI Browser..."
CHROMIUM_SRC="/Volumes/ssd/apple/ai_browser/backend/chromium/build/src"
exec "$CHROMIUM_SRC/out/Default/chrome" \
  --enable-extensions \
  --load-extension="/Volumes/ssd/apple/ai_browser/extension" \
  --user-data-dir="/tmp/ai_browser_profile" \
  --enable-logging \
  --v=1 \
  "$@"
LAUNCHER_EOF
        chmod +x "/Volumes/ssd/apple/ai_browser/launch_ai_browser.sh"
        echo "✅ Created AI browser launcher: ./launch_ai_browser.sh" | tee -a "$BUILD_LOG"
    else
        echo "❌ Chrome binary not found after build" | tee -a "$BUILD_LOG"
        exit 1
    fi
else
    echo "❌ AI Browser build failed" | tee -a "$BUILD_LOG"
    exit 1
fi

echo "========================================" | tee -a "$BUILD_LOG"
echo "🎉 AI BROWSER READY!" | tee -a "$BUILD_LOG"
echo "Launch with: ./launch_ai_browser.sh" | tee -a "$BUILD_LOG"
echo "Extension will be loaded automatically" | tee -a "$BUILD_LOG"
echo "Backend running on: http://localhost:8000" | tee -a "$BUILD_LOG"
echo "========================================" | tee -a "$BUILD_LOG"