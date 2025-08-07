#!/usr/bin/env python3
"""
Visual Tools for AI Browser
Handles screenshots, visual element detection, and image-based interactions
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, validator
from enum import Enum

from .base_tool import BaseTool, ToolSchema, ToolResult

class ScreenshotFormat(str, Enum):
    """Screenshot output formats"""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"

class ScreenshotSchema(ToolSchema):
    """Schema for screenshot tool"""
    format: ScreenshotFormat = Field(default=ScreenshotFormat.PNG, description="Screenshot format")
    quality: int = Field(default=90, description="Image quality (1-100, for JPEG/WEBP)")
    full_page: bool = Field(default=False, description="Capture full page including scrollable areas")
    selector: Optional[str] = Field(default=None, description="Capture specific element only")
    clip_rect: Optional[Dict[str, int]] = Field(default=None, description="Custom clipping rectangle {x, y, width, height}")
    
    @validator('quality')
    def validate_quality(cls, v):
        if not 1 <= v <= 100:
            raise ValueError("Quality must be between 1 and 100")
        return v

class HighlightElementSchema(ToolSchema):
    """Schema for highlighting elements visually"""
    selector: str = Field(description="Element selector or description")
    color: str = Field(default="red", description="Highlight color (name or hex)")
    style: str = Field(default="outline", description="Highlight style: outline, fill, shadow")
    duration: int = Field(default=3000, description="Highlight duration in milliseconds")
    thickness: int = Field(default=2, description="Outline thickness in pixels")

class VisualFindSchema(ToolSchema):
    """Schema for finding elements visually"""
    description: str = Field(description="Visual description of element to find")
    confidence: float = Field(default=0.8, description="Minimum confidence threshold (0.0-1.0)")
    max_results: int = Field(default=5, description="Maximum results to return")
    region: Optional[Dict[str, int]] = Field(default=None, description="Search region {x, y, width, height}")

class CompareImageSchema(ToolSchema):
    """Schema for image comparison"""
    reference_image: str = Field(description="Base64 encoded reference image or URL")
    selector: Optional[str] = Field(default=None, description="Element to compare (defaults to full page)")
    threshold: float = Field(default=0.1, description="Difference threshold (0.0-1.0)")
    ignore_colors: bool = Field(default=False, description="Compare structure only, ignore colors")

class ScreenshotTool(BaseTool):
    """Tool for taking screenshots of pages or elements"""
    
    def __init__(self):
        super().__init__(
            name="screenshot",
            description="Take a screenshot of the current page or specific element",
            schema=ScreenshotSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        format_type = params.get("format", ScreenshotFormat.PNG)
        quality = params.get("quality", 90)
        full_page = params.get("full_page", False)
        selector = params.get("selector")
        clip_rect = params.get("clip_rect")
        
        # Build screenshot instructions
        if selector:
            target = f"element matching '{selector}'"
        elif clip_rect:
            target = f"region at ({clip_rect['x']}, {clip_rect['y']}) size {clip_rect['width']}x{clip_rect['height']}"
        elif full_page:
            target = "full page (including scrollable areas)"
        else:
            target = "current viewport"
        
        instructions = f"Take {format_type.value} screenshot of {target}"
        if format_type in [ScreenshotFormat.JPEG, ScreenshotFormat.WEBP]:
            instructions += f" at {quality}% quality"
        
        return ToolResult(
            success=True,
            message=f"Screenshot prepared: {target}",
            data={
                "action": "screenshot",
                "format": format_type.value,
                "quality": quality,
                "full_page": full_page,
                "selector": selector,
                "clip_rect": clip_rect,
                "instructions": instructions
            },
            metadata={
                "estimated_size": "large" if full_page else "medium"
            }
        )

class HighlightElementTool(BaseTool):
    """Tool for visually highlighting elements on the page"""
    
    def __init__(self):
        super().__init__(
            name="highlight_element",
            description="Visually highlight elements on the page for user guidance",
            schema=HighlightElementSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        color = params.get("color", "red")
        style = params.get("style", "outline")
        duration = params.get("duration", 3000)
        thickness = params.get("thickness", 2)
        
        instructions = f"Highlight element '{selector}' with {color} {style} for {duration/1000}s"
        if style == "outline":
            instructions += f" (thickness: {thickness}px)"
        
        return ToolResult(
            success=True,
            message=f"Element highlight prepared: {selector}",
            data={
                "action": "highlight_element",
                "selector": selector,
                "color": color,
                "style": style,
                "duration": duration,
                "thickness": thickness,
                "instructions": instructions
            }
        )

class VisualFindTool(BaseTool):
    """Tool for finding elements using visual AI"""
    
    def __init__(self):
        super().__init__(
            name="visual_find",
            description="Find elements on the page using visual description (experimental)",
            schema=VisualFindSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        description = params["description"]
        confidence = params.get("confidence", 0.8)
        max_results = params.get("max_results", 5)
        region = params.get("region")
        
        search_area = "entire page"
        if region:
            search_area = f"region ({region['x']}, {region['y']}) - ({region['x']+region['width']}, {region['y']+region['height']})"
        
        instructions = f"Find up to {max_results} elements matching '{description}' in {search_area} (confidence >= {confidence})"
        
        return ToolResult(
            success=True,
            message=f"Visual search prepared: '{description}'",
            data={
                "action": "visual_find",
                "description": description,
                "confidence": confidence,
                "max_results": max_results,
                "region": region,
                "instructions": instructions
            },
            metadata={
                "requires_screenshot": True,
                "experimental": True
            }
        )

class CompareImageTool(BaseTool):
    """Tool for comparing images or page states"""
    
    def __init__(self):
        super().__init__(
            name="compare_image",
            description="Compare current page or element with reference image",
            schema=CompareImageSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        reference_image = params["reference_image"]
        selector = params.get("selector")
        threshold = params.get("threshold", 0.1)
        ignore_colors = params.get("ignore_colors", False)
        
        target = f"element '{selector}'" if selector else "page"
        comparison_type = "structure" if ignore_colors else "visual"
        
        instructions = f"Compare {target} with reference image using {comparison_type} analysis (threshold: {threshold})"
        
        return ToolResult(
            success=True,
            message=f"Image comparison prepared: {target}",
            data={
                "action": "compare_image",
                "reference_image": reference_image,
                "selector": selector,
                "threshold": threshold,
                "ignore_colors": ignore_colors,
                "instructions": instructions
            },
            metadata={
                "requires_screenshot": True
            }
        )

class GetElementBoundsSchema(ToolSchema):
    """Schema for getting element boundaries"""
    selector: str = Field(description="Element selector or description")
    include_children: bool = Field(default=False, description="Include child element bounds")
    viewport_relative: bool = Field(default=True, description="Return coordinates relative to viewport")

class GetElementBoundsTool(BaseTool):
    """Tool for getting visual bounds of elements"""
    
    def __init__(self):
        super().__init__(
            name="get_element_bounds",
            description="Get the visual boundaries and position of elements",
            schema=GetElementBoundsSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        include_children = params.get("include_children", False)
        viewport_relative = params.get("viewport_relative", True)
        
        coordinate_system = "viewport-relative" if viewport_relative else "page-absolute"
        instructions = f"Get {coordinate_system} bounds for element '{selector}'"
        if include_children:
            instructions += " (including child elements)"
        
        return ToolResult(
            success=True,
            message=f"Element bounds query prepared: {selector}",
            data={
                "action": "get_element_bounds",
                "selector": selector,
                "include_children": include_children,
                "viewport_relative": viewport_relative,
                "instructions": instructions
            }
        )

class ScrollIntoViewSchema(ToolSchema):
    """Schema for scrolling elements into view"""
    selector: str = Field(description="Element selector or description")
    behavior: str = Field(default="smooth", description="Scroll behavior: auto, smooth")
    block: str = Field(default="center", description="Block alignment: start, center, end, nearest")
    inline: str = Field(default="nearest", description="Inline alignment: start, center, end, nearest")

class ScrollIntoViewTool(BaseTool):
    """Tool for scrolling elements into view"""
    
    def __init__(self):
        super().__init__(
            name="scroll_into_view",
            description="Scroll an element into view in the browser viewport",
            schema=ScrollIntoViewSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        behavior = params.get("behavior", "smooth")
        block = params.get("block", "center")
        inline = params.get("inline", "nearest")
        
        instructions = f"Scroll element '{selector}' into view ({behavior} scroll, {block} alignment)"
        
        return ToolResult(
            success=True,
            message=f"Scroll into view prepared: {selector}",
            data={
                "action": "scroll_into_view",
                "selector": selector,
                "behavior": behavior,
                "block": block,
                "inline": inline,
                "instructions": instructions
            }
        )

# Helper function to register all visual tools
def register_visual_tools():
    """Register all visual tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    tools = [
        (ScreenshotTool(), ToolType.VISUAL),
        (HighlightElementTool(), ToolType.VISUAL),
        (VisualFindTool(), ToolType.VISUAL),
        (CompareImageTool(), ToolType.VISUAL),
        (GetElementBoundsTool(), ToolType.VISUAL),
        (ScrollIntoViewTool(), ToolType.NAVIGATION),
    ]
    
    for tool, tool_type in tools:
        tool_registry.register(tool, tool_type)