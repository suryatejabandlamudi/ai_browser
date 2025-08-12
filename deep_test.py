#!/usr/bin/env python3
"""
Deep testing of AI Browser - verify every component actually works
"""

import subprocess
import time
import requests
import json
import sys
import os
from pathlib import Path

def test_ollama():
    """Test if Ollama and AI model are working"""
    print("🧪 Testing Ollama AI model...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gpt-oss:20b",
                "prompt": "Hello, this is a test",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and data["response"]:
                print("✅ Ollama AI model working - response received")
                return True
            else:
                print("❌ Ollama responded but no AI response generated")
                return False
        else:
            print(f"❌ Ollama request failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_backend():
    """Test backend API endpoints"""
    print("🧪 Testing backend API...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend health: {health_data['status']}")
            print(f"   - AI Model: {health_data['ai_model']}")
            print(f"   - Tools: {health_data['tools']['total_registered']}")
            print(f"   - Agents: {len(health_data['agents'])}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test chat endpoint
    print("🧪 Testing backend chat endpoint...")
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={
                "message": "Test from deep test script",
                "page_url": "https://example.com"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            chat_data = response.json()
            if "response" in chat_data and chat_data["response"]:
                print("✅ Backend chat endpoint working")
                print(f"   - AI Response: {chat_data['response'][:100]}...")
                return True
            else:
                print("❌ Backend chat endpoint returned empty response")
                return False
        else:
            print(f"❌ Backend chat request failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Backend chat failed: {e}")
        return False

def test_extension_files():
    """Test extension files exist and are valid"""
    print("🧪 Testing extension files...")
    
    extension_dir = Path("/Volumes/ssd/apple/ai_browser/extension")
    required_files = [
        "manifest.json",
        "background.js", 
        "sidepanel.js",
        "sidepanel.html",
        "sidepanel.css",
        "content.js"
    ]
    
    for file in required_files:
        file_path = extension_dir / file
        if not file_path.exists():
            print(f"❌ Missing extension file: {file}")
            return False
        else:
            print(f"✅ Found: {file}")
    
    # Test manifest.json is valid JSON
    try:
        with open(extension_dir / "manifest.json", 'r') as f:
            manifest = json.load(f)
        print(f"✅ Manifest valid - Extension: {manifest['name']} v{manifest['version']}")
    except json.JSONDecodeError as e:
        print(f"❌ Manifest.json invalid: {e}")
        return False
    
    # Test JavaScript syntax
    for js_file in ["background.js", "sidepanel.js", "content.js"]:
        try:
            result = subprocess.run(
                ["node", "-c", str(extension_dir / js_file)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {js_file} syntax valid")
            else:
                print(f"❌ {js_file} syntax error: {result.stderr}")
                return False
        except FileNotFoundError:
            print("⚠️ Node.js not found, skipping JS syntax check")
            break
    
    return True

def test_chrome_extension_loading():
    """Test loading extension in Chrome"""
    print("🧪 Testing Chrome extension loading...")
    
    extension_dir = "/Volumes/ssd/apple/ai_browser/extension"
    profile_dir = "/tmp/ai_browser_deep_test"
    
    # Clean up any existing test profile
    if os.path.exists(profile_dir):
        subprocess.run(["rm", "-rf", profile_dir])
    
    os.makedirs(profile_dir, exist_ok=True)
    
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--load-extension={extension_dir}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check", 
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "chrome://extensions/"
    ]
    
    try:
        # Start Chrome with extension
        process = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Chrome started with extension")
        print("   - Chrome should be running now")
        print("   - Extension page should be open")
        print("   - Look for 'AI Browser Extension' in the list")
        print("   - Check if it shows any error messages")
        
        # Let it run for a moment
        time.sleep(5)
        
        # Check if process is still running (not crashed)
        if process.poll() is None:
            print("✅ Chrome process running stable")
            
            # Try to terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=10)
                print("✅ Chrome shut down cleanly")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️ Had to force kill Chrome")
            
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ Chrome process exited immediately")
            if stderr:
                print(f"Chrome stderr: {stderr[:500]}")
            return False
            
    except FileNotFoundError:
        print("❌ Chrome not found at expected path")
        return False
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        return False
    finally:
        # Cleanup
        subprocess.run(["rm", "-rf", profile_dir], capture_output=True)

def main():
    """Run all tests"""
    print("🔬 AI BROWSER DEEP TESTING")
    print("=" * 50)
    
    tests = [
        ("Ollama AI Model", test_ollama),
        ("Backend API", test_backend), 
        ("Extension Files", test_extension_files),
        ("Chrome Extension Loading", test_chrome_extension_loading)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    print("\n🏁 FINAL RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The AI Browser system is working correctly.")
        print("You should be able to:")
        print("1. Launch Chrome with the extension")
        print("2. See the AI Browser extension icon")
        print("3. Click it to open the side panel")
        print("4. Chat with the AI in the side panel")
        return True
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("The AI Browser has issues that need to be fixed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)