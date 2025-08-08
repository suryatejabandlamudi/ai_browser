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

__all__ = [
    'tool_registry',
    'streaming_executor', 
    'AIBrowserTool',
    'ToolCategory',
    'ToolResult',
    'BrowserContext',
    'initialize_tools'
]