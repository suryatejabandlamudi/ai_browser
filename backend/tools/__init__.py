#!/usr/bin/env python3
"""
AI Browser Tools Package
Comprehensive tool system for browser automation with structured schemas and validation
"""

from .base_tool import (
    BaseTool,
    ToolSchema, 
    ToolResult,
    ToolType,
    ToolExecutionContext,
    ToolRegistry,
    ToolManager,
    tool_registry
)

from .navigation_tool import (
    NavigateTool,
    BackTool, 
    ForwardTool,
    RefreshTool,
    ScrollTool,
    register_navigation_tools
)

from .interaction_tool import (
    ClickTool,
    TypeTool,
    PressKeyTool,
    HoverTool,
    DragDropTool,
    SelectTool,
    SelectorType,
    register_interaction_tools
)

from .extraction_tool import (
    ExtractContentTool,
    ExtractElementTool,
    ExtractTableTool,
    ExtractLinksTool,
    SearchContentTool,
    GetPageInfoTool,
    ExtractType,
    register_extraction_tools
)

from .visual_tool import (
    ScreenshotTool,
    HighlightElementTool,
    VisualFindTool,
    CompareImageTool,
    GetElementBoundsTool,
    ScrollIntoViewTool,
    ScreenshotFormat,
    register_visual_tools
)

from .wait_tool import (
    WaitTool,
    WaitForElementTool,
    WaitForPageLoadTool,
    SleepTool,
    WaitForResponseTool,
    WaitCondition,
    register_wait_tools
)

from .accessibility_tool import (
    GetAccessibilityTreeTool,
    FindByAccessibilityTool,
    GetElementAccessibilityTool,
    GetLandmarksTool,
    GetHeadingsTool,
    GetFormControlsTool,
    GetInteractiveElementsTool,
    register_accessibility_tools
)

# Version information
__version__ = "1.0.0"
__author__ = "AI Browser Team"

def register_all_tools():
    """Register all available tools with the global tool registry"""
    register_navigation_tools()
    register_interaction_tools() 
    register_extraction_tools()
    register_visual_tools()
    register_wait_tools()
    register_accessibility_tools()

def get_tool_manager() -> ToolManager:
    """Get a configured tool manager instance"""
    if not tool_registry.tools:
        register_all_tools()
    return ToolManager(tool_registry)

def get_available_tools() -> dict:
    """Get a dictionary of all available tools organized by type"""
    if not tool_registry.tools:
        register_all_tools()
    
    tools_by_type = {}
    for tool_type in ToolType:
        tools = tool_registry.get_tools_by_type(tool_type)
        if tools:
            tools_by_type[tool_type.value] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.schema.model_json_schema()
                }
                for tool in tools
            ]
    
    return tools_by_type

def create_tool_execution_context(
    page_url: str,
    page_content: str = None,
    page_title: str = None,
    **kwargs
) -> ToolExecutionContext:
    """Create a tool execution context with common page information"""
    return ToolExecutionContext(
        page_url=page_url,
        page_content=page_content,
        page_title=page_title,
        **kwargs
    )

# Auto-register tools when module is imported
register_all_tools()

__all__ = [
    # Base classes
    'BaseTool',
    'ToolSchema', 
    'ToolResult',
    'ToolType',
    'ToolExecutionContext',
    'ToolRegistry',
    'ToolManager',
    'tool_registry',
    
    # Navigation tools
    'NavigateTool',
    'BackTool', 
    'ForwardTool',
    'RefreshTool',
    'ScrollTool',
    
    # Interaction tools
    'ClickTool',
    'TypeTool',
    'PressKeyTool',
    'HoverTool',
    'DragDropTool',
    'SelectTool',
    'SelectorType',
    
    # Extraction tools
    'ExtractContentTool',
    'ExtractElementTool',
    'ExtractTableTool',
    'ExtractLinksTool',
    'SearchContentTool',
    'GetPageInfoTool',
    'ExtractType',
    
    # Visual tools
    'ScreenshotTool',
    'HighlightElementTool',
    'VisualFindTool',
    'CompareImageTool',
    'GetElementBoundsTool',
    'ScrollIntoViewTool',
    'ScreenshotFormat',
    
    # Wait tools
    'WaitTool',
    'WaitForElementTool',
    'WaitForPageLoadTool',
    'SleepTool',
    'WaitForResponseTool',
    'WaitCondition',
    
    # Accessibility tools
    'GetAccessibilityTreeTool',
    'FindByAccessibilityTool',
    'GetElementAccessibilityTool',
    'GetLandmarksTool',
    'GetHeadingsTool',
    'GetFormControlsTool',
    'GetInteractiveElementsTool',
    
    # Utility functions
    'register_all_tools',
    'get_tool_manager',
    'get_available_tools',
    'create_tool_execution_context',
]