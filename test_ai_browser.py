#!/usr/bin/env python3
"""
AI Browser Demo Script
Tests the complete pipeline: Extension <-> FastAPI <-> GPT-OSS 20B
"""

import asyncio
import json
import aiohttp
from datetime import datetime

async def test_ai_browser():
    """Test our AI browser backend integration"""
    
    print("🤖 Testing AI Browser with GPT-OSS 20B")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("1️⃣ Testing backend health...")
        try:
            async with session.get(f"{backend_url}/health") as resp:
                health = await resp.json()
                print(f"   ✅ Backend: {health['status']}")
                print(f"   🧠 AI Model: {health['ai_model']}")
                print(f"   ⏱️  Timestamp: {health['timestamp']}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        
        # Test 2: Simple chat
        print("\n2️⃣ Testing AI chat...")
        chat_request = {
            "message": "What can you help me with on websites?",
        }
        
        try:
            async with session.post(
                f"{backend_url}/api/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            ) as resp:
                chat_response = await resp.json()
                print(f"   ✅ AI Response: {chat_response['response'][:150]}...")
                print(f"   📊 Metadata: {chat_response['metadata']}")
        except Exception as e:
            print(f"   ❌ Chat test failed: {e}")
            return
            
        # Test 3: Page context chat
        print("\n3️⃣ Testing AI with page context...")
        page_context_request = {
            "message": "Summarize this page for me",
            "page_url": "https://example.com",
            "page_content": "This is a demo page. It contains information about web development, AI, and browser automation. The main content discusses how AI can help users navigate websites more efficiently."
        }
        
        try:
            async with session.post(
                f"{backend_url}/api/chat", 
                json=page_context_request,
                headers={"Content-Type": "application/json"}
            ) as resp:
                context_response = await resp.json()
                print(f"   ✅ Context Response: {context_response['response'][:150]}...")
                print(f"   🔧 Has Actions: {context_response['metadata']['has_actions']}")
        except Exception as e:
            print(f"   ❌ Context test failed: {e}")
            return
            
        # Test 4: Page summarization
        print("\n4️⃣ Testing page summarization...")
        summary_request = {
            "url": "https://example.com",
            "content": "Welcome to Example.com. This domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission. More information about this domain can be found at the IANA website."
        }
        
        try:
            async with session.post(
                f"{backend_url}/api/summarize",
                json=summary_request,
                headers={"Content-Type": "application/json"}
            ) as resp:
                summary_response = await resp.json()
                print(f"   ✅ Summary: {summary_response['summary'][:100]}...")
                print(f"   📝 Key Points: {len(summary_response['key_points'])} points")
        except Exception as e:
            print(f"   ❌ Summarization test failed: {e}")
            return
    
    print("\n" + "=" * 50)
    print("🎉 AI Browser Backend Test Complete!")
    print("💡 Next: Load the extension in Chrome to test full integration")
    
    # Extension loading instructions
    print("\n📋 To test the complete AI browser:")
    print("1. Open Chrome and go to chrome://extensions/")
    print("2. Enable 'Developer mode' (toggle in top right)")
    print("3. Click 'Load unpacked' and select the extension/ folder")
    print("4. Open any website and use Cmd+E to open AI sidebar")
    print("5. Chat with GPT-OSS about the current page!")

if __name__ == "__main__":
    asyncio.run(test_ai_browser())