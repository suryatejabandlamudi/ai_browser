#!/usr/bin/env python3
"""
Navigation Tools for AI Browser
Handles URL navigation, page loading, and navigation history
"""

from typing import Dict, Any, Optional, List
from pydantic import Field, validator
from urllib.parse import urljoin, urlparse
import re

from .base_tool import BaseTool, ToolSchema, ToolResult

class NavigateSchema(ToolSchema):
    """Schema for navigate tool parameters"""
    url: str = Field(description="URL to navigate to")
    wait_for_load: bool = Field(default=True, description="Wait for page to fully load")
    timeout: int = Field(default=10, description="Navigation timeout in seconds")
    
    @validator('url')
    def validate_url(cls, v):
        if not v:
            raise ValueError("URL cannot be empty")
        
        # Add protocol if missing
        if not v.startswith(('http://', 'https://', 'file://', 'data:')):
            if v.startswith('//'):
                v = 'https:' + v
            elif not v.startswith('/'):
                v = 'https://' + v
        
        # Basic URL validation
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            if not v.startswith(('file://', 'data:')):
                raise ValueError(f"Invalid URL format: {v}")
        
        return v

class BackSchema(ToolSchema):
    """Schema for back navigation"""
    steps: int = Field(default=1, description="Number of steps to go back")
    
    @validator('steps')
    def validate_steps(cls, v):
        if v < 1:
            raise ValueError("Steps must be positive")
        return v

class ForwardSchema(ToolSchema):
    """Schema for forward navigation"""
    steps: int = Field(default=1, description="Number of steps to go forward")
    
    @validator('steps')
    def validate_steps(cls, v):
        if v < 1:
            raise ValueError("Steps must be positive")
        return v

class RefreshSchema(ToolSchema):
    """Schema for page refresh"""
    hard_refresh: bool = Field(default=False, description="Force hard refresh (bypass cache)")

class NavigateTool(BaseTool):
    """Tool for navigating to URLs"""
    
    def __init__(self):
        super().__init__(
            name="navigate",
            description="Navigate to a specific URL",
            schema=NavigateSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        url = params["url"]
        wait_for_load = params.get("wait_for_load", True)
        timeout = params.get("timeout", 10)
        
        # Resolve relative URLs if we have current page context
        current_url = context.get("page_url")
        if current_url and not url.startswith(('http://', 'https://', 'file://', 'data:')):
            url = urljoin(current_url, url)
        
        return ToolResult(
            success=True,
            message=f"Navigation initiated to: {url}",
            data={
                "action": "navigate",
                "url": url,
                "wait_for_load": wait_for_load,
                "timeout": timeout,
                "instructions": f"Navigate browser to {url}"
            },
            metadata={
                "original_url": params["url"],
                "resolved_url": url
            }
        )

class BackTool(BaseTool):
    """Tool for navigating back in browser history"""
    
    def __init__(self):
        super().__init__(
            name="back",
            description="Navigate back in browser history",
            schema=BackSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        steps = params.get("steps", 1)
        
        return ToolResult(
            success=True,
            message=f"Navigating back {steps} step{'s' if steps != 1 else ''}",
            data={
                "action": "back",
                "steps": steps,
                "instructions": f"Navigate back {steps} step{'s' if steps != 1 else ''} in browser history"
            }
        )

class ForwardTool(BaseTool):
    """Tool for navigating forward in browser history"""
    
    def __init__(self):
        super().__init__(
            name="forward",
            description="Navigate forward in browser history",
            schema=ForwardSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        steps = params.get("steps", 1)
        
        return ToolResult(
            success=True,
            message=f"Navigating forward {steps} step{'s' if steps != 1 else ''}",
            data={
                "action": "forward",
                "steps": steps,
                "instructions": f"Navigate forward {steps} step{'s' if steps != 1 else ''} in browser history"
            }
        )

class RefreshTool(BaseTool):
    """Tool for refreshing the current page"""
    
    def __init__(self):
        super().__init__(
            name="refresh",
            description="Refresh the current page",
            schema=RefreshSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        hard_refresh = params.get("hard_refresh", False)
        
        return ToolResult(
            success=True,
            message=f"Page refresh initiated ({'hard' if hard_refresh else 'normal'})",
            data={
                "action": "refresh",
                "hard_refresh": hard_refresh,
                "instructions": f"Refresh page ({'bypass cache' if hard_refresh else 'normal refresh'})"
            }
        )

class ScrollSchema(ToolSchema):
    """Schema for scroll actions"""
    direction: str = Field(description="Scroll direction: up, down, left, right, top, bottom")
    amount: str = Field(default="page", description="Scroll amount: page, half, line, or pixel amount")
    element: Optional[str] = Field(default=None, description="Element to scroll (default: page)")
    
    @validator('direction')
    def validate_direction(cls, v):
        valid_directions = ['up', 'down', 'left', 'right', 'top', 'bottom']
        if v.lower() not in valid_directions:
            raise ValueError(f"Direction must be one of: {', '.join(valid_directions)}")
        return v.lower()

class ScrollTool(BaseTool):
    """Tool for scrolling pages and elements"""
    
    def __init__(self):
        super().__init__(
            name="scroll",
            description="Scroll the page or a specific element",
            schema=ScrollSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        direction = params["direction"]
        amount = params.get("amount", "page")
        element = params.get("element")
        
        # Convert direction to standardized format
        direction_map = {
            "up": "up",
            "down": "down", 
            "left": "left",
            "right": "right",
            "top": "top",
            "bottom": "bottom"
        }
        
        normalized_direction = direction_map.get(direction, "down")
        
        return ToolResult(
            success=True,
            message=f"Scrolling {normalized_direction} by {amount}" + (f" on {element}" if element else ""),
            data={
                "action": "scroll",
                "direction": normalized_direction,
                "amount": amount,
                "element": element,
                "instructions": f"Scroll {normalized_direction} by {amount}" + (f" on element '{element}'" if element else " on page")
            }
        )

# Helper function to register all navigation tools
def register_navigation_tools():
    """Register all navigation tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    tools = [
        (NavigateTool(), ToolType.NAVIGATION),
        (BackTool(), ToolType.NAVIGATION),
        (ForwardTool(), ToolType.NAVIGATION),
        (RefreshTool(), ToolType.NAVIGATION),
        (ScrollTool(), ToolType.NAVIGATION),
    ]
    
    for tool, tool_type in tools:
        tool_registry.register(tool, tool_type)