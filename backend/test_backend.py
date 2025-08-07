#!/usr/bin/env python3
"""Simple test script to verify backend components work"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

async def test_ai_client():
    """Test AI client connection"""
    try:
        from ai_client import AIClient
        
        client = AIClient()
        print("Testing AI client connection...")
        
        if await client.test_connection():
            print("✅ AI client connection successful")
            
            # Test basic chat
            response = await client.chat("Hello, can you confirm you're working?")
            print(f"✅ Chat response: {response['content'][:100]}...")
            
        else:
            print("❌ AI client connection failed")
            
        await client.close()
        
    except Exception as e:
        print(f"❌ AI client test failed: {e}")

async def test_content_extractor():
    """Test content extraction"""
    try:
        from content_extractor import ContentExtractor
        
        extractor = ContentExtractor()
        print("Testing content extractor...")
        
        # Test with simple HTML
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is a test paragraph with some content.</p>
                <p>Another paragraph here.</p>
            </body>
        </html>
        """
        
        content = await extractor.extract_main_content(html, "http://test.com")
        print(f"✅ Content extracted: {len(content)} characters")
        print(f"Preview: {content[:100]}...")
        
        await extractor.close()
        
    except Exception as e:
        print(f"❌ Content extractor test failed: {e}")

async def test_browser_agent():
    """Test browser agent action parsing"""
    try:
        from browser_agent import BrowserAgent
        
        agent = BrowserAgent()
        print("Testing browser agent...")
        
        # Test action parsing
        test_response = "I'll click the 'Login' button and then type 'user@example.com' in the email field."
        actions = await agent.parse_actions(test_response)
        
        print(f"✅ Parsed {len(actions)} actions from response")
        for action in actions:
            print(f"   - {action}")
            
    except Exception as e:
        print(f"❌ Browser agent test failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Testing AI Browser Backend Components\n")
    
    await test_ai_client()
    print()
    await test_content_extractor()
    print()
    await test_browser_agent()
    print()
    
    print("✅ Backend component tests completed!")

if __name__ == "__main__":
    asyncio.run(main())