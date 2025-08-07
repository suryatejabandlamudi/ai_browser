#!/usr/bin/env python3
"""
Wait Tools for AI Browser
Handles timing, page loading, and element waiting operations
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, validator
from enum import Enum

from .base_tool import BaseTool, ToolSchema, ToolResult

class WaitCondition(str, Enum):
    """Types of wait conditions"""
    TIME = "time"
    ELEMENT = "element"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_HIDDEN = "element_hidden"
    PAGE_LOAD = "page_load"
    NETWORK_IDLE = "network_idle"
    URL_CHANGE = "url_change"
    TEXT_PRESENT = "text_present"
    TEXT_ABSENT = "text_absent"

class WaitSchema(ToolSchema):
    """Schema for general wait operations"""
    condition: WaitCondition = Field(description="Type of wait condition")
    timeout: int = Field(default=10, description="Maximum wait time in seconds")
    
    # Time-based wait
    duration: Optional[float] = Field(default=None, description="Duration to wait in seconds (for TIME condition)")
    
    # Element-based waits
    selector: Optional[str] = Field(default=None, description="Element selector to wait for")
    
    # Text-based waits
    text: Optional[str] = Field(default=None, description="Text to wait for/against")
    
    # URL-based waits
    url_pattern: Optional[str] = Field(default=None, description="URL pattern to wait for")
    
    # Network-based waits
    network_idle_time: Optional[float] = Field(default=2.0, description="Network idle duration in seconds")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        if v > 300:  # 5 minutes max
            raise ValueError("Timeout cannot exceed 300 seconds")
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Duration must be positive")
        return v

class WaitForElementSchema(ToolSchema):
    """Schema for waiting for specific element states"""
    selector: str = Field(description="Element selector or description")
    state: str = Field(default="present", description="Element state: present, visible, hidden, clickable, enabled, disabled")
    timeout: int = Field(default=10, description="Maximum wait time in seconds")
    polling_interval: float = Field(default=0.5, description="Polling interval in seconds")
    
    @validator('state')
    def validate_state(cls, v):
        valid_states = ['present', 'visible', 'hidden', 'clickable', 'enabled', 'disabled']
        if v not in valid_states:
            raise ValueError(f"State must be one of: {', '.join(valid_states)}")
        return v

class WaitForPageLoadSchema(ToolSchema):
    """Schema for waiting for page load events"""
    event: str = Field(default="load", description="Load event: load, domcontentloaded, networkidle")
    timeout: int = Field(default=30, description="Maximum wait time in seconds")
    network_idle_time: float = Field(default=2.0, description="Network idle duration for networkidle event")
    
    @validator('event')
    def validate_event(cls, v):
        valid_events = ['load', 'domcontentloaded', 'networkidle']
        if v not in valid_events:
            raise ValueError(f"Event must be one of: {', '.join(valid_events)}")
        return v

class WaitTool(BaseTool):
    """General purpose wait tool with multiple condition types"""
    
    def __init__(self):
        super().__init__(
            name="wait",
            description="Wait for various conditions before proceeding",
            schema=WaitSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        condition = params["condition"]
        timeout = params.get("timeout", 10)
        
        if condition == WaitCondition.TIME:
            duration = params.get("duration", 1.0)
            instructions = f"Wait for {duration} seconds"
            
        elif condition == WaitCondition.ELEMENT:
            selector = params.get("selector", "")
            instructions = f"Wait up to {timeout}s for element '{selector}' to be present"
            
        elif condition == WaitCondition.ELEMENT_VISIBLE:
            selector = params.get("selector", "")
            instructions = f"Wait up to {timeout}s for element '{selector}' to be visible"
            
        elif condition == WaitCondition.ELEMENT_HIDDEN:
            selector = params.get("selector", "")
            instructions = f"Wait up to {timeout}s for element '{selector}' to be hidden"
            
        elif condition == WaitCondition.PAGE_LOAD:
            instructions = f"Wait up to {timeout}s for page to finish loading"
            
        elif condition == WaitCondition.NETWORK_IDLE:
            idle_time = params.get("network_idle_time", 2.0)
            instructions = f"Wait up to {timeout}s for network to be idle for {idle_time}s"
            
        elif condition == WaitCondition.URL_CHANGE:
            url_pattern = params.get("url_pattern", "")
            instructions = f"Wait up to {timeout}s for URL to match pattern '{url_pattern}'"
            
        elif condition == WaitCondition.TEXT_PRESENT:
            text = params.get("text", "")
            instructions = f"Wait up to {timeout}s for text '{text}' to appear on page"
            
        elif condition == WaitCondition.TEXT_ABSENT:
            text = params.get("text", "")
            instructions = f"Wait up to {timeout}s for text '{text}' to disappear from page"
        
        else:
            instructions = f"Wait with condition: {condition.value}"
        
        return ToolResult(
            success=True,
            message=f"Wait operation prepared: {condition.value}",
            data={
                "action": "wait",
                "condition": condition.value,
                "timeout": timeout,
                "duration": params.get("duration"),
                "selector": params.get("selector"),
                "text": params.get("text"),
                "url_pattern": params.get("url_pattern"),
                "network_idle_time": params.get("network_idle_time"),
                "instructions": instructions
            }
        )

class WaitForElementTool(BaseTool):
    """Specialized tool for waiting for element state changes"""
    
    def __init__(self):
        super().__init__(
            name="wait_for_element",
            description="Wait for an element to reach a specific state",
            schema=WaitForElementSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        state = params.get("state", "present")
        timeout = params.get("timeout", 10)
        polling_interval = params.get("polling_interval", 0.5)
        
        instructions = f"Wait up to {timeout}s for element '{selector}' to be {state} (check every {polling_interval}s)"
        
        return ToolResult(
            success=True,
            message=f"Element wait prepared: {selector} ({state})",
            data={
                "action": "wait_for_element",
                "selector": selector,
                "state": state,
                "timeout": timeout,
                "polling_interval": polling_interval,
                "instructions": instructions
            }
        )

class WaitForPageLoadTool(BaseTool):
    """Specialized tool for waiting for page load events"""
    
    def __init__(self):
        super().__init__(
            name="wait_for_page_load",
            description="Wait for page loading events to complete",
            schema=WaitForPageLoadSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        event = params.get("event", "load")
        timeout = params.get("timeout", 30)
        network_idle_time = params.get("network_idle_time", 2.0)
        
        if event == "networkidle":
            instructions = f"Wait up to {timeout}s for network to be idle for {network_idle_time}s"
        else:
            instructions = f"Wait up to {timeout}s for '{event}' event"
        
        return ToolResult(
            success=True,
            message=f"Page load wait prepared: {event}",
            data={
                "action": "wait_for_page_load",
                "event": event,
                "timeout": timeout,
                "network_idle_time": network_idle_time,
                "instructions": instructions
            }
        )

class SleepSchema(ToolSchema):
    """Schema for simple sleep operations"""
    duration: float = Field(description="Sleep duration in seconds")
    
    @validator('duration')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        if v > 60:  # 1 minute max for simple sleep
            raise ValueError("Sleep duration cannot exceed 60 seconds")
        return v

class SleepTool(BaseTool):
    """Simple sleep/delay tool"""
    
    def __init__(self):
        super().__init__(
            name="sleep",
            description="Simple sleep/delay for a specified duration",
            schema=SleepSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        duration = params["duration"]
        
        instructions = f"Sleep for {duration} seconds"
        
        return ToolResult(
            success=True,
            message=f"Sleep prepared: {duration}s",
            data={
                "action": "sleep",
                "duration": duration,
                "instructions": instructions
            }
        )

class WaitForResponseSchema(ToolSchema):
    """Schema for waiting for network responses"""
    url_pattern: str = Field(description="URL pattern to wait for (regex supported)")
    method: Optional[str] = Field(default=None, description="HTTP method to wait for")
    status_code: Optional[int] = Field(default=None, description="Expected status code")
    timeout: int = Field(default=30, description="Maximum wait time in seconds")

class WaitForResponseTool(BaseTool):
    """Tool for waiting for specific network responses"""
    
    def __init__(self):
        super().__init__(
            name="wait_for_response",
            description="Wait for a specific network request/response",
            schema=WaitForResponseSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        url_pattern = params["url_pattern"]
        method = params.get("method")
        status_code = params.get("status_code")
        timeout = params.get("timeout", 30)
        
        instructions = f"Wait up to {timeout}s for response matching URL pattern '{url_pattern}'"
        if method:
            instructions += f" (method: {method})"
        if status_code:
            instructions += f" (status: {status_code})"
        
        return ToolResult(
            success=True,
            message=f"Response wait prepared: {url_pattern}",
            data={
                "action": "wait_for_response",
                "url_pattern": url_pattern,
                "method": method,
                "status_code": status_code,
                "timeout": timeout,
                "instructions": instructions
            }
        )

# Helper function to register all wait tools
def register_wait_tools():
    """Register all wait tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    tools = [
        (WaitTool(), ToolType.WAIT),
        (WaitForElementTool(), ToolType.WAIT),
        (WaitForPageLoadTool(), ToolType.WAIT),
        (SleepTool(), ToolType.WAIT),
        (WaitForResponseTool(), ToolType.WAIT),
    ]
    
    for tool, tool_type in tools:
        tool_registry.register(tool, tool_type)