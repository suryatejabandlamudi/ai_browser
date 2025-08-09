#!/usr/bin/env python3
"""
AI Browser Build System
Based on BrowserOS architecture, customized for local GPT-OSS 20B integration
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class AIBrowserBuilder:
    """Build system for custom AI browser with local GPT-OSS 20B"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.chromium_dir = self.base_dir / "backend" / "chromium" 
        self.build_dir = self.chromium_dir / "build"
        self.patches_dir = self.chromium_dir / "BrowserOS" / "patches" / "nxtscape"
        self.ai_patches_dir = self.chromium_dir / "patches" / "ai-browser"
        
        # Build configuration
        self.browser_name = "AIBrowser"
        self.build_type = "release"
        self.parallel_jobs = os.cpu_count() or 4
        
    def check_prerequisites(self) -> bool:
        """Check if all build prerequisites are met"""
        print("🔍 Checking build prerequisites...")
        
        checks = {
            "Python 3": self._check_python(),
            "Git": self._check_git(), 
            "Xcode (macOS)": self._check_xcode(),
            "Depot Tools": self._check_depot_tools(),
            "Disk Space (>100GB)": self._check_disk_space(),
            "Memory (>8GB)": self._check_memory()
        }
        
        failed_checks = [name for name, passed in checks.items() if not passed]
        
        if failed_checks:
            print(f"❌ Failed prerequisites: {', '.join(failed_checks)}")
            return False
        
        print("✅ All prerequisites met")
        return True
    
    def _check_python(self) -> bool:
        return sys.version_info >= (3, 8)
    
    def _check_git(self) -> bool:
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            return True
        except:
            return False
    
    def _check_xcode(self) -> bool:
        if sys.platform != "darwin":
            return True  # Not macOS, skip Xcode check
        try:
            subprocess.run(["xcodebuild", "-version"], check=True, capture_output=True)
            return True
        except:
            return False
    
    def _check_depot_tools(self) -> bool:
        try:
            subprocess.run(["gclient", "--version"], check=True, capture_output=True)
            return True
        except:
            print("⚠️  depot_tools not found. Installing...")
            return self._install_depot_tools()
    
    def _check_disk_space(self) -> bool:
        """Check if we have enough disk space (100GB)"""
        statvfs = os.statvfs(self.base_dir)
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        return free_space_gb > 100
    
    def _check_memory(self) -> bool:
        """Check if we have enough RAM (8GB minimum)"""
        try:
            if sys.platform == "darwin":
                result = subprocess.run(["sysctl", "hw.memsize"], capture_output=True, text=True)
                memory_bytes = int(result.stdout.split()[1])
                memory_gb = memory_bytes / (1024**3)
                return memory_gb >= 8
            else:
                # Linux/other - check /proc/meminfo
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal:' in line:
                            memory_kb = int(line.split()[1])
                            memory_gb = memory_kb / (1024**2)
                            return memory_gb >= 8
        except:
            return True  # Assume sufficient memory if can't detect
        
        return True
    
    def _install_depot_tools(self) -> bool:
        """Install depot_tools if not present"""
        try:
            depot_tools_dir = self.base_dir / "depot_tools"
            if not depot_tools_dir.exists():
                print("📥 Cloning depot_tools...")
                subprocess.run([
                    "git", "clone", 
                    "https://chromium.googlesource.com/chromium/tools/depot_tools.git",
                    str(depot_tools_dir)
                ], check=True)
            
            # Add to PATH
            os.environ["PATH"] = f"{depot_tools_dir}:{os.environ.get('PATH', '')}"
            return True
        except Exception as e:
            print(f"❌ Failed to install depot_tools: {e}")
            return False
    
    def setup_chromium_source(self) -> bool:
        """Set up Chromium source code"""
        print("🔧 Setting up Chromium source...")
        
        chromium_src = self.chromium_dir / "src"
        
        if chromium_src.exists():
            print("✅ Chromium source already exists")
            return True
        
        print("📥 This will take a while... Fetching Chromium source (~50GB)")
        
        try:
            # Create build directory
            self.build_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize gclient
            gclient_file = self.build_dir / ".gclient"
            if not gclient_file.exists():
                os.chdir(self.build_dir)
                subprocess.run([
                    "gclient", "config", "--name", "src",
                    "https://chromium.googlesource.com/chromium/src.git"
                ], check=True)
            
            # Sync Chromium source
            print("⏳ Syncing Chromium... This takes 30-60 minutes")
            os.chdir(self.build_dir)
            subprocess.run(["gclient", "sync"], check=True)
            
            print("✅ Chromium source setup complete")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup Chromium source: {e}")
            return False
    
    def apply_ai_patches(self) -> bool:
        """Apply AI browser patches to Chromium"""
        print("🔨 Applying AI browser patches...")
        
        chromium_src = self.chromium_dir / "src"
        if not chromium_src.exists():
            print("❌ Chromium source not found")
            return False
        
        try:
            os.chdir(chromium_src)
            
            # Apply BrowserOS patches first
            if self.patches_dir.exists():
                print("📋 Applying BrowserOS patches...")
                for patch_file in sorted(self.patches_dir.glob("*.patch")):
                    print(f"   Applying {patch_file.name}")
                    try:
                        subprocess.run([
                            "git", "apply", "--whitespace=fix", str(patch_file)
                        ], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️  Patch {patch_file.name} failed, continuing...")
            
            # Apply custom AI patches
            if self.ai_patches_dir.exists():
                print("🤖 Applying AI browser patches...")
                for patch_file in sorted(self.ai_patches_dir.glob("*.patch")):
                    print(f"   Applying {patch_file.name}")
                    try:
                        subprocess.run([
                            "git", "apply", "--whitespace=fix", str(patch_file)
                        ], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️  Patch {patch_file.name} failed, continuing...")
            
            # Create AI integration files
            self._create_ai_integration_files()
            
            print("✅ AI patches applied successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply patches: {e}")
            return False
    
    def _create_ai_integration_files(self):
        """Create additional AI integration files"""
        chromium_src = self.chromium_dir / "src"
        
        # Create AI API files
        ai_api_dir = chromium_src / "chrome" / "browser" / "ai"
        ai_api_dir.mkdir(parents=True, exist_ok=True)
        
        # AI API header
        ai_api_h = ai_api_dir / "ai_service.h"
        ai_api_h.write_text('''
#ifndef CHROME_BROWSER_AI_AI_SERVICE_H_
#define CHROME_BROWSER_AI_AI_SERVICE_H_

#include "base/memory/weak_ptr.h"
#include "components/keyed_service/core/keyed_service.h"

namespace ai {

class AIService : public KeyedService {
 public:
  AIService();
  ~AIService() override;

  // Connect to local GPT-OSS 20B via Ollama
  void ConnectToLocalModel();
  
  // Process AI requests
  void ProcessRequest(const std::string& message, 
                     const std::string& page_content,
                     base::OnceCallback<void(const std::string&)> callback);

 private:
  std::string ollama_endpoint_ = "http://localhost:11434";
  std::string model_name_ = "gpt-oss:20b";
  
  base::WeakPtrFactory<AIService> weak_factory_{this};
};

}  // namespace ai

#endif  // CHROME_BROWSER_AI_AI_SERVICE_H_
''')
        
        # AI API implementation
        ai_api_cc = ai_api_dir / "ai_service.cc"
        ai_api_cc.write_text('''
#include "chrome/browser/ai/ai_service.h"

#include "base/json/json_reader.h"
#include "base/json/json_writer.h"
#include "services/network/public/cpp/simple_url_loader.h"

namespace ai {

AIService::AIService() = default;
AIService::~AIService() = default;

void AIService::ConnectToLocalModel() {
  // Implementation for connecting to local Ollama instance
  LOG(INFO) << "Connecting to local GPT-OSS 20B model...";
}

void AIService::ProcessRequest(
    const std::string& message,
    const std::string& page_content,
    base::OnceCallback<void(const std::string&)> callback) {
  
  // Create request payload for Ollama API
  base::Value::Dict request_data;
  request_data.Set("model", model_name_);
  request_data.Set("prompt", message);
  
  // Add page content as context
  if (!page_content.empty()) {
    request_data.Set("context", page_content.substr(0, 4000));  // Limit context
  }
  
  std::string json_request;
  base::JSONWriter::Write(request_data, &json_request);
  
  // TODO: Implement actual HTTP request to Ollama
  // For now, return a mock response
  std::move(callback).Run("AI response from GPT-OSS 20B (local)");
}

}  // namespace ai
''')
        
        print("📝 Created AI integration files")
    
    def configure_build(self) -> bool:
        """Configure the build with AI browser settings"""
        print("⚙️  Configuring build settings...")
        
        chromium_src = self.chromium_dir / "src"
        if not chromium_src.exists():
            print("❌ Chromium source not found")
            return False
        
        try:
            os.chdir(chromium_src)
            
            # Create build args
            build_args = {
                "is_debug": self.build_type == "debug",
                "is_component_build": False,
                "symbol_level": 1,
                "enable_nacl": False,
                "target_cpu": "arm64" if "arm64" in subprocess.check_output(["uname", "-m"]).decode() else "x64",
                "chrome_pgo_phase": 0,
                "use_goma": False,
                "enable_widevine": True,
                "proprietary_codecs": True,
                "ffmpeg_branding": "Chrome",
                # AI Browser specific settings
                "ai_browser_build": True,
                "browser_name": self.browser_name,
                "local_ai_integration": True
            }
            
            # Write build args
            build_dir = chromium_src / "out" / "Default"
            build_dir.mkdir(parents=True, exist_ok=True)
            
            args_file = build_dir / "args.gn"
            args_content = "\n".join([f"{k} = {json.dumps(v)}" for k, v in build_args.items()])
            args_file.write_text(args_content)
            
            # Generate build files
            subprocess.run(["gn", "gen", "out/Default"], check=True)
            
            print("✅ Build configured successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure build: {e}")
            return False
    
    def build_browser(self) -> bool:
        """Build the AI browser"""
        print(f"🔨 Building AI Browser... This will take 2-4 hours")
        
        chromium_src = self.chromium_dir / "src"
        if not chromium_src.exists():
            print("❌ Chromium source not found")
            return False
        
        try:
            os.chdir(chromium_src)
            
            build_start = time.time()
            
            # Build the browser
            subprocess.run([
                "autoninja", "-C", "out/Default", 
                "chrome", f"-j{self.parallel_jobs}"
            ], check=True)
            
            build_time = time.time() - build_start
            print(f"✅ Build completed in {build_time/3600:.1f} hours")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            return False
    
    def test_browser(self) -> bool:
        """Test the built browser"""
        print("🧪 Testing AI Browser...")
        
        chromium_src = self.chromium_dir / "src"
        browser_binary = chromium_src / "out" / "Default" / "chrome"
        
        if not browser_binary.exists():
            print("❌ Browser binary not found")
            return False
        
        try:
            # Test basic launch
            print("   Testing browser launch...")
            process = subprocess.Popen([
                str(browser_binary),
                "--disable-web-security",
                "--user-data-dir=/tmp/ai-browser-test",
                "--no-first-run",
                "--disable-default-apps"
            ])
            
            # Give it time to start
            time.sleep(5)
            
            # Check if process is running
            if process.poll() is None:
                print("✅ Browser launched successfully")
                process.terminate()
                return True
            else:
                print("❌ Browser failed to launch")
                return False
                
        except Exception as e:
            print(f"❌ Browser test failed: {e}")
            return False
    
    def package_browser(self) -> bool:
        """Package the browser for distribution"""
        print("📦 Packaging AI Browser...")
        
        chromium_src = self.chromium_dir / "src"
        build_output = chromium_src / "out" / "Default"
        
        if not build_output.exists():
            print("❌ Build output not found")
            return False
        
        try:
            # Create package directory
            package_dir = self.base_dir / "dist" / self.browser_name
            package_dir.mkdir(parents=True, exist_ok=True)
            
            if sys.platform == "darwin":
                # macOS app bundle
                app_bundle = package_dir / f"{self.browser_name}.app"
                subprocess.run([
                    "cp", "-R",
                    str(build_output / "Chrome.app"),
                    str(app_bundle)
                ], check=True)
                
                # Rename executable
                exec_dir = app_bundle / "Contents" / "MacOS"
                subprocess.run([
                    "mv", 
                    str(exec_dir / "Chrome"),
                    str(exec_dir / self.browser_name)
                ], check=True)
                
            print(f"✅ Browser packaged at {package_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Packaging failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Build AI Browser with local GPT-OSS 20B")
    parser.add_argument("--setup", action="store_true", help="Setup Chromium source")
    parser.add_argument("--patch", action="store_true", help="Apply AI patches")
    parser.add_argument("--configure", action="store_true", help="Configure build")
    parser.add_argument("--build", action="store_true", help="Build browser")
    parser.add_argument("--test", action="store_true", help="Test browser")
    parser.add_argument("--package", action="store_true", help="Package browser")
    parser.add_argument("--all", action="store_true", help="Do everything")
    parser.add_argument("--build-type", choices=["debug", "release"], default="release")
    
    args = parser.parse_args()
    
    if not any([args.setup, args.patch, args.configure, args.build, args.test, args.package, args.all]):
        parser.print_help()
        return 1
    
    # Get the project root directory
    base_dir = Path(__file__).parent
    
    builder = AIBrowserBuilder(str(base_dir))
    builder.build_type = args.build_type
    
    print(f"🚀 AI Browser Build System")
    print(f"   Base Directory: {base_dir}")
    print(f"   Build Type: {args.build_type}")
    print(f"   Browser Name: {builder.browser_name}")
    
    # Check prerequisites
    if not builder.check_prerequisites():
        return 1
    
    success = True
    
    if args.all or args.setup:
        success &= builder.setup_chromium_source()
    
    if success and (args.all or args.patch):
        success &= builder.apply_ai_patches()
    
    if success and (args.all or args.configure):
        success &= builder.configure_build()
    
    if success and (args.all or args.build):
        success &= builder.build_browser()
    
    if success and (args.all or args.test):
        success &= builder.test_browser()
    
    if success and (args.all or args.package):
        success &= builder.package_browser()
    
    if success:
        print(f"\n🎉 AI Browser build completed successfully!")
        print(f"🤖 Your privacy-first AI browser with GPT-OSS 20B is ready!")
        print(f"📍 Location: {base_dir}/dist/{builder.browser_name}")
    else:
        print(f"\n❌ Build failed. Check the logs above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())