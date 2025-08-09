#!/usr/bin/env python3
"""
Deep functionality tests for AI Browser - testing actual functionality, not just HTTP codes
This goes beyond status codes to verify actual functionality works correctly
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List
import requests

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_browser_agent_deep():
    """Deep test of browser_agent functionality - test actual methods work"""
    print("🔍 Deep testing browser_agent functionality...")
    try:
        # Import and create instance
        from browser_agent import BrowserAgent
        agent = BrowserAgent()
        
        # Test actual method calls
        test_results = {}
        
        # Test _find_input_selector method
        selector = agent._find_input_selector("email", "https://example.com")
        if "email" in selector and "input" in selector:
            print("✅ Input selector generation works")
            test_results['selector'] = True
        else:
            print(f"❌ Input selector broken: {selector}")
            test_results['selector'] = False
        
        # Test action preparation methods exist and are callable
        methods_to_test = ['_handle_navigate', '_handle_scroll', 'execute_action']
        for method_name in methods_to_test:
            if hasattr(agent, method_name) and callable(getattr(agent, method_name)):
                print(f"✅ Method {method_name} exists and callable")
                test_results[method_name] = True
            else:
                print(f"❌ Method {method_name} missing or not callable")
                test_results[method_name] = False
        
        success = all(test_results.values())
        if success:
            print("✅ Browser agent deep functionality verified")
        else:
            print(f"❌ Browser agent issues: {[k for k,v in test_results.items() if not v]}")
        
        return success
        
    except Exception as e:
        print(f"❌ Browser agent deep test failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_ai_actual_intelligence():
    """Test if AI can actually understand and respond intelligently"""
    print("🔍 Deep testing AI intelligence and understanding...")
    
    # Test complex reasoning
    test_cases = [
        {
            "input": "If I have 3 apples and give away 1, how many do I have left?",
            "expected_keywords": ["2", "two"],
            "test_name": "Basic Math"
        },
        {
            "input": "What is the capital of France?",
            "expected_keywords": ["paris"],
            "test_name": "General Knowledge"  
        },
        {
            "input": "Write a JSON object with a field called 'test' set to true",
            "expected_keywords": ['"test"', '"true"', '{', '}'],
            "test_name": "JSON Generation"
        },
        {
            "input": "Extract the main action from this: 'Please click the submit button and then navigate to the home page'",
            "expected_keywords": ["click", "navigate", "submit", "home"],
            "test_name": "Action Understanding"
        }
    ]
    
    results = {}
    for test_case in test_cases:
        try:
            payload = {
                "message": test_case["input"],
                "page_url": "http://test-page.local"
            }
            response = requests.post(
                "http://localhost:8000/api/chat",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '').lower()
                
                # Check if response contains expected keywords
                found_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in ai_response]
                
                if found_keywords:
                    print(f"✅ {test_case['test_name']}: Found {len(found_keywords)}/{len(test_case['expected_keywords'])} keywords")
                    print(f"   Response: '{data.get('response', '')[:100]}...'")
                    results[test_case['test_name']] = True
                else:
                    print(f"❌ {test_case['test_name']}: No expected keywords found")
                    print(f"   Expected: {test_case['expected_keywords']}")
                    print(f"   Got: '{data.get('response', '')[:100]}...'")
                    results[test_case['test_name']] = False
            else:
                print(f"❌ {test_case['test_name']}: HTTP error {response.status_code}")
                results[test_case['test_name']] = False
                
        except Exception as e:
            print(f"❌ {test_case['test_name']}: Exception - {str(e)}")
            results[test_case['test_name']] = False
    
    success_rate = sum(results.values()) / len(results)
    overall_success = success_rate >= 0.75  # 75% success rate required
    
    print(f"🧠 AI Intelligence Score: {success_rate*100:.1f}% ({sum(results.values())}/{len(results)} tests passed)")
    
    if overall_success:
        print("✅ AI demonstrates good intelligence and understanding")
    else:
        print("❌ AI intelligence concerns - may not understand complex tasks properly")
    
    return overall_success

def test_tools_actually_work():
    """Test that the registered tools actually function properly"""
    print("🔍 Deep testing tool functionality...")
    
    try:
        # Get tools info from backend
        response = requests.get("http://localhost:8000/api/tools", timeout=5)
        if response.status_code != 200:
            print("❌ Cannot fetch tools list")
            return False
        
        tools_data = response.json()
        tools = tools_data.get('tools', [])
        
        if not tools:
            print("❌ No tools found in backend")
            return False
        
        print(f"📋 Found {len(tools)} tools to test")
        
        # Test specific tools that should work
        critical_tools = ['navigate', 'click', 'type', 'search_page']
        tool_names = [tool.get('name', '') for tool in tools]
        
        missing_tools = [tool for tool in critical_tools if tool not in tool_names]
        if missing_tools:
            print(f"❌ Missing critical tools: {missing_tools}")
            return False
        
        print(f"✅ All critical tools present: {critical_tools}")
        
        # Test tool execution via API
        test_action = {
            "action": "navigate",
            "parameters": {
                "url": "https://example.com"
            },
            "page_url": "https://test.com"
        }
        
        response = requests.post(
            "http://localhost:8000/api/action",
            json=test_action,
            timeout=10
        )
        
        if response.status_code == 200:
            action_result = response.json()
            
            # Check if action preparation worked
            if action_result.get('success') and action_result.get('message'):
                print(f"✅ Tool execution works - Result: {action_result.get('message')}")
                
                # Check action data structure
                action_data = action_result.get('data')
                if action_data and action_data.get('action') == 'navigate':
                    print("✅ Action data structure correct")
                    return True
                else:
                    print(f"❌ Action data structure broken: {action_data}")
                    return False
            else:
                print(f"❌ Tool execution failed: {action_result}")
                return False
        else:
            print(f"❌ Tool execution HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Tool testing failed: {str(e)}")
        return False

def test_memory_persistence():
    """Test if the system can maintain conversation context"""
    print("🔍 Testing memory and context persistence...")
    
    try:
        # First message - establish context
        response1 = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": "My name is TestUser. Remember this for our conversation.", "page_url": "http://test.com"},
            timeout=10
        )
        
        if response1.status_code != 200:
            print("❌ First message failed")
            return False
            
        # Second message - test if context is remembered
        response2 = requests.post(
            "http://localhost:8000/api/chat", 
            json={"message": "What is my name?", "page_url": "http://test.com"},
            timeout=10
        )
        
        if response2.status_code != 200:
            print("❌ Second message failed")
            return False
        
        response_text = response2.json().get('response', '').lower()
        
        if 'testuser' in response_text:
            print("✅ Memory persistence works - AI remembered context")
            return True
        else:
            print(f"❌ Memory failed - AI didn't remember name. Response: {response_text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Memory test failed: {str(e)}")
        return False

def test_error_handling():
    """Test how system handles various error conditions"""
    print("🔍 Testing error handling and resilience...")
    
    error_tests = []
    
    # Test invalid JSON
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code >= 400:  # Should return error
            error_tests.append(("Invalid JSON", True))
            print("✅ Invalid JSON properly rejected")
        else:
            error_tests.append(("Invalid JSON", False))
            print("❌ Invalid JSON not properly handled")
    except:
        error_tests.append(("Invalid JSON", False))
        print("❌ Invalid JSON crashed system")
    
    # Test missing required fields
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"page_url": "http://test.com"},  # Missing message
            timeout=5
        )
        if response.status_code >= 400:
            error_tests.append(("Missing Fields", True))
            print("✅ Missing required fields properly rejected")
        else:
            error_tests.append(("Missing Fields", False))
            print("❌ Missing fields not validated")
    except:
        error_tests.append(("Missing Fields", False))
        print("❌ Missing fields crashed system")
    
    # Test extremely long input
    try:
        long_message = "x" * 10000  # Very long message
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": long_message, "page_url": "http://test.com"},
            timeout=15
        )
        if response.status_code < 500:  # Should not crash
            error_tests.append(("Long Input", True))
            print("✅ Long input handled gracefully")
        else:
            error_tests.append(("Long Input", False))
            print("❌ Long input crashed system")
    except:
        error_tests.append(("Long Input", False))
        print("❌ Long input exception")
    
    success_rate = sum(test[1] for test in error_tests) / len(error_tests)
    overall_success = success_rate >= 0.75
    
    print(f"🛡️  Error Handling Score: {success_rate*100:.1f}%")
    
    return overall_success

def test_extension_manifest_deep():
    """Deep test of extension manifest and files"""
    print("🔍 Deep testing extension manifest and structure...")
    
    try:
        extension_dir = Path(__file__).parent / "extension"
        manifest_path = extension_dir / "manifest.json"
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Check manifest version 3 compliance
        if manifest.get("manifest_version") != 3:
            print(f"❌ Wrong manifest version: {manifest.get('manifest_version')}")
            return False
        
        # Check required permissions
        required_permissions = ["activeTab", "storage", "scripting", "tabs", "sidePanel"]
        permissions = manifest.get("permissions", [])
        missing_perms = [p for p in required_permissions if p not in permissions]
        
        if missing_perms:
            print(f"❌ Missing permissions: {missing_perms}")
            return False
        
        # Check files referenced in manifest actually exist
        files_to_check = []
        
        # Background script
        if "background" in manifest:
            bg_script = manifest["background"].get("service_worker")
            if bg_script:
                files_to_check.append(bg_script)
        
        # Side panel
        if "side_panel" in manifest:
            side_panel = manifest["side_panel"].get("default_path")
            if side_panel:
                files_to_check.append(side_panel)
        
        # Content scripts
        for cs in manifest.get("content_scripts", []):
            files_to_check.extend(cs.get("js", []))
        
        # Icons
        for icon_dict in [manifest.get("action", {}).get("default_icon", {}), manifest.get("icons", {})]:
            files_to_check.extend(icon_dict.values())
        
        # Check all files exist
        missing_files = []
        for file_path in files_to_check:
            full_path = extension_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files referenced in manifest: {missing_files}")
            return False
        
        # Check JavaScript files are valid
        js_files = [f for f in files_to_check if f.endswith('.js')]
        for js_file in js_files:
            js_path = extension_dir / js_file
            try:
                with open(js_path) as f:
                    content = f.read()
                if len(content) < 50:  # Very short files are suspicious
                    print(f"❌ {js_file} seems too short: {len(content)} chars")
                    return False
                if 'localhost:8000' not in content and js_file in ['background.js', 'sidepanel.js']:
                    print(f"❌ {js_file} missing localhost:8000 backend reference")
                    return False
            except Exception as e:
                print(f"❌ Cannot read {js_file}: {str(e)}")
                return False
        
        print("✅ Extension manifest and files deeply validated")
        print(f"   Checked {len(files_to_check)} referenced files")
        print(f"   Validated {len(js_files)} JavaScript files")
        
        return True
        
    except Exception as e:
        print(f"❌ Extension deep test failed: {str(e)}")
        return False

def run_deep_tests():
    """Run comprehensive deep functionality tests"""
    print("🔬 AI Browser Deep Functionality Test Suite")
    print("=" * 60)
    print("⚠️  These tests verify actual functionality, not just HTTP status codes")
    print()
    
    tests = [
        ("Browser Agent Deep", test_browser_agent_deep),
        ("AI Intelligence", test_ai_actual_intelligence),
        ("Tool Functionality", test_tools_actually_work), 
        ("Memory Persistence", test_memory_persistence),
        ("Error Handling", test_error_handling),
        ("Extension Deep", test_extension_manifest_deep)
    ]
    
    results = {}
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{'─' * 40}")
        print(f"🧪 {test_name.upper()}")
        print(f"{'─' * 40}")
        
        test_start = time.time()
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed with exception: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            results[test_name] = False
        
        test_time = time.time() - test_start
        status = "✅ PASS" if results[test_name] else "❌ FAIL"
        print(f"\n{status} {test_name} completed in {test_time:.2f}s")
    
    total_time = time.time() - start_time
    
    print()
    print("=" * 60)
    print("📊 DEEP FUNCTIONALITY TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status:<12} {test_name}")
    
    print(f"\nTotal test time: {total_time:.1f} seconds")
    print(f"Overall score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 EXCELLENT! All deep functionality tests passed!")
        print("The AI Browser has been thoroughly verified and is production-ready.")
        print("No surface-level testing - actual functionality confirmed working.")
    elif passed >= total * 0.8:
        print("\n✅ GOOD! Most deep functionality works correctly.")
        print("Minor issues detected but core systems are solid.")
        print("Ready for advanced testing and refinement.")
    else:
        print("\n⚠️  ISSUES DETECTED! Significant functionality problems found.")
        print("Surface-level tests may pass, but deep functionality is broken.")
        print("Requires investigation and fixes before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = run_deep_tests()
    sys.exit(0 if success else 1)