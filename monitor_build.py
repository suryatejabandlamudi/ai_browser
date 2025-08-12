#!/usr/bin/env python3
"""
Chromium Build Monitor - Real-time build status and progress tracker
Usage: python3 monitor_build.py
"""

import json
import os
import time
import subprocess
import sys
from datetime import datetime, timedelta

def load_status():
    """Load build status from JSON file."""
    status_file = "/Volumes/ssd/apple/ai_browser/logs/build_status.json"
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "not_started", "message": "Build not started yet"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Status file corrupted"}

def get_log_tail(log_file, lines=10):
    """Get last N lines from log file."""
    try:
        result = subprocess.run(['tail', f'-{lines}', log_file], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Log file not accessible"

def format_duration(start_time_str):
    """Calculate and format elapsed time."""
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        elapsed = datetime.now() - start_time.replace(tzinfo=None)
        
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "Unknown"

def get_process_status(pid):
    """Check if process is still running."""
    if not pid or pid == "null":
        return "No PID"
    
    try:
        # Check if process exists
        subprocess.run(['ps', '-p', str(pid)], check=True, 
                      capture_output=True)
        return "Running"
    except subprocess.CalledProcessError:
        return "Stopped"

def display_status():
    """Display formatted build status."""
    status = load_status()
    
    print("╔════════════════════════════════════════╗")
    print("║         CHROMIUM BUILD MONITOR         ║")
    print("╠════════════════════════════════════════╣")
    
    if status.get("status") == "not_started":
        print("║ Status: Not Started                    ║")
        print("║                                        ║")
        print("║ Run: ./chromium_build_manager.sh start║")
    else:
        # Status line
        status_display = {
            "initializing": "🔄 Initializing",
            "running": "🔨 Building", 
            "completed": "✅ Completed",
            "failed": "❌ Failed",
            "killed": "🛑 Killed"
        }
        
        current_status = status_display.get(status.get("status", "unknown"), "❓ Unknown")
        print(f"║ Status: {current_status:<25} ║")
        
        # Current step
        step = status.get("current_step", "unknown").replace("_", " ").title()
        print(f"║ Step: {step:<29} ║")
        
        # Progress
        progress = status.get("progress", "0%")
        print(f"║ Progress: {progress:<27} ║")
        
        # Time info
        if "start_time" in status:
            elapsed = format_duration(status["start_time"])
            print(f"║ Elapsed: {elapsed:<28} ║")
        
        remaining = status.get("estimated_remaining", "Unknown")
        print(f"║ Remaining: {remaining:<26} ║")
        
        # Process status
        if "pid" in status:
            proc_status = get_process_status(status["pid"])
            print(f"║ Process: {proc_status:<28} ║")
    
    print("╚════════════════════════════════════════╝")
    
    # Show recent log entries if available
    if "build_log" in status and os.path.exists(status["build_log"]):
        print("\n📋 Recent Log Entries:")
        print("-" * 50)
        print(get_log_tail(status["build_log"], 5))
    
    print(f"\n⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main monitoring loop."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            display_status()
            return
        elif sys.argv[1] == "--help":
            print("Usage: python3 monitor_build.py [--once|--help]")
            print("  --once  Show status once and exit")
            print("  --help  Show this help message")
            return
    
    print("🔍 Chromium Build Monitor - Press Ctrl+C to exit\n")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            display_status()
            
            # Quick commands reference
            print("\n💡 Quick Commands:")
            print("   ./chromium_build_manager.sh status  - Detailed status")
            print("   ./chromium_build_manager.sh logs    - View logs")
            print("   ./chromium_build_manager.sh kill    - Stop build")
            
            # Wait before next update
            time.sleep(30)  # Update every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped. Build continues in background.")
        sys.exit(0)

if __name__ == "__main__":
    main()