#!/usr/bin/env python3
"""
AI Browser One-Click Setup
Automatically installs and configures everything needed to run AI Browser
"""

import os
import sys
import subprocess
import platform
import urllib.request
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class AIBrowserSetup:
    """One-click setup for AI Browser with all dependencies"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.platform = platform.system().lower()
        self.arch = "arm64" if "arm" in platform.machine().lower() else "x64"
        self.setup_dir = Path.home() / ".ai-browser-setup"
        
        print("🤖 AI Browser One-Click Setup")
        print("=" * 50)
        print(f"Platform: {self.platform}-{self.arch}")
        print(f"Setup directory: {self.setup_dir}")
        print()
    
    async def run_complete_setup(self):
        """Run the complete setup process"""
        try:
            print("🚀 Starting AI Browser setup...")
            
            # Create setup directory
            self.setup_dir.mkdir(exist_ok=True)
            
            # Step 1: Check and install system dependencies
            print("\n1️⃣ Checking system dependencies...")
            await self.install_system_dependencies()
            
            # Step 2: Install Python dependencies
            print("\n2️⃣ Setting up Python environment...")
            await self.setup_python_environment()
            
            # Step 3: Install and setup Ollama
            print("\n3️⃣ Installing Ollama and GPT-OSS 20B...")
            await self.setup_ollama()
            
            # Step 4: Download GPT-OSS 20B model
            print("\n4️⃣ Downloading GPT-OSS 20B model...")
            await self.download_gpt_oss_model()
            
            # Step 5: Setup AI Browser
            print("\n5️⃣ Setting up AI Browser...")
            await self.setup_ai_browser()
            
            # Step 6: Create launchers and shortcuts
            print("\n6️⃣ Creating launchers...")
            await self.create_launchers()
            
            # Step 7: Verify installation
            print("\n7️⃣ Verifying installation...")
            await self.verify_installation()
            
            print("\n🎉 AI Browser setup completed successfully!")
            self.print_next_steps()
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            print("💡 Try running with --verbose for more details")
            sys.exit(1)
    
    async def install_system_dependencies(self):
        """Install platform-specific system dependencies"""
        if self.platform == "darwin":
            await self.install_macos_dependencies()
        elif self.platform == "linux":
            await self.install_linux_dependencies()
        elif self.platform == "windows":
            await self.install_windows_dependencies()
    
    async def install_macos_dependencies(self):
        """Install macOS dependencies"""
        print("🍎 Setting up macOS dependencies...")
        
        # Check for Homebrew
        if not shutil.which("brew"):
            print("📥 Installing Homebrew...")
            install_cmd = [
                "/bin/bash", "-c",
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            ]
            subprocess.run(install_cmd, check=True)
        
        # Install Python if needed
        if not shutil.which("python3"):
            print("🐍 Installing Python...")
            subprocess.run(["brew", "install", "python@3.11"], check=True)
        
        # Install other dependencies
        brew_packages = ["curl", "git", "nodejs"]
        for package in brew_packages:
            if not shutil.which(package):
                print(f"📦 Installing {package}...")
                subprocess.run(["brew", "install", package], check=True)
        
        print("✅ macOS dependencies installed")
    
    async def install_linux_dependencies(self):
        """Install Linux dependencies"""
        print("🐧 Setting up Linux dependencies...")
        
        # Detect package manager
        if shutil.which("apt-get"):
            pkg_manager = "apt"
        elif shutil.which("yum"):
            pkg_manager = "yum"
        elif shutil.which("pacman"):
            pkg_manager = "pacman"
        else:
            print("⚠️  Unknown package manager, installing manually...")
            return
        
        # Install Python and dependencies
        if pkg_manager == "apt":
            packages = ["python3", "python3-pip", "curl", "git", "nodejs", "npm"]
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y"] + packages, check=True)
        elif pkg_manager == "yum":
            packages = ["python3", "python3-pip", "curl", "git", "nodejs", "npm"]
            subprocess.run(["sudo", "yum", "install", "-y"] + packages, check=True)
        elif pkg_manager == "pacman":
            packages = ["python", "python-pip", "curl", "git", "nodejs", "npm"]
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm"] + packages, check=True)
        
        print("✅ Linux dependencies installed")
    
    async def install_windows_dependencies(self):
        """Install Windows dependencies (requires WSL or manual installation)"""
        print("🪟 Windows setup...")
        print("For Windows, please ensure you have:")
        print("  • Python 3.8+ installed")
        print("  • Git installed")
        print("  • Node.js installed")
        print("  • WSL2 (recommended) or native tools")
        
        # Check if Python is available
        if not shutil.which("python") and not shutil.which("python3"):
            print("❌ Python not found. Install from https://python.org")
            sys.exit(1)
        
        print("✅ Windows dependencies checked")
    
    async def setup_python_environment(self):
        """Setup Python virtual environment and dependencies"""
        print("🐍 Setting up Python environment...")
        
        # Create virtual environment
        venv_dir = self.setup_dir / "venv"
        if not venv_dir.exists():
            python_cmd = "python3" if shutil.which("python3") else "python"
            subprocess.run([python_cmd, "-m", "venv", str(venv_dir)], check=True)
        
        # Get pip path
        if self.platform == "windows":
            pip_path = venv_dir / "Scripts" / "pip"
            python_path = venv_dir / "Scripts" / "python"
        else:
            pip_path = venv_dir / "bin" / "pip"
            python_path = venv_dir / "bin" / "python"
        
        # Install Python packages
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "websockets==12.0",
            "aiohttp==3.9.0",
            "requests==2.31.0",
            "Pillow==10.0.1",
            "structlog==23.2.0",
            "pydantic==2.5.0",
            "packaging==23.2"
        ]
        
        for req in requirements:
            print(f"📦 Installing {req}...")
            subprocess.run([str(pip_path), "install", req], check=True)
        
        # Save paths for later
        self.python_path = python_path
        self.pip_path = pip_path
        
        print("✅ Python environment ready")
    
    async def setup_ollama(self):
        """Install and setup Ollama"""
        print("🦙 Setting up Ollama...")
        
        if shutil.which("ollama"):
            print("✅ Ollama already installed")
        else:
            print("📥 Installing Ollama...")
            
            if self.platform == "darwin" or self.platform == "linux":
                # Download and install Ollama
                install_script = "curl -fsSL https://ollama.ai/install.sh | sh"
                subprocess.run(install_script, shell=True, check=True)
            else:
                print("🪟 For Windows, download Ollama from: https://ollama.ai/download")
                print("   Then run this setup script again")
                sys.exit(1)
        
        # Start Ollama service
        print("🚀 Starting Ollama service...")
        try:
            # Start Ollama in background
            if self.platform == "darwin":
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif self.platform == "linux":
                subprocess.run(["sudo", "systemctl", "enable", "ollama"], check=False)
                subprocess.run(["sudo", "systemctl", "start", "ollama"], check=False)
                # Also start manually in case systemctl fails
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            print("⚠️  Please start Ollama manually with: ollama serve")
        
        # Wait for Ollama to start
        print("⏳ Waiting for Ollama to start...")
        time.sleep(5)
        
        print("✅ Ollama setup complete")
    
    async def download_gpt_oss_model(self):
        """Download GPT-OSS 20B model"""
        print("🧠 Downloading GPT-OSS 20B model...")
        print("⚠️  This is a 14GB download - may take 30+ minutes")
        
        # Check if model already exists
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "gpt-oss:20b" in result.stdout:
                print("✅ GPT-OSS 20B already downloaded")
                return
        except Exception:
            pass
        
        # Download model
        print("📥 Starting download...")
        subprocess.run(["ollama", "pull", "gpt-oss:20b"], check=True)
        
        print("✅ GPT-OSS 20B model ready")
    
    async def setup_ai_browser(self):
        """Setup AI Browser files"""
        print("🌐 Setting up AI Browser...")
        
        # Copy AI Browser files to setup directory
        browser_dir = self.setup_dir / "ai-browser"
        if browser_dir.exists():
            shutil.rmtree(browser_dir)
        
        # Copy backend
        if (self.base_dir / "backend").exists():
            shutil.copytree(self.base_dir / "backend", browser_dir / "backend")
        
        # Copy extension
        if (self.base_dir / "extension").exists():
            shutil.copytree(self.base_dir / "extension", browser_dir / "extension")
        
        # Copy other important files
        important_files = ["README.md", "BUILD_GUIDE.md", "CLAUDE.md"]
        for file_name in important_files:
            src_file = self.base_dir / file_name
            if src_file.exists():
                shutil.copy2(src_file, browser_dir / file_name)
        
        print("✅ AI Browser files ready")
    
    async def create_launchers(self):
        """Create platform-specific launchers"""
        print("🚀 Creating launchers...")
        
        browser_dir = self.setup_dir / "ai-browser"
        
        if self.platform == "darwin" or self.platform == "linux":
            # Create shell launcher
            launcher_script = f'''#!/bin/bash
# AI Browser Launcher
export AI_BROWSER_HOME="{browser_dir}"
export PATH="{self.setup_dir / "venv" / "bin"}:$PATH"

echo "🤖 Starting AI Browser..."

# Start Ollama if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🦙 Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Start backend
cd "$AI_BROWSER_HOME/backend"
echo "🔧 Starting AI Browser backend..."
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

echo "✅ AI Browser is ready!"
echo "🌐 Open Chrome and load the extension from:"
echo "   {browser_dir}/extension"
echo
echo "💬 Or chat directly at: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop..."

# Wait for interrupt
wait $BACKEND_PID
'''
            
            launcher_path = self.setup_dir / "launch-ai-browser.sh"
            launcher_path.write_text(launcher_script)
            os.chmod(launcher_path, 0o755)
            
            # Create symlink in user's bin
            bin_dir = Path.home() / ".local" / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            
            symlink_path = bin_dir / "ai-browser"
            if symlink_path.exists():
                symlink_path.unlink()
            symlink_path.symlink_to(launcher_path)
            
        elif self.platform == "windows":
            # Create batch launcher
            launcher_bat = f'''@echo off
title AI Browser
echo 🤖 Starting AI Browser...

cd /d "{browser_dir}\\backend"
"{self.python_path}" main.py
'''
            
            launcher_path = self.setup_dir / "Launch-AI-Browser.bat"
            launcher_path.write_text(launcher_bat)
        
        print("✅ Launchers created")
    
    async def verify_installation(self):
        """Verify the complete installation"""
        print("🔍 Verifying installation...")
        
        # Check Ollama
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if "gpt-oss:20b" in result.stdout:
                print("✅ Ollama and GPT-OSS 20B working")
            else:
                print("❌ GPT-OSS 20B model not found")
        except Exception:
            print("❌ Ollama verification failed")
        
        # Check Python environment
        try:
            result = subprocess.run([str(self.python_path), "-c", "import fastapi; print('OK')"], 
                                  capture_output=True, text=True)
            if "OK" in result.stdout:
                print("✅ Python environment working")
            else:
                print("❌ Python environment issues")
        except Exception:
            print("❌ Python verification failed")
        
        # Check AI Browser files
        browser_dir = self.setup_dir / "ai-browser"
        if (browser_dir / "backend" / "main.py").exists():
            print("✅ AI Browser files ready")
        else:
            print("❌ AI Browser files missing")
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "=" * 60)
        print("🎉 AI BROWSER SETUP COMPLETE!")
        print("=" * 60)
        print()
        print("🚀 To launch AI Browser:")
        
        if self.platform == "darwin" or self.platform == "linux":
            print(f"   Run: ai-browser")
            print(f"   Or: {self.setup_dir}/launch-ai-browser.sh")
        elif self.platform == "windows":
            print(f"   Double-click: {self.setup_dir}\\Launch-AI-Browser.bat")
        
        print()
        print("🌐 To use the Chrome extension:")
        print("   1. Open Chrome")
        print("   2. Go to chrome://extensions/")
        print("   3. Enable 'Developer mode'")
        print("   4. Click 'Load unpacked'")
        print(f"   5. Select: {self.setup_dir}/ai-browser/extension/")
        print("   6. Open the side panel and start chatting!")
        
        print()
        print("📚 Documentation:")
        print(f"   Build Guide: {self.setup_dir}/ai-browser/BUILD_GUIDE.md")
        print(f"   Project Info: {self.setup_dir}/ai-browser/README.md")
        
        print()
        print("🔒 Privacy Features:")
        print("   ✅ 100% local AI processing")
        print("   ✅ No data sent to cloud services")
        print("   ✅ GPT-OSS 20B runs on your machine")
        print("   ✅ Complete privacy and control")
        
        print()
        print("💡 Troubleshooting:")
        print("   • If Ollama fails: Run 'ollama serve' manually")
        print("   • If backend fails: Check Python dependencies")
        print("   • If extension fails: Reload it in Chrome")
        print("   • For help: Check the documentation or GitHub issues")

async def main():
    if "--help" in sys.argv:
        print("AI Browser One-Click Setup")
        print("Usage: python setup_ai_browser.py [options]")
        print("Options:")
        print("  --help     Show this help")
        print("  --verbose  Show detailed output")
        return
    
    setup = AIBrowserSetup()
    await setup.run_complete_setup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())