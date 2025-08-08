#!/usr/bin/env python3
"""
AI Browser Integration Tests
Test the complete stack: Custom Browser + Local GPT-OSS 20B + Backend API
"""

import asyncio
import json
import subprocess
import time
import requests
# import websocket  # Not needed for basic tests
from pathlib import Path

class AIBrowserIntegrationTest:
    """Complete integration testing for AI Browser stack"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.browser_binary = None
        self.backend_process = None
        self.browser_process = None
        
        # Test configuration
        self.backend_url = "http://localhost:8000"
        self.test_results = {
            "ollama_connection": False,
            "backend_startup": False,
            "ai_chat": False,
            "browser_automation": False,
            "autonomous_tasks": False,
            "browser_launch": False,
            "end_to_end": False
        }
    
    async def run_full_test_suite(self):
        """Run complete AI browser integration tests"""
        print("🧪 AI Browser Integration Test Suite")
        print("=" * 50)
        
        try:
            # Test 1: Ollama and GPT-OSS 20B
            print("\n1️⃣ Testing Ollama and GPT-OSS 20B connection...")
            await self.test_ollama_connection()
            
            # Test 2: Backend startup
            print("\n2️⃣ Testing backend startup...")
            await self.test_backend_startup()
            
            # Test 3: AI chat functionality
            print("\n3️⃣ Testing AI chat with GPT-OSS 20B...")
            await self.test_ai_chat()
            
            # Test 4: Browser automation tools
            print("\n4️⃣ Testing browser automation...")
            await self.test_browser_automation()
            
            # Test 5: Autonomous AI tasks
            print("\n5️⃣ Testing autonomous AI tasks...")
            await self.test_autonomous_tasks()
            
            # Test 6: Custom browser launch (if built)
            print("\n6️⃣ Testing custom browser launch...")
            await self.test_browser_launch()
            
            # Test 7: End-to-end integration
            print("\n7️⃣ Testing end-to-end integration...")
            await self.test_end_to_end_integration()
            
        finally:
            await self.cleanup()
        
        # Print results
        self.print_test_results()
    
    async def test_ollama_connection(self):
        """Test Ollama and GPT-OSS 20B connection"""
        try:
            # Check if Ollama is running
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/version"], 
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                print("   ✅ Ollama is running")
                
                # Test GPT-OSS 20B model
                test_payload = {
                    "model": "gpt-oss:20b",
                    "prompt": "Hello, respond with 'AI working'",
                    "stream": False,
                    "options": {"num_predict": 10}
                }
                
                result = subprocess.run([
                    "curl", "-s", "-X", "POST",
                    "http://localhost:11434/api/generate",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(test_payload)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and "response" in result.stdout:
                    print("   ✅ GPT-OSS 20B responding")
                    self.test_results["ollama_connection"] = True
                else:
                    print("   ❌ GPT-OSS 20B not responding")
            else:
                print("   ❌ Ollama not running - start with 'ollama serve'")
        except Exception as e:
            print(f"   ❌ Ollama test failed: {e}")
    
    async def test_backend_startup(self):
        """Test backend startup"""
        try:
            # Start backend
            print("   🚀 Starting AI Browser backend...")
            self.backend_process = subprocess.Popen([
                "python", "main.py"
            ], cwd=self.backend_dir)
            
            # Wait for startup
            await asyncio.sleep(5)
            
            # Test health check
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Backend started successfully")
                print(f"   📊 Agents: {sum(health_data.get('agents', {}).values())}")
                print(f"   🔧 Tools: {health_data.get('tools', {}).get('total_registered', 0)}")
                self.test_results["backend_startup"] = True
            else:
                print(f"   ❌ Backend health check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Backend startup failed: {e}")
    
    async def test_ai_chat(self):
        """Test AI chat functionality"""
        try:
            if not self.test_results["backend_startup"]:
                print("   ⏩ Skipped - backend not running")
                return
                
            # Test basic chat
            chat_payload = {
                "message": "Hello! Say 'Local AI working' if you can hear me.",
                "page_url": "https://example.com"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/chat",
                json=chat_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                ai_response = chat_data.get("response", "")
                model_used = chat_data.get("metadata", {}).get("model", "unknown")
                
                print(f"   ✅ AI chat working")
                print(f"   🤖 Model: {model_used}")
                print(f"   💬 Response preview: {ai_response[:100]}...")
                self.test_results["ai_chat"] = True
            else:
                print(f"   ❌ AI chat failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ AI chat test failed: {e}")
    
    async def test_browser_automation(self):
        """Test browser automation tools"""
        try:
            if not self.test_results["backend_startup"]:
                print("   ⏩ Skipped - backend not running")
                return
            
            # Test action execution
            action_payload = {
                "action_type": "click",
                "parameters": {"target": "login button"},
                "page_url": "https://example.com"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/action",
                json=action_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                action_result = response.json()
                print(f"   ✅ Browser automation working")
                print(f"   🎯 Action: {action_result.get('success', False)}")
                self.test_results["browser_automation"] = True
            else:
                print(f"   ❌ Browser automation failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Browser automation test failed: {e}")
    
    async def test_autonomous_tasks(self):
        """Test autonomous AI task execution"""
        try:
            if not self.test_results["backend_startup"]:
                print("   ⏩ Skipped - backend not running")
                return
            
            # Test autonomous task
            task_payload = {
                "task": "Search for 'AI browser' on the current page",
                "current_url": "https://google.com",
                "page_content": "Google search page content..."
            }
            
            response = requests.post(
                f"{self.backend_url}/api/agent/execute-task",
                json=task_payload,
                timeout=60
            )
            
            if response.status_code == 200:
                task_result = response.json()
                progress_count = len(task_result.get("progress", []))
                print(f"   ✅ Autonomous tasks working")
                print(f"   📈 Progress updates: {progress_count}")
                self.test_results["autonomous_tasks"] = True
            else:
                print(f"   ❌ Autonomous tasks failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Autonomous tasks test failed: {e}")
    
    async def test_browser_launch(self):
        """Test custom browser launch"""
        try:
            # Look for built browser
            possible_locations = [
                self.base_dir / "dist" / "AIBrowser" / "AIBrowser.app" / "Contents" / "MacOS" / "AIBrowser",
                self.base_dir / "backend" / "chromium" / "src" / "out" / "Default" / "chrome",
                self.base_dir / "backend" / "chromium" / "build" / "src" / "out" / "Default" / "chrome"
            ]
            
            browser_binary = None
            for location in possible_locations:
                if location.exists():
                    browser_binary = location
                    break
            
            if browser_binary:
                print(f"   🌐 Found browser at: {browser_binary}")
                
                # Test browser launch
                self.browser_process = subprocess.Popen([
                    str(browser_binary),
                    "--disable-web-security",
                    "--user-data-dir=/tmp/ai-browser-test",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--headless"  # Run in headless mode for testing
                ])
                
                # Give browser time to start
                await asyncio.sleep(3)
                
                if self.browser_process.poll() is None:
                    print("   ✅ Custom browser launched successfully")
                    self.test_results["browser_launch"] = True
                else:
                    print("   ❌ Browser crashed on startup")
            else:
                print("   ⏩ Custom browser not built - run build_ai_browser.py first")
        except Exception as e:
            print(f"   ❌ Browser launch test failed: {e}")
    
    async def test_end_to_end_integration(self):
        """Test complete end-to-end integration"""
        try:
            if not all([
                self.test_results["ollama_connection"],
                self.test_results["backend_startup"],
                self.test_results["ai_chat"]
            ]):
                print("   ⏩ Skipped - prerequisites not met")
                return
            
            print("   🔗 Testing complete integration...")
            
            # Test AI-powered page analysis
            analysis_payload = {
                "page_url": "https://example.com",
                "page_content": "<html><body><h1>Example Page</h1><p>This is a test page.</p></body></html>",
                "question": "What is this page about?"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/search/analyze-page",
                json=analysis_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                analysis_result = response.json()
                print("   ✅ End-to-end integration working")
                print(f"   🧠 AI Analysis: {analysis_result.get('analysis', '')[:100]}...")
                self.test_results["end_to_end"] = True
            else:
                print(f"   ❌ End-to-end test failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ End-to-end test failed: {e}")
    
    async def cleanup(self):
        """Clean up test processes"""
        if self.backend_process:
            self.backend_process.terminate()
            await asyncio.sleep(2)
            if self.backend_process.poll() is None:
                self.backend_process.kill()
        
        if self.browser_process:
            self.browser_process.terminate()
            await asyncio.sleep(2)
            if self.browser_process.poll() is None:
                self.browser_process.kill()
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 50)
        print("🏆 AI BROWSER INTEGRATION TEST RESULTS")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name:<20} {status}")
        
        print("-" * 50)
        print(f"   TOTAL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("🤖 Your AI Browser stack is working perfectly!")
        elif passed_tests >= total_tests * 0.7:
            print("\n✨ Most tests passed - good progress!")
            print("🔧 Fix the failing components for full functionality")
        else:
            print("\n⚠️  Several tests failed")
            print("🔍 Check the logs above for specific issues")
        
        print("\n💡 Next Steps:")
        if not self.test_results["ollama_connection"]:
            print("   1. Start Ollama: ollama serve")
            print("   2. Pull GPT-OSS model: ollama pull gpt-oss:20b")
        if not self.test_results["browser_launch"]:
            print("   3. Build custom browser: python build_ai_browser.py --all")
        if passed_tests == total_tests:
            print("   4. Your privacy-first AI browser is ready! 🚀")

async def main():
    tester = AIBrowserIntegrationTest()
    await tester.run_full_test_suite()

if __name__ == "__main__":
    asyncio.run(main())