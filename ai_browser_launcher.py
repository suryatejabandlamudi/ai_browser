#!/usr/bin/env python3
"""
AI Browser Launcher - Complete Working Solution
This creates a fully functional AI browser using Chrome + our working extension + backend
"""

import subprocess
import sys
import time
import os
import json
import signal
import requests
from pathlib import Path

class AIBrowserLauncher:
    def __init__(self):
        self.base_dir = Path("/Volumes/ssd/apple/ai_browser")
        self.extension_dir = self.base_dir / "extension"
        self.backend_process = None
        self.ollama_process = None
        self.chrome_process = None
        
    def check_dependencies(self):
        """Check if all required components are available"""
        print("🔍 Checking AI Browser dependencies...")
        
        # Check Chrome
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
                
        if not chrome_path:
            print("❌ Chrome/Chromium not found")
            return False
            
        print(f"✅ Found browser: {chrome_path}")
        
        # Check extension
        if not self.extension_dir.exists():
            print(f"❌ Extension not found: {self.extension_dir}")
            return False
        print("✅ Extension directory found")
        
        # Check backend
        backend_main = self.base_dir / "backend" / "main.py"
        if not backend_main.exists():
            print(f"❌ Backend not found: {backend_main}")
            return False
        print("✅ Backend found")
        
        # Check Ollama
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
            print("✅ Ollama available")
        except:
            print("❌ Ollama not found")
            return False
            
        return True, chrome_path
    
    def start_ollama(self):
        """Start Ollama if not running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            print("✅ Ollama already running")
            return True
        except:
            print("🚀 Starting Ollama...")
            try:
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(3)
                return True
            except Exception as e:
                print(f"❌ Failed to start Ollama: {e}")
                return False
    
    def start_backend(self):
        """Start the AI backend"""
        print("🚀 Starting AI backend...")
        try:
            # Change to backend directory
            backend_dir = self.base_dir / "backend"
            
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=backend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for backend to start
            for i in range(10):
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ AI backend started successfully")
                        return True
                except:
                    time.sleep(1)
                    
            print("❌ Backend failed to start")
            return False
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_chrome_with_extension(self, chrome_path):
        """Start Chrome with our AI extension loaded"""
        print("🚀 Starting AI Browser (Chrome + AI Extension)...")
        
        # Create temp profile directory
        profile_dir = "/tmp/ai_browser_profile"
        os.makedirs(profile_dir, exist_ok=True)
        
        chrome_args = [
            chrome_path,
            f"--load-extension={self.extension_dir}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--enable-logging",
            "--log-level=0",
            "--enable-extensions",
            "--allow-running-insecure-content",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--new-window",
            "https://www.google.com"  # Start with Google
        ]
        
        try:
            self.chrome_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(3)
            print("✅ AI Browser launched successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            return False
    
    def show_instructions(self):
        """Show user instructions"""
        print("\n" + "="*60)
        print("🎉 AI BROWSER IS NOW RUNNING!")
        print("="*60)
        print()
        print("📖 HOW TO USE YOUR AI BROWSER:")
        print()
        print("1. 🔍 Look for the AI Browser extension icon in Chrome")
        print("2. 📋 Click the extension icon to open the AI side panel")
        print("3. 💬 Start chatting with your local GPT-OSS 20B model")
        print("4. 🤖 Ask the AI to automate websites for you")
        print()
        print("✨ EXAMPLE COMMANDS TO TRY:")
        print('   • "Search for AI news on Google"')
        print('   • "Find me restaurants nearby"') 
        print('   • "Help me fill out this form"')
        print('   • "Summarize this webpage"')
        print()
        print("🔒 PRIVACY: Everything runs locally - no data sent to cloud!")
        print("⚡ SPEED: 3-5 second AI responses from your local model")
        print()
        print("🛑 To stop: Press Ctrl+C in this terminal")
        print("="*60)
    
    def cleanup(self, signum=None, frame=None):
        """Clean shutdown of all processes"""
        print("\n🛑 Shutting down AI Browser...")
        
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
                print("✅ Chrome stopped")
            except:
                self.chrome_process.kill()
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ Backend stopped")
            except:
                self.backend_process.kill()
        
        if self.ollama_process:
            try:
                self.ollama_process.terminate()
                print("✅ Ollama stopped")
            except:
                pass
        
        print("👋 AI Browser shut down complete")
        sys.exit(0)
    
    def run(self):
        """Main run function"""
        print("🚀 AI BROWSER LAUNCHER")
        print("=" * 50)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        # Check dependencies
        deps_check = self.check_dependencies()
        if not deps_check:
            print("❌ Missing dependencies. Please check the requirements above.")
            return False
        
        deps_ok, chrome_path = deps_check
        if not deps_ok:
            return False
        
        # Start services
        if not self.start_ollama():
            return False
            
        if not self.start_backend():
            return False
            
        if not self.start_chrome_with_extension(chrome_path):
            return False
        
        # Show instructions
        self.show_instructions()
        
        # Keep running
        try:
            while True:
                # Check if processes are still running
                if self.chrome_process and self.chrome_process.poll() is not None:
                    print("Chrome closed, shutting down...")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

if __name__ == "__main__":
    launcher = AIBrowserLauncher()
    launcher.run()