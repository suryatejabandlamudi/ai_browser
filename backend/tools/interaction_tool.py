#!/usr/bin/env python3
"""
Interaction Tools for AI Browser
Handles clicking, typing, form filling, and other user interactions
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, validator
from enum import Enum

from .base_tool import BaseTool, ToolSchema, ToolResult

class SelectorType(str, Enum):
    """Types of element selectors"""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ID = "id"
    CLASS = "class"
    NAME = "name"
    TAG = "tag"
    DESCRIPTION = "description"  # AI-powered element finding

class ClickSchema(ToolSchema):
    """Schema for click tool parameters"""
    selector: str = Field(description="Element selector or description")
    selector_type: SelectorType = Field(default=SelectorType.DESCRIPTION, description="Type of selector")
    wait_for_element: bool = Field(default=True, description="Wait for element to be present")
    timeout: int = Field(default=5, description="Wait timeout in seconds")
    click_type: str = Field(default="left", description="Click type: left, right, double")
    coordinates: Optional[Dict[str, int]] = Field(default=None, description="Exact click coordinates {x, y}")
    
    @validator('click_type')
    def validate_click_type(cls, v):
        valid_types = ['left', 'right', 'double', 'middle']
        if v not in valid_types:
            raise ValueError(f"Click type must be one of: {', '.join(valid_types)}")
        return v

class TypeSchema(ToolSchema):
    """Schema for typing tool parameters"""
    text: str = Field(description="Text to type")
    selector: Optional[str] = Field(default=None, description="Target element selector (defaults to focused element)")
    selector_type: SelectorType = Field(default=SelectorType.DESCRIPTION, description="Type of selector")
    clear_first: bool = Field(default=False, description="Clear existing text before typing")
    delay: int = Field(default=0, description="Delay between keystrokes in milliseconds")
    
    @validator('text')
    def validate_text(cls, v):
        if not v:
            raise ValueError("Text cannot be empty")
        return v

class PressKeySchema(ToolSchema):
    """Schema for key press actions"""
    key: str = Field(description="Key to press (e.g., 'Enter', 'Tab', 'Escape', 'Ctrl+A')")
    selector: Optional[str] = Field(default=None, description="Target element (defaults to focused element)")
    hold_duration: int = Field(default=0, description="Hold duration in milliseconds")
    
    @validator('key')
    def validate_key(cls, v):
        if not v:
            raise ValueError("Key cannot be empty")
        return v

class HoverSchema(ToolSchema):
    """Schema for hover actions"""
    selector: str = Field(description="Element selector or description")
    selector_type: SelectorType = Field(default=SelectorType.DESCRIPTION, description="Type of selector")
    duration: int = Field(default=1000, description="Hover duration in milliseconds")

class DragDropSchema(ToolSchema):
    """Schema for drag and drop actions"""
    source_selector: str = Field(description="Source element selector")
    target_selector: str = Field(description="Target element selector")
    source_selector_type: SelectorType = Field(default=SelectorType.DESCRIPTION, description="Source selector type")
    target_selector_type: SelectorType = Field(default=SelectorType.DESCRIPTION, description="Target selector type")

class ClickTool(BaseTool):
    """Tool for clicking elements on the page"""
    
    def __init__(self):
        super().__init__(
            name="click",
            description="Click on an element by selector or description",
            schema=ClickSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        selector_type = params.get("selector_type", SelectorType.DESCRIPTION)
        wait_for_element = params.get("wait_for_element", True)
        timeout = params.get("timeout", 5)
        click_type = params.get("click_type", "left")
        coordinates = params.get("coordinates")
        
        # Generate human-readable instructions
        if coordinates:
            instructions = f"Click at coordinates ({coordinates['x']}, {coordinates['y']})"
        elif selector_type == SelectorType.DESCRIPTION:
            instructions = f"Find and click element: '{selector}'"
        else:
            instructions = f"Click element with {selector_type.value} selector: '{selector}'"
        
        return ToolResult(
            success=True,
            message=f"Click action prepared: {selector}",
            data={
                "action": "click",
                "selector": selector,
                "selector_type": selector_type.value,
                "click_type": click_type,
                "wait_for_element": wait_for_element,
                "timeout": timeout,
                "coordinates": coordinates,
                "instructions": instructions
            },
            metadata={
                "element_description": selector if selector_type == SelectorType.DESCRIPTION else None
            }
        )

class TypeTool(BaseTool):
    """Tool for typing text into elements"""
    
    def __init__(self):
        super().__init__(
            name="type",
            description="Type text into an input field or element",
            schema=TypeSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        text = params["text"]
        selector = params.get("selector")
        selector_type = params.get("selector_type", SelectorType.DESCRIPTION)
        clear_first = params.get("clear_first", False)
        delay = params.get("delay", 0)
        
        # Generate instructions
        if selector:
            if selector_type == SelectorType.DESCRIPTION:
                instructions = f"Type '{text}' into element: '{selector}'"
            else:
                instructions = f"Type '{text}' into element with {selector_type.value} selector: '{selector}'"
        else:
            instructions = f"Type '{text}' into focused element"
        
        if clear_first:
            instructions = "Clear existing text and " + instructions.lower()
        
        return ToolResult(
            success=True,
            message=f"Type action prepared: '{text[:50]}{'...' if len(text) > 50 else ''}'",
            data={
                "action": "type",
                "text": text,
                "selector": selector,
                "selector_type": selector_type.value if selector else None,
                "clear_first": clear_first,
                "delay": delay,
                "instructions": instructions
            }
        )

class PressKeyTool(BaseTool):
    """Tool for pressing special keys"""
    
    def __init__(self):
        super().__init__(
            name="press_key",
            description="Press a keyboard key or key combination",
            schema=PressKeySchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        key = params["key"]
        selector = params.get("selector")
        hold_duration = params.get("hold_duration", 0)
        
        instructions = f"Press {key}"
        if selector:
            instructions += f" on element: '{selector}'"
        if hold_duration > 0:
            instructions += f" (hold for {hold_duration}ms)"
        
        return ToolResult(
            success=True,
            message=f"Key press action prepared: {key}",
            data={
                "action": "press_key",
                "key": key,
                "selector": selector,
                "hold_duration": hold_duration,
                "instructions": instructions
            }
        )

class HoverTool(BaseTool):
    """Tool for hovering over elements"""
    
    def __init__(self):
        super().__init__(
            name="hover",
            description="Hover over an element to reveal hidden content or tooltips",
            schema=HoverSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        selector_type = params.get("selector_type", SelectorType.DESCRIPTION)
        duration = params.get("duration", 1000)
        
        if selector_type == SelectorType.DESCRIPTION:
            instructions = f"Hover over element: '{selector}' for {duration}ms"
        else:
            instructions = f"Hover over element with {selector_type.value} selector: '{selector}' for {duration}ms"
        
        return ToolResult(
            success=True,
            message=f"Hover action prepared: {selector}",
            data={
                "action": "hover",
                "selector": selector,
                "selector_type": selector_type.value,
                "duration": duration,
                "instructions": instructions
            }
        )

class DragDropTool(BaseTool):
    """Tool for drag and drop operations"""
    
    def __init__(self):
        super().__init__(
            name="drag_drop",
            description="Drag an element from source to target location",
            schema=DragDropSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        source_selector = params["source_selector"]
        target_selector = params["target_selector"]
        source_type = params.get("source_selector_type", SelectorType.DESCRIPTION)
        target_type = params.get("target_selector_type", SelectorType.DESCRIPTION)
        
        instructions = f"Drag element '{source_selector}' to '{target_selector}'"
        
        return ToolResult(
            success=True,
            message=f"Drag-drop action prepared: {source_selector} → {target_selector}",
            data={
                "action": "drag_drop",
                "source_selector": source_selector,
                "target_selector": target_selector,
                "source_selector_type": source_type.value,
                "target_selector_type": target_type.value,
                "instructions": instructions
            }
        )

class SelectSchema(ToolSchema):
    """Schema for select dropdown actions"""
    selector: str = Field(description="Select element selector")
    value: Optional[str] = Field(default=None, description="Option value to select")
    text: Optional[str] = Field(default=None, description="Option text to select")
    index: Optional[int] = Field(default=None, description="Option index to select")
    
    @validator('value', 'text', 'index', pre=True, always=True)
    def validate_option_selection(cls, v, values):
        # At least one selection method must be provided
        if not any([values.get('value'), values.get('text'), v is not None]):
            raise ValueError("Must specify either value, text, or index for selection")
        return v

class SelectTool(BaseTool):
    """Tool for selecting options in dropdowns"""
    
    def __init__(self):
        super().__init__(
            name="select",
            description="Select an option from a dropdown or select element",
            schema=SelectSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        value = params.get("value")
        text = params.get("text")
        index = params.get("index")
        
        selection_method = "value" if value else ("text" if text else "index")
        selection_value = value or text or index
        
        instructions = f"Select option by {selection_method}: '{selection_value}' in dropdown '{selector}'"
        
        return ToolResult(
            success=True,
            message=f"Select action prepared: {selection_value}",
            data={
                "action": "select",
                "selector": selector,
                "value": value,
                "text": text,
                "index": index,
                "selection_method": selection_method,
                "instructions": instructions
            }
        )

# Helper function to register all interaction tools
def register_interaction_tools():
    """Register all interaction tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    tools = [
        (ClickTool(), ToolType.INTERACTION),
        (TypeTool(), ToolType.INTERACTION),
        (PressKeyTool(), ToolType.INTERACTION),
        (HoverTool(), ToolType.INTERACTION),
        (DragDropTool(), ToolType.INTERACTION),
        (SelectTool(), ToolType.FORM),
    ]
    
    for tool, tool_type in tools:
        tool_registry.register(tool, tool_type)