#!/usr/bin/env python3
"""
AI Browser Packaging Script
Creates a professional, installable browser package like Perplexity Comet
"""

import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path

class AIBrowserPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.chromium_src = self.project_root / "backend" / "chromium" / "src"
        self.build_dir = self.chromium_src / "out" / "AIBrowser"
        self.package_dir = self.project_root / "dist"
        
    def check_build_complete(self):
        """Check if the Chromium build has completed"""
        chrome_binary = self.build_dir / "chrome"
        if chrome_binary.exists():
            print("✅ Chrome binary found!")
            return True
            
        # Check if build is still running
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'ninja' in result.stdout:
                print("🏗️  Build still in progress...")
                return False
        except:
            pass
            
        print("❌ Chrome binary not found. Build may have failed.")
        return False
    
    def wait_for_build(self, timeout_hours=4):
        """Wait for build to complete"""
        print("⏳ Waiting for Chromium build to complete...")
        start_time = time.time()
        timeout_seconds = timeout_hours * 3600
        
        while time.time() - start_time < timeout_seconds:
            if self.check_build_complete():
                return True
            time.sleep(60)  # Check every minute
            
        print(f"⏰ Build timeout after {timeout_hours} hours")
        return False
    
    def create_app_bundle(self):
        """Create macOS .app bundle"""
        print("📦 Creating AI Browser.app bundle...")
        
        app_name = "AI Browser.app"
        app_bundle = self.package_dir / app_name
        
        # Remove existing bundle
        if app_bundle.exists():
            shutil.rmtree(app_bundle)
        
        # Create app bundle structure
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        frameworks_dir = contents_dir / "Frameworks"
        
        for directory in [macos_dir, resources_dir, frameworks_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Copy Chrome binary
        chrome_binary = self.build_dir / "chrome"
        app_binary = macos_dir / "AI Browser"
        shutil.copy2(chrome_binary, app_binary)
        
        # Make executable
        os.chmod(app_binary, 0o755)
        
        # Copy frameworks and libraries
        self.copy_dependencies(frameworks_dir)
        
        # Create Info.plist
        self.create_info_plist(contents_dir)
        
        # Copy resources
        self.copy_resources(resources_dir)
        
        print(f"✅ Created {app_name}")
        return app_bundle
    
    def copy_dependencies(self, frameworks_dir):
        """Copy required dylibs and frameworks"""
        print("📚 Copying dependencies...")
        
        # Copy all .dylib files
        for dylib in self.build_dir.glob("*.dylib"):
            shutil.copy2(dylib, frameworks_dir)
        
        # Copy Chromium Framework if it exists
        framework_src = self.build_dir / "Chromium Framework.framework"
        if framework_src.exists():
            framework_dst = frameworks_dir / "Chromium Framework.framework"
            shutil.copytree(framework_src, framework_dst, dirs_exist_ok=True)
    
    def create_info_plist(self, contents_dir):
        """Create Info.plist for the app bundle"""
        info_plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>AI Browser</string>
    <key>CFBundleExecutable</key>
    <string>AI Browser</string>
    <key>CFBundleIdentifier</key>
    <string>com.aibrowser.browser</string>
    <key>CFBundleName</key>
    <string>AI Browser</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>Web site URL</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>http</string>
                <string>https</string>
            </array>
        </dict>
    </array>
</dict>
</plist>'''
        
        plist_file = contents_dir / "Info.plist"
        plist_file.write_text(info_plist_content)
        print("✅ Created Info.plist")
    
    def copy_resources(self, resources_dir):
        """Copy application resources"""
        # Copy icudtl.dat (required for internationalization)
        icudtl = self.build_dir / "icudtl.dat"
        if icudtl.exists():
            shutil.copy2(icudtl, resources_dir)
        
        # Copy other resources
        for resource in ['pak', 'pem']:
            for file in self.build_dir.glob(f"*.{resource}"):
                shutil.copy2(file, resources_dir)
        
        # Copy locale files
        locales_src = self.build_dir / "locales"
        if locales_src.exists():
            locales_dst = resources_dir / "locales"
            shutil.copytree(locales_src, locales_dst, dirs_exist_ok=True)
    
    def create_dmg(self, app_bundle):
        """Create installable DMG"""
        print("💿 Creating DMG installer...")
        
        dmg_name = "AI-Browser-Installer.dmg"
        dmg_path = self.package_dir / dmg_name
        
        # Remove existing DMG
        if dmg_path.exists():
            dmg_path.unlink()
        
        # Create temporary directory for DMG contents
        dmg_temp = self.package_dir / "dmg_temp"
        if dmg_temp.exists():
            shutil.rmtree(dmg_temp)
        dmg_temp.mkdir()
        
        # Copy app bundle to temp directory
        shutil.copytree(app_bundle, dmg_temp / app_bundle.name)
        
        # Create symlink to Applications
        applications_link = dmg_temp / "Applications"
        os.symlink("/Applications", applications_link)
        
        # Create DMG
        subprocess.run([
            'hdiutil', 'create',
            '-volname', 'AI Browser',
            '-srcfolder', str(dmg_temp),
            '-ov', '-format', 'UDZO',
            str(dmg_path)
        ])
        
        # Clean up temp directory
        shutil.rmtree(dmg_temp)
        
        if dmg_path.exists():
            print(f"✅ Created {dmg_name}")
            print(f"📍 DMG Location: {dmg_path}")
            return dmg_path
        else:
            print("❌ Failed to create DMG")
            return None
    
    def create_startup_script(self):
        """Create startup script that ensures AI backend is running"""
        startup_script = self.package_dir / "start-ai-browser.sh"
        
        script_content = f'''#!/bin/bash
# AI Browser Startup Script
# Ensures AI backend is running before launching browser

echo "🚀 Starting AI Browser..."

# Check if AI backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "🔄 Starting AI backend..."
    cd "{self.project_root}/backend"
    python main.py &
    
    # Wait for backend to be ready
    echo "⏳ Waiting for AI backend to initialize..."
    for i in {{1..30}}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ AI backend ready!"
            break
        fi
        sleep 1
    done
fi

# Launch AI Browser
echo "🌐 Launching AI Browser..."
open "{self.package_dir}/AI Browser.app"
'''
        
        startup_script.write_text(script_content)
        os.chmod(startup_script, 0o755)
        print(f"✅ Created startup script: {startup_script}")
    
    def package(self):
        """Main packaging function"""
        print("🎯 AI Browser Packaging Started")
        print("=" * 50)
        
        # Ensure package directory exists
        self.package_dir.mkdir(exist_ok=True)
        
        # Wait for build if not complete
        if not self.check_build_complete():
            if not self.wait_for_build():
                print("❌ Build not complete, cannot package")
                return False
        
        # Create app bundle
        app_bundle = self.create_app_bundle()
        
        # Create DMG installer
        dmg_path = self.create_dmg(app_bundle)
        
        # Create startup script
        self.create_startup_script()
        
        print("\n" + "=" * 50)
        print("🎉 AI Browser Packaging Complete!")
        print(f"📱 App Bundle: {app_bundle}")
        if dmg_path:
            print(f"💿 DMG Installer: {dmg_path}")
        print(f"📁 Package Directory: {self.package_dir}")
        
        print("\n📋 Next Steps:")
        print("1. Ensure AI backend is running: cd backend && python main.py")
        print("2. Install from DMG or run: open 'dist/AI Browser.app'")
        print("3. Test AI features in the browser")
        
        return True

def main():
    packager = AIBrowserPackager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        # Force wait for build
        if not packager.wait_for_build():
            sys.exit(1)
    
    success = packager.package()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()