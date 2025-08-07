#!/usr/bin/env python3
"""
Test script for structured tools system
Tests tool registration, validation, and basic functionality
"""

import asyncio
import json
from typing import Dict, Any

from tools import (
    get_tool_manager,
    get_available_tools,
    create_tool_execution_context,
    tool_registry
)

async def test_tool_registration():
    """Test that all tools are properly registered"""
    print("🧪 Testing tool registration...")
    
    # Check that tools are registered
    all_tools = tool_registry.get_all_tools()
    print(f"✅ Total tools registered: {len(all_tools)}")
    
    # Check tools by category
    from tools.base_tool import ToolType
    for tool_type in ToolType:
        tools = tool_registry.get_tools_by_type(tool_type)
        if tools:
            print(f"  📁 {tool_type.value}: {len(tools)} tools")
            for tool in tools[:3]:  # Show first 3 tools per category
                print(f"    • {tool.name}: {tool.description[:60]}...")
    
    print()

async def test_tool_schemas():
    """Test tool schema validation"""
    print("🧪 Testing tool schema validation...")
    
    # Test navigate tool
    navigate_tool = tool_registry.get_tool("navigate")
    if navigate_tool:
        # Valid parameters
        valid_params = {"url": "https://google.com", "wait_for_load": True}
        is_valid, error = navigate_tool.validate_params(valid_params)
        print(f"✅ Navigate tool validation (valid): {is_valid}")
        
        # Invalid parameters
        invalid_params = {"url": "", "timeout": -1}
        is_valid, error = navigate_tool.validate_params(invalid_params)
        print(f"✅ Navigate tool validation (invalid): {not is_valid} (error: {error[:50] if error else 'None'})")
    
    print()

async def test_tool_execution():
    """Test basic tool execution"""
    print("🧪 Testing tool execution...")
    
    # Create execution context
    context = create_tool_execution_context(
        page_url="https://example.com",
        page_title="Example Page"
    )
    
    # Test navigate tool
    tool_manager = get_tool_manager()
    result = await tool_manager.registry.execute_tool(
        "navigate",
        {"url": "https://google.com"},
        context.model_dump() if hasattr(context, 'model_dump') else context.__dict__
    )
    
    print(f"✅ Navigate tool execution: success={result.success}")
    print(f"   Message: {result.message}")
    if result.data:
        print(f"   Action: {result.data.get('action')}")
    
    # Test extract_content tool
    result = await tool_manager.registry.execute_tool(
        "extract_content",
        {"extract_type": "text", "clean_text": True},
        context.model_dump() if hasattr(context, 'model_dump') else context.__dict__
    )
    
    print(f"✅ Extract content tool execution: success={result.success}")
    print(f"   Message: {result.message}")
    
    print()

async def test_tool_chain_execution():
    """Test executing multiple tools in sequence"""
    print("🧪 Testing tool chain execution...")
    
    # Create execution context
    context = create_tool_execution_context(
        page_url="https://example.com",
        page_content="<html><body>Test page</body></html>"
    )
    
    # Define tool chain
    tool_chain = [
        {
            "name": "navigate",
            "parameters": {"url": "https://google.com"}
        },
        {
            "name": "wait_for_page_load",
            "parameters": {"event": "load", "timeout": 10}
        },
        {
            "name": "extract_content",
            "parameters": {"extract_type": "text"}
        }
    ]
    
    # Execute tool chain
    tool_manager = get_tool_manager()
    results = await tool_manager.execute_tool_chain(tool_chain, context)
    
    print(f"✅ Tool chain execution: {len(results)} tools executed")
    for i, result in enumerate(results):
        print(f"   Step {i+1}: {tool_chain[i]['name']} - success={result.success}")
    
    print()

async def test_available_tools_api():
    """Test the available tools API function"""
    print("🧪 Testing available tools API...")
    
    tools_info = get_available_tools()
    
    print(f"✅ Available tools API: {len(tools_info)} categories")
    total_tools = sum(len(tools) for tools in tools_info.values())
    print(f"   Total tools: {total_tools}")
    
    for category, tools in tools_info.items():
        print(f"   📁 {category}: {len(tools)} tools")
        if tools:
            print(f"      Example: {tools[0]['name']} - {tools[0]['description'][:50]}...")
    
    print()

async def test_error_handling():
    """Test error handling in tools"""
    print("🧪 Testing error handling...")
    
    tool_manager = get_tool_manager()
    context_dict = {
        "page_url": "https://example.com"
    }
    
    # Test non-existent tool
    result = await tool_manager.registry.execute_tool(
        "non_existent_tool",
        {},
        context_dict
    )
    
    print(f"✅ Non-existent tool handling: success={result.success}")
    print(f"   Error: {result.error}")
    
    # Test invalid parameters
    result = await tool_manager.registry.execute_tool(
        "navigate",
        {"invalid_param": "value"},
        context_dict
    )
    
    print(f"✅ Invalid parameters handling: success={result.success}")
    print(f"   Error: {result.error[:100] if result.error else 'None'}...")
    
    print()

async def main():
    """Run all tests"""
    print("🚀 Starting Structured Tools System Tests\n")
    
    try:
        await test_tool_registration()
        await test_tool_schemas()
        await test_tool_execution()
        await test_tool_chain_execution()
        await test_available_tools_api()
        await test_error_handling()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())