#!/usr/bin/env python3
"""
Automated tests for critical fixes in AI Browser
Tests the components we fixed and verified:
1. browser_agent.py syntax fix
2. Backend API functionality
3. AI model integration
4. Dependency installation
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any
import requests

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_browser_agent_import():
    """Test that browser_agent.py can be imported without syntax errors"""
    print("🧪 Testing browser_agent.py import...")
    try:
        import browser_agent
        print("✅ browser_agent.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ browser_agent.py import failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print("🧪 Testing backend health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy - Model: {data.get('ai_model', 'unknown')}")
            print(f"   Tools registered: {data.get('tools', {}).get('total_registered', 0)}")
            print(f"   Agents working: {len([k for k, v in data.get('agents', {}).items() if v])}")
            return True
        else:
            print(f"❌ Backend health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {str(e)}")
        return False

def test_ai_chat():
    """Test AI chat functionality"""
    print("🧪 Testing AI chat functionality...")
    try:
        payload = {
            "message": "Hello! Please respond with exactly: 'Test successful'",
            "page_url": "http://test-page.local"
        }
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('response', '').lower()
            if 'test successful' in ai_response or 'hello' in ai_response:
                print(f"✅ AI chat working - Response: '{data.get('response', '')[:50]}...'")
                print(f"   Model: {data.get('metadata', {}).get('model', 'unknown')}")
                return True
            else:
                print(f"❌ AI chat unexpected response: {data.get('response', '')[:100]}")
                return False
        else:
            print(f"❌ AI chat failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI chat failed: {str(e)}")
        return False

def test_dependencies():
    """Test that critical dependencies are available"""
    print("🧪 Testing critical dependencies...")
    dependencies = {
        'numpy': 'import numpy',
        'PIL': 'from PIL import Image', 
        'sentence-transformers': 'import sentence_transformers',
        'faiss': 'import faiss',
        'pytesseract': 'import pytesseract'
    }
    
    results = {}
    for name, import_cmd in dependencies.items():
        try:
            exec(import_cmd)
            print(f"✅ {name} available")
            results[name] = True
        except ImportError as e:
            print(f"❌ {name} missing: {str(e)}")
            results[name] = False
        except Exception as e:
            print(f"❌ {name} error: {str(e)}")
            results[name] = False
    
    return all(results.values())

def test_ollama_connection():
    """Test Ollama connection and model availability"""
    print("🧪 Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            if 'gpt-oss:20b' in models:
                print("✅ Ollama connected - GPT-OSS 20B available")
                print(f"   Available models: {', '.join(models)}")
                return True
            else:
                print(f"❌ GPT-OSS 20B not found. Available: {', '.join(models)}")
                return False
        else:
            print(f"❌ Ollama not responding - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {str(e)}")
        return False

def test_extension_files():
    """Test that extension files exist and are valid"""
    print("🧪 Testing extension files...")
    extension_dir = Path(__file__).parent / "extension"
    required_files = [
        "manifest.json",
        "sidepanel.html", 
        "sidepanel.js",
        "background.js",
        "content.js",
        "icons/icon16.png",
        "icons/icon48.png",
        "icons/icon128.png"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = extension_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ All extension files present")
        
        # Test manifest.json validity
        try:
            manifest_path = extension_dir / "manifest.json"
            with open(manifest_path) as f:
                manifest = json.load(f)
            print(f"   Manifest version: {manifest.get('manifest_version')}")
            print(f"   Extension name: {manifest.get('name')}")
            return True
        except Exception as e:
            print(f"❌ Manifest.json invalid: {str(e)}")
            return False
    else:
        print(f"❌ Missing extension files: {', '.join(missing_files)}")
        return False

def test_performance():
    """Test performance of AI responses"""
    print("🧪 Testing AI response performance...")
    try:
        start_time = time.time()
        payload = {
            "message": "Quick test - just say OK",
            "page_url": "http://test-page.local"
        }
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=payload,
            timeout=15
        )
        end_time = time.time()
        
        if response.status_code == 200:
            response_time = end_time - start_time
            print(f"✅ AI response time: {response_time:.2f} seconds")
            
            if response_time < 5:
                print("   🚀 Excellent performance (< 5s)")
            elif response_time < 10:
                print("   ⚡ Good performance (< 10s)")
            else:
                print("   ⚠️  Slow performance (> 10s)")
            
            return True
        else:
            print(f"❌ Performance test failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🤖 AI Browser Critical Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        ("Browser Agent Import", test_browser_agent_import),
        ("Backend Health", test_backend_health), 
        ("AI Chat", test_ai_chat),
        ("Dependencies", test_dependencies),
        ("Ollama Connection", test_ollama_connection),
        ("Extension Files", test_extension_files),
        ("AI Performance", test_performance)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print()
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
    
    print()
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status:<10} {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All critical fixes working perfectly!")
        print("The AI Browser is ready for production use.")
    elif passed >= total * 0.8:
        print("✅ Most critical fixes working well!")
        print("Minor issues remain but core functionality is stable.")
    else:
        print("⚠️  Significant issues detected.")
        print("Review failed tests before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)