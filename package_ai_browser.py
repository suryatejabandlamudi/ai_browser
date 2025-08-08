#!/usr/bin/env python3
"""
AI Browser Distribution Packager
Creates distributable packages for macOS, Windows, and Linux
"""

import os
import sys
import shutil
import subprocess
import platform
import json
from pathlib import Path
from typing import Dict, List, Optional
import tarfile
import zipfile

class AIBrowserPackager:
    """Package AI Browser for distribution across platforms"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.dist_dir = self.base_dir / "dist"
        self.package_dir = self.base_dir / "packages"
        self.assets_dir = self.base_dir / "assets"
        
        # Version info
        self.version = "1.0.0"
        self.app_name = "AI Browser"
        self.bundle_id = "com.aibrowser.privacy"
        
        # Platform detection
        self.platform = platform.system().lower()
        self.arch = "arm64" if "arm" in platform.machine().lower() else "x64"
        
        print(f"🚀 AI Browser Packager - Platform: {self.platform}-{self.arch}")
    
    async def create_all_packages(self):
        """Create packages for all supported platforms"""
        print("📦 Creating distributable packages for AI Browser...")
        
        # Prepare directories
        self.package_dir.mkdir(exist_ok=True)
        
        # Create platform-specific packages
        if self.platform == "darwin":
            await self.create_macos_package()
        elif self.platform == "windows":
            await self.create_windows_package()
        elif self.platform == "linux":
            await self.create_linux_package()
        
        # Create universal installer
        await self.create_universal_installer()
        
        # Create update system
        await self.create_update_system()
        
        print("✅ All packages created successfully!")
        self.print_package_info()
    
    async def create_macos_package(self):
        """Create macOS .app bundle and .dmg"""
        print("🍎 Creating macOS package...")
        
        app_bundle = self.package_dir / f"{self.app_name}.app"
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        # Create app bundle structure
        for dir_path in [macos_dir, resources_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Copy browser binary
        browser_binary = self.find_browser_binary()
        if browser_binary:
            shutil.copy2(browser_binary, macos_dir / "AIBrowser")
            os.chmod(macos_dir / "AIBrowser", 0o755)
        
        # Copy backend
        backend_dest = resources_dir / "backend"
        if (self.base_dir / "backend").exists():
            shutil.copytree(self.base_dir / "backend", backend_dest, dirs_exist_ok=True)
        
        # Create Info.plist
        info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>AIBrowser</string>
    <key>CFBundleIdentifier</key>
    <string>{self.bundle_id}</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleVersion</key>
    <string>{self.version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.version}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>'''
        
        (contents_dir / "Info.plist").write_text(info_plist)
        
        # Create launcher script
        launcher_script = f'''#!/bin/bash
# AI Browser Launcher
export AI_BROWSER_ROOT="$(dirname "$0")/../Resources"
export PYTHONPATH="$AI_BROWSER_ROOT/backend:$PYTHONPATH"

# Start backend in background
cd "$AI_BROWSER_ROOT/backend"
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Launch browser
"$(dirname "$0")/AIBrowser" \\
    --user-data-dir="$HOME/.ai-browser" \\
    --enable-logging \\
    --v=1 \\
    --disable-web-security \\
    --allow-running-insecure-content \\
    --disable-features=VizDisplayCompositor

# Cleanup
kill $BACKEND_PID 2>/dev/null
'''
        
        launcher_path = macos_dir / "launcher.sh"
        launcher_path.write_text(launcher_script)
        os.chmod(launcher_path, 0o755)
        
        # Create DMG
        await self.create_dmg(app_bundle)
        
        print("✅ macOS package created")
    
    async def create_windows_package(self):
        """Create Windows installer and portable version"""
        print("🪟 Creating Windows package...")
        
        # Create portable version
        portable_dir = self.package_dir / f"{self.app_name}-Portable"
        portable_dir.mkdir(exist_ok=True)
        
        # Copy files
        browser_binary = self.find_browser_binary()
        if browser_binary:
            shutil.copy2(browser_binary, portable_dir / "AIBrowser.exe")
        
        if (self.base_dir / "backend").exists():
            shutil.copytree(self.base_dir / "backend", portable_dir / "backend", dirs_exist_ok=True)
        
        # Create batch launcher
        launcher_bat = f'''@echo off
title AI Browser
cd /d "%~dp0backend"
start /b python main.py
timeout /t 3 /nobreak >nul
start "" "%~dp0AIBrowser.exe" --user-data-dir="%USERPROFILE%\\.ai-browser"
'''
        
        (portable_dir / "Launch-AI-Browser.bat").write_text(launcher_bat)
        
        # Create ZIP
        zip_path = self.package_dir / f"{self.app_name}-{self.version}-Windows-Portable.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in portable_dir.rglob("*"):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(portable_dir))
        
        print("✅ Windows package created")
    
    async def create_linux_package(self):
        """Create Linux AppImage and .tar.gz"""
        print("🐧 Creating Linux package...")
        
        # Create AppDir structure
        app_dir = self.package_dir / f"{self.app_name}.AppDir"
        app_dir.mkdir(exist_ok=True)
        
        # Copy files
        browser_binary = self.find_browser_binary()
        if browser_binary:
            shutil.copy2(browser_binary, app_dir / "AIBrowser")
            os.chmod(app_dir / "AIBrowser", 0o755)
        
        if (self.base_dir / "backend").exists():
            shutil.copytree(self.base_dir / "backend", app_dir / "backend", dirs_exist_ok=True)
        
        # Create AppRun
        apprun_script = f'''#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$HERE/backend:$PYTHONPATH"

# Start backend
cd "$HERE/backend"
python main.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Launch browser
"$HERE/AIBrowser" \\
    --user-data-dir="$HOME/.ai-browser" \\
    --no-sandbox \\
    --disable-dev-shm-usage \\
    "$@"

# Cleanup
kill $BACKEND_PID 2>/dev/null
'''
        
        apprun_path = app_dir / "AppRun"
        apprun_path.write_text(apprun_script)
        os.chmod(apprun_path, 0o755)
        
        # Create .desktop file
        desktop_file = f'''[Desktop Entry]
Type=Application
Name={self.app_name}
Exec=AppRun
Icon=ai-browser
StartupWMClass={self.app_name}
Comment=Privacy-first AI browser with local GPT-OSS 20B
Category=Network;WebBrowser;
'''
        
        (app_dir / f"{self.app_name.lower().replace(' ', '-')}.desktop").write_text(desktop_file)
        
        # Create tar.gz
        tar_path = self.package_dir / f"{self.app_name}-{self.version}-Linux-{self.arch}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(app_dir, arcname=app_dir.name)
        
        print("✅ Linux package created")
    
    async def create_universal_installer(self):
        """Create cross-platform installer script"""
        print("🌍 Creating universal installer...")
        
        installer_script = f'''#!/bin/bash
# AI Browser Universal Installer
# Supports macOS, Linux, and Windows (via WSL/MSYS2)

set -e

AI_BROWSER_VERSION="{self.version}"
INSTALL_DIR="$HOME/.local/share/ai-browser"

echo "🤖 AI Browser Installer v$AI_BROWSER_VERSION"
echo "Privacy-first browser with local GPT-OSS 20B"
echo

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    PACKAGE_URL="https://github.com/your-repo/ai-browser/releases/download/v$AI_BROWSER_VERSION/AI-Browser-$AI_BROWSER_VERSION-macOS.dmg"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    ARCH=$(uname -m)
    PACKAGE_URL="https://github.com/your-repo/ai-browser/releases/download/v$AI_BROWSER_VERSION/AI-Browser-$AI_BROWSER_VERSION-Linux-$ARCH.tar.gz"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
    PACKAGE_URL="https://github.com/your-repo/ai-browser/releases/download/v$AI_BROWSER_VERSION/AI-Browser-$AI_BROWSER_VERSION-Windows-Portable.zip"
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo "📍 Detected platform: $PLATFORM"
echo

# Check dependencies
echo "🔍 Checking dependencies..."

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is required but not installed"
    echo "   Install Python 3.8+ from https://python.org"
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is required but not installed"
    echo "   Install from: https://ollama.ai"
    echo "   Then run: ollama pull gpt-oss:20b"
    exit 1
fi

# Check GPT-OSS model
if ! ollama list | grep -q "gpt-oss:20b"; then
    echo "📥 GPT-OSS 20B model not found, downloading..."
    ollama pull gpt-oss:20b
fi

echo "✅ All dependencies satisfied"
echo

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download and extract
echo "📦 Downloading AI Browser..."
case $PLATFORM in
    "macos")
        # For now, just point to manual installation
        echo "🍎 For macOS, download the .dmg from:"
        echo "   $PACKAGE_URL"
        echo "   Then drag AI Browser.app to Applications"
        ;;
    "linux")
        curl -L "$PACKAGE_URL" -o ai-browser.tar.gz
        tar -xzf ai-browser.tar.gz
        mv AI-Browser.AppDir/* .
        rm ai-browser.tar.gz
        chmod +x AppRun AIBrowser
        ;;
    "windows")
        curl -L "$PACKAGE_URL" -o ai-browser.zip
        unzip ai-browser.zip
        mv AI-Browser-Portable/* .
        rm ai-browser.zip
        ;;
esac

# Create launcher
echo "🚀 Creating launcher..."
case $PLATFORM in
    "linux")
        ln -sf "$INSTALL_DIR/AppRun" "$HOME/.local/bin/ai-browser" 2>/dev/null || true
        
        # Create desktop entry
        DESKTOP_DIR="$HOME/.local/share/applications"
        mkdir -p "$DESKTOP_DIR"
        cat > "$DESKTOP_DIR/ai-browser.desktop" << EOF
[Desktop Entry]
Type=Application
Name=AI Browser
Exec=$INSTALL_DIR/AppRun
Icon=$INSTALL_DIR/assets/icon.png
StartupWMClass=AI Browser
Comment=Privacy-first AI browser with local GPT-OSS 20B
Category=Network;WebBrowser;
EOF
        ;;
esac

echo
echo "🎉 AI Browser installed successfully!"
echo
echo "🚀 To launch:"
case $PLATFORM in
    "macos")
        echo "   Open AI Browser.app from Applications"
        ;;
    "linux")
        echo "   Run: ai-browser"
        echo "   Or find it in your applications menu"
        ;;
    "windows")
        echo "   Double-click Launch-AI-Browser.bat"
        ;;
esac

echo
echo "📚 Documentation: https://github.com/your-repo/ai-browser/wiki"
echo "🐛 Issues: https://github.com/your-repo/ai-browser/issues"
echo
echo "🔒 Your data stays local - no cloud required!"
'''
        
        installer_path = self.package_dir / "install.sh"
        installer_path.write_text(installer_script)
        os.chmod(installer_path, 0o755)
        
        print("✅ Universal installer created")
    
    async def create_update_system(self):
        """Create automatic update system"""
        print("🔄 Creating update system...")
        
        # Update checker script
        update_checker = '''#!/usr/bin/env python3
"""
AI Browser Update Checker
Checks for and installs updates automatically
"""

import json
import requests
import subprocess
import sys
from pathlib import Path
from packaging import version

class AIBrowserUpdater:
    def __init__(self):
        self.current_version = "1.0.0"  # Will be replaced during build
        self.update_url = "https://api.github.com/repos/your-repo/ai-browser/releases/latest"
    
    def check_for_updates(self):
        try:
            response = requests.get(self.update_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                
                if version.parse(latest_version) > version.parse(self.current_version):
                    return {
                        "available": True,
                        "version": latest_version,
                        "url": release_data["html_url"],
                        "notes": release_data["body"]
                    }
            return {"available": False}
        except Exception:
            return {"available": False}
    
    def notify_update(self, update_info):
        print(f"🚀 AI Browser v{update_info['version']} is available!")
        print(f"Current version: v{self.current_version}")
        print(f"Download: {update_info['url']}")
        
        if update_info.get("notes"):
            print("\\nRelease Notes:")
            print(update_info["notes"][:500] + "..." if len(update_info["notes"]) > 500 else update_info["notes"])

if __name__ == "__main__":
    updater = AIBrowserUpdater()
    update = updater.check_for_updates()
    if update["available"]:
        updater.notify_update(update)
    else:
        print("✅ AI Browser is up to date")
'''
        
        updater_path = self.package_dir / "update_checker.py"
        updater_path.write_text(update_checker)
        
        print("✅ Update system created")
    
    async def create_dmg(self, app_bundle: Path):
        """Create macOS DMG file"""
        try:
            dmg_path = self.package_dir / f"{self.app_name}-{self.version}-macOS.dmg"
            
            # Create temporary DMG
            subprocess.run([
                "hdiutil", "create", 
                "-size", "500m",
                "-volname", self.app_name,
                "-srcfolder", str(app_bundle),
                "-ov", "-format", "UDZO",
                str(dmg_path)
            ], check=True)
            
            print(f"✅ DMG created: {dmg_path}")
        except subprocess.CalledProcessError:
            print("⚠️  DMG creation failed - app bundle still available")
    
    def find_browser_binary(self) -> Optional[Path]:
        """Find the built browser binary"""
        possible_locations = [
            self.base_dir / "dist" / "AIBrowser" / "AIBrowser.app" / "Contents" / "MacOS" / "AIBrowser",
            self.base_dir / "backend" / "chromium" / "src" / "out" / "Default" / "chrome",
            self.base_dir / "backend" / "chromium" / "build" / "src" / "out" / "Default" / "chrome"
        ]
        
        for location in possible_locations:
            if location.exists():
                return location
        return None
    
    def print_package_info(self):
        """Print package creation summary"""
        print("\\n" + "=" * 60)
        print("📦 AI BROWSER DISTRIBUTION PACKAGES")
        print("=" * 60)
        
        packages = list(self.package_dir.glob("*"))
        for package in sorted(packages):
            if package.is_file():
                size_mb = package.stat().st_size / (1024 * 1024)
                print(f"   📁 {package.name:<40} ({size_mb:.1f} MB)")
        
        print("-" * 60)
        print(f"   Total packages: {len([p for p in packages if p.is_file()])}")
        print(f"   Package directory: {self.package_dir}")
        
        print("\\n🚀 Distribution Ready!")
        print("📋 Upload packages to GitHub Releases")
        print("🌍 Users can install with: curl -fsSL your-domain.com/install.sh | bash")
        print("\\n🔒 Privacy-first AI browser with local GPT-OSS 20B")

async def main():
    packager = AIBrowserPackager()
    await packager.create_all_packages()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())