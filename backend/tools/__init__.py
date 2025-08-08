"""
AI Browser Tool System
BrowserOS-inspired tool architecture for local-first AI browser automation.
"""

from .base import tool_registry, streaming_executor, AIBrowserTool, ToolCategory, ToolResult, BrowserContext
from .navigation import register_navigation_tools
from .interaction import register_interaction_tools  
from .planning import register_planning_tools
from .extraction import register_extraction_tools

def initialize_tools():
    """Initialize and register all AI browser tools"""
    register_navigation_tools()
    register_interaction_tools()
    register_planning_tools()
    register_extraction_tools()
    
    print(f"✅ Registered {len(tool_registry.get_all_tools())} AI browser tools")

# Auto-initialize when module is imported
initialize_tools()

def get_available_tools():
    """Get information about available tools"""
    all_tools_list = tool_registry.get_all_tools()
    tools_by_category = {}
    tool_names = []
    
    for tool in all_tools_list:
        category = tool.category.value if hasattr(tool, 'category') else 'general'
        if category not in tools_by_category:
            tools_by_category[category] = []
        tools_by_category[category].append(tool.name)
        tool_names.append(tool.name)
    
    return {
        'total_tools': len(all_tools_list),
        'tools_by_category': tools_by_category,
        'tool_names': tool_names
    }

__all__ = [
    'tool_registry',
    'streaming_executor', 
    'AIBrowserTool',
    'ToolCategory',
    'ToolResult',
    'BrowserContext',
    'initialize_tools',
    'get_available_tools'
]