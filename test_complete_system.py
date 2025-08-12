#!/usr/bin/env python3
"""
Complete AI Browser System Test
Tests the full integration of custom browser + AI backend + extension
"""

import requests
import time
import json
import sys

def test_ollama_connection():
    """Test if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            gpt_oss_available = any('gpt-oss' in model.get('name', '') for model in models)
            print(f"✅ Ollama running with {len(models)} models")
            print(f"✅ GPT-OSS 20B available: {gpt_oss_available}")
            return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy - AI Model: {data.get('ai_model')}")
            print(f"✅ Tools registered: {data.get('tools', {}).get('total_registered', 0)}")
            print(f"✅ Agents available: {len(data.get('agents', {}))}")
            return True
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_ai_chat():
    """Test AI chat functionality"""
    try:
        payload = {
            "message": "Say hello and tell me you're ready for browser automation",
            "page_url": "https://example.com"
        }
        
        print("🔄 Testing AI chat (this may take 10-15 seconds)...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=payload,
            timeout=30
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI responded in {response_time:.1f}s")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Model: {data.get('metadata', {}).get('model')}")
            return True
        else:
            print(f"❌ AI chat failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI chat test failed: {e}")
        return False

def test_browser_processes():
    """Check if browser processes are running"""
    import subprocess
    try:
        # Check for custom Chromium
        result = subprocess.run(['pgrep', '-f', 'Chromium.app'], 
                              capture_output=True, text=True)
        chromium_running = len(result.stdout.strip().split('\n')) > 0 if result.stdout.strip() else False
        
        # Check for Chrome with extension
        result = subprocess.run(['pgrep', '-f', 'load-extension'], 
                              capture_output=True, text=True)
        chrome_extension_running = len(result.stdout.strip().split('\n')) > 0 if result.stdout.strip() else False
        
        print(f"✅ Custom Chromium running: {chromium_running}")
        print(f"✅ Chrome with AI extension: {chrome_extension_running}")
        
        return chromium_running or chrome_extension_running
        
    except Exception as e:
        print(f"❌ Browser process check failed: {e}")
        return False

def main():
    """Run complete system test"""
    print("🚀 AI BROWSER COMPLETE SYSTEM TEST")
    print("=" * 50)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Backend Health", test_backend_health),
        ("AI Chat", test_ai_chat),
        ("Browser Processes", test_browser_processes),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS:")
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 SUCCESS! Your AI Browser system is fully operational!")
        print("\nNext steps:")
        print("1. Open your custom Chromium browser")
        print("2. Load the Chrome extension in any Chrome browser") 
        print("3. Use Cmd+E to open the AI sidepanel")
        print("4. Test real-world automation tasks")
    else:
        print("\n⚠️  Some components need attention before full deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)