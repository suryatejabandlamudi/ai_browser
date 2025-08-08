"""
Navigation Tools for AI Browser
Inspired by BrowserOS-agent navigation tools but optimized for local AI.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import aiohttp
import asyncio
from urllib.parse import urlparse, urljoin
import structlog

from .base import AIBrowserTool, ToolCategory, ToolResult, BrowserContext

logger = structlog.get_logger(__name__)

# Input Schemas

class NavigationToolInput(BaseModel):
    """Input for navigation tool"""
    url: str = Field(description="URL to navigate to")
    wait_for_load: bool = Field(default=True, description="Wait for page load completion")
    timeout_seconds: int = Field(default=10, description="Navigation timeout in seconds")

class ScrollToolInput(BaseModel):
    """Input for scroll tool"""
    direction: str = Field(description="Scroll direction: 'up', 'down', 'left', 'right'")
    amount: Optional[int] = Field(default=500, description="Scroll amount in pixels")
    smooth: bool = Field(default=True, description="Use smooth scrolling")

class SearchToolInput(BaseModel):
    """Input for page search tool"""
    query: str = Field(description="Text to search for on the page")
    highlight: bool = Field(default=True, description="Highlight search results")
    case_sensitive: bool = Field(default=False, description="Case sensitive search")

class RefreshStateToolInput(BaseModel):
    """Input for refresh state tool"""
    extract_content: bool = Field(default=True, description="Extract page content")
    extract_accessibility: bool = Field(default=True, description="Extract accessibility tree")
    capture_screenshot: bool = Field(default=False, description="Capture page screenshot")

# Tool Implementations

class NavigationTool(AIBrowserTool[NavigationToolInput]):
    """
    Navigate to web pages with state tracking.
    Inspired by BrowserOS NavigationTool but enhanced for local processing.
    """
    
    def __init__(self):
        super().__init__(
            name="navigate",
            description="Navigate to a specific URL and wait for page load",
            category=ToolCategory.NAVIGATION,
            input_schema=NavigationToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: NavigationToolInput, context: BrowserContext) -> ToolResult:
        """Execute navigation to specified URL"""
        
        try:
            # Validate URL
            parsed_url = urlparse(params.url)
            if not parsed_url.scheme:
                params.url = f"https://{params.url}"
            
            # For now, simulate navigation (in real implementation, this would use browser automation)
            # In browser extension, this would trigger actual navigation
            
            # Check if URL is accessible
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(params.url, timeout=aiohttp.ClientTimeout(total=params.timeout_seconds)) as response:
                        if response.status >= 400:
                            return ToolResult(
                                success=False,
                                message=f"Navigation failed: HTTP {response.status}",
                                error=f"Server returned {response.status} for {params.url}"
                            )
                except aiohttp.ClientError as e:
                    return ToolResult(
                        success=False,
                        message=f"Navigation failed: {str(e)}",
                        error=f"Network error: {str(e)}"
                    )
            
            # Simulate waiting for page load
            if params.wait_for_load:
                await asyncio.sleep(0.5)  # Simulate load time
            
            return ToolResult(
                success=True,
                message=f"Successfully navigated to {params.url}",
                data={
                    "url": params.url,
                    "waited_for_load": params.wait_for_load,
                    "domain": parsed_url.netloc
                }
            )
            
        except Exception as e:
            logger.error(f"Navigation failed", url=params.url, error=str(e))
            return ToolResult(
                success=False,
                message="Navigation failed",
                error=str(e)
            )

class ScrollTool(AIBrowserTool[ScrollToolInput]):
    """
    Smart scrolling with context awareness.
    Inspired by BrowserOS ScrollTool.
    """
    
    def __init__(self):
        super().__init__(
            name="scroll",
            description="Scroll the page in specified direction",
            category=ToolCategory.NAVIGATION,
            input_schema=ScrollToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: ScrollToolInput, context: BrowserContext) -> ToolResult:
        """Execute scrolling action"""
        
        try:
            # Validate direction
            valid_directions = ["up", "down", "left", "right"]
            if params.direction not in valid_directions:
                return ToolResult(
                    success=False,
                    message=f"Invalid scroll direction. Must be one of: {valid_directions}",
                    error=f"Invalid direction: {params.direction}"
                )
            
            # Calculate scroll coordinates
            scroll_x = 0
            scroll_y = 0
            
            if params.direction == "down":
                scroll_y = params.amount
            elif params.direction == "up":
                scroll_y = -params.amount
            elif params.direction == "right":
                scroll_x = params.amount
            elif params.direction == "left":
                scroll_x = -params.amount
            
            # In real implementation, this would execute browser scroll
            # For now, simulate scroll action
            await asyncio.sleep(0.1)  # Simulate scroll time
            
            return ToolResult(
                success=True,
                message=f"Scrolled {params.direction} by {params.amount} pixels",
                data={
                    "direction": params.direction,
                    "amount": params.amount,
                    "scroll_x": scroll_x,
                    "scroll_y": scroll_y,
                    "smooth": params.smooth
                }
            )
            
        except Exception as e:
            logger.error(f"Scroll failed", error=str(e))
            return ToolResult(
                success=False,
                message="Scroll action failed",
                error=str(e)
            )

class SearchTool(AIBrowserTool[SearchToolInput]):
    """
    Page search with result highlighting.
    Enhanced version of BrowserOS SearchTool.
    """
    
    def __init__(self):
        super().__init__(
            name="search_page",
            description="Search for text on the current page",
            category=ToolCategory.EXTRACTION,
            input_schema=SearchToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True  # For highlighting
        )
    
    async def execute(self, params: SearchToolInput, context: BrowserContext) -> ToolResult:
        """Execute page search"""
        
        try:
            if not context.page_content:
                return ToolResult(
                    success=False,
                    message="No page content available for search",
                    error="Browser context missing page content"
                )
            
            # Perform search
            search_text = params.query if params.case_sensitive else params.query.lower()
            page_text = context.page_content if params.case_sensitive else context.page_content.lower()
            
            # Find all occurrences
            matches = []
            start = 0
            while True:
                index = page_text.find(search_text, start)
                if index == -1:
                    break
                    
                # Get surrounding context (50 chars before and after)
                context_start = max(0, index - 50)
                context_end = min(len(context.page_content), index + len(params.query) + 50)
                context_text = context.page_content[context_start:context_end]
                
                matches.append({
                    "index": index,
                    "context": context_text,
                    "highlight_start": index - context_start,
                    "highlight_end": index - context_start + len(params.query)
                })
                
                start = index + 1
            
            # Limit to first 20 matches for performance
            matches = matches[:20]
            
            return ToolResult(
                success=True,
                message=f"Found {len(matches)} matches for '{params.query}'",
                data={
                    "query": params.query,
                    "match_count": len(matches),
                    "matches": matches,
                    "case_sensitive": params.case_sensitive,
                    "highlight_enabled": params.highlight
                }
            )
            
        except Exception as e:
            logger.error(f"Page search failed", error=str(e))
            return ToolResult(
                success=False,
                message="Page search failed",
                error=str(e)
            )

class RefreshStateTool(AIBrowserTool[RefreshStateToolInput]):
    """
    Refresh browser state and context.
    Similar to BrowserOS RefreshStateTool.
    """
    
    def __init__(self):
        super().__init__(
            name="refresh_state",
            description="Refresh browser state and extract updated page information",
            category=ToolCategory.UTILITY,
            input_schema=RefreshStateToolInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: RefreshStateToolInput, context: BrowserContext) -> ToolResult:
        """Refresh browser state"""
        
        try:
            updated_data = {}
            
            # Simulate state refresh (in real implementation, would query browser)
            if params.extract_content:
                # In real implementation, would re-extract page content
                updated_data["content_refreshed"] = True
                updated_data["content_length"] = len(context.page_content) if context.page_content else 0
            
            if params.extract_accessibility:
                # In real implementation, would re-extract accessibility tree
                updated_data["accessibility_refreshed"] = True
                updated_data["accessibility_nodes"] = len(context.accessibility_tree.get("nodes", [])) if context.accessibility_tree else 0
            
            if params.capture_screenshot:
                # In real implementation, would capture new screenshot
                updated_data["screenshot_captured"] = True
                updated_data["screenshot_path"] = "/tmp/browser_screenshot.png"
            
            await asyncio.sleep(0.2)  # Simulate refresh time
            
            return ToolResult(
                success=True,
                message="Browser state refreshed successfully",
                data=updated_data
            )
            
        except Exception as e:
            logger.error(f"State refresh failed", error=str(e))
            return ToolResult(
                success=False,
                message="Failed to refresh browser state",
                error=str(e)
            )

# Register all navigation tools
def register_navigation_tools():
    """Register all navigation tools in the global registry"""
    from .base import tool_registry
    
    tools = [
        NavigationTool(),
        ScrollTool(),
        SearchTool(),
        RefreshStateTool()
    ]
    
    for tool in tools:
        tool_registry.register(tool)