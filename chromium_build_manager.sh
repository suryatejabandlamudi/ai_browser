#!/bin/bash

# Chromium Build Manager - Persistent build with monitoring
# This script manages the long-running Chromium build process

set -e

SCRIPT_DIR="/Volumes/ssd/apple/ai_browser"
BUILD_LOG="$SCRIPT_DIR/logs/chromium_build.log"
STATUS_FILE="$SCRIPT_DIR/logs/build_status.json"
PID_FILE="$SCRIPT_DIR/logs/build.pid"
CHROMIUM_SRC="/Volumes/ssd/apple/ai_browser/backend/chromium/build/src"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Initialize status
init_status() {
    cat > "$STATUS_FILE" << EOF
{
    "status": "initializing",
    "start_time": "$(date -Iseconds)",
    "current_step": "preparation",
    "progress": "0%",
    "estimated_remaining": "12 hours",
    "last_update": "$(date -Iseconds)",
    "build_log": "$BUILD_LOG",
    "pid": null
}
EOF
}

# Update status
update_status() {
    local status="$1"
    local step="$2"
    local progress="$3"
    local remaining="$4"
    
    local pid_value="null"
    if [ -f "$PID_FILE" ]; then
        pid_value=$(cat "$PID_FILE")
    fi
    
    cat > "$STATUS_FILE" << EOF
{
    "status": "$status",
    "start_time": "$(grep start_time "$STATUS_FILE" | cut -d'"' -f4)",
    "current_step": "$step",
    "progress": "$progress",
    "estimated_remaining": "$remaining",
    "last_update": "$(date -Iseconds)",
    "build_log": "$BUILD_LOG",
    "pid": $pid_value
}
EOF
}

# Apply patches function
apply_patches() {
    echo "=== APPLYING AI PATCHES ===" | tee -a "$BUILD_LOG"
    cd "$CHROMIUM_SRC" || exit 1
    
    local patches_dir="/Volumes/ssd/apple/ai_browser/backend/chromium/patches/ai-browser"
    
    for patch in 006 007 008 009 010 011 012; do
        echo "Applying patch ${patch}..." | tee -a "$BUILD_LOG"
        if patch -p1 < "${patches_dir}/${patch}"-*.patch >> "$BUILD_LOG" 2>&1; then
            echo "✅ Patch ${patch} applied successfully" | tee -a "$BUILD_LOG"
        else
            echo "❌ Patch ${patch} failed to apply" | tee -a "$BUILD_LOG"
            return 1
        fi
    done
    
    echo "=== ALL PATCHES APPLIED ===" | tee -a "$BUILD_LOG"
    return 0
}

# Build function
build_chromium() {
    echo "=== STARTING CHROMIUM BUILD ===" | tee -a "$BUILD_LOG"
    cd "$CHROMIUM_SRC" || exit 1
    
    # Configure build
    echo "Configuring build..." | tee -a "$BUILD_LOG"
    gn gen out/Default --args='is_debug=false use_goma=false' >> "$BUILD_LOG" 2>&1
    
    # Start build
    echo "Starting compilation..." | tee -a "$BUILD_LOG"
    autoninja -C out/Default chrome >> "$BUILD_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "=== BUILD COMPLETED SUCCESSFULLY ===" | tee -a "$BUILD_LOG"
        return 0
    else
        echo "=== BUILD FAILED ===" | tee -a "$BUILD_LOG"
        return 1
    fi
}

# Main build process
main_build() {
    init_status
    
    echo "Starting Chromium build process at $(date)" | tee "$BUILD_LOG"
    echo "Process ID: $$" | tee -a "$BUILD_LOG"
    echo "$$" > "$PID_FILE"
    
    # Step 1: Apply patches
    update_status "running" "applying_patches" "5%" "11.5 hours"
    if apply_patches; then
        echo "Patches applied successfully" | tee -a "$BUILD_LOG"
    else
        update_status "failed" "patch_application_failed" "5%" "N/A"
        echo "Failed to apply patches" | tee -a "$BUILD_LOG"
        exit 1
    fi
    
    # Step 2: Build
    update_status "running" "compiling" "10%" "11 hours"
    if build_chromium; then
        update_status "completed" "build_successful" "100%" "0 hours"
        echo "Build completed successfully!" | tee -a "$BUILD_LOG"
    else
        update_status "failed" "compilation_failed" "90%" "N/A"
        echo "Build failed!" | tee -a "$BUILD_LOG"
        exit 1
    fi
    
    # Cleanup
    rm -f "$PID_FILE"
    echo "Build process finished at $(date)" | tee -a "$BUILD_LOG"
}

# Handle command line arguments
case "${1:-start}" in
    "start")
        echo "Starting persistent Chromium build..."
        nohup bash -c "$(declare -f init_status update_status apply_patches build_chromium main_build); main_build" > /dev/null 2>&1 &
        NOHUP_PID=$!
        echo "$NOHUP_PID" > "$PID_FILE"
        echo "Build started with PID: $NOHUP_PID"
        echo "Monitor with: $0 status"
        echo "View logs with: $0 logs"
        ;;
    "status")
        if [ -f "$STATUS_FILE" ]; then
            echo "=== BUILD STATUS ==="
            cat "$STATUS_FILE" | python3 -m json.tool
        else
            echo "No build status found. Start with: $0 start"
        fi
        ;;
    "logs")
        if [ -f "$BUILD_LOG" ]; then
            tail -f "$BUILD_LOG"
        else
            echo "No build log found."
        fi
        ;;
    "kill")
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            echo "Killing build process $PID..."
            kill "$PID" 2>/dev/null || echo "Process already stopped"
            rm -f "$PID_FILE"
            update_status "killed" "user_terminated" "N/A" "N/A"
        else
            echo "No running build process found."
        fi
        ;;
    *)
        echo "Usage: $0 {start|status|logs|kill}"
        echo "  start  - Start the build process in background"
        echo "  status - Show current build status"
        echo "  logs   - View build logs in real-time"
        echo "  kill   - Stop the build process"
        ;;
esac