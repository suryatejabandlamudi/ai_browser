#!/usr/bin/env python3
"""
Extraction Tools for AI Browser
Handles content extraction, data scraping, and information gathering from pages
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, validator
from enum import Enum

from .base_tool import BaseTool, ToolSchema, ToolResult

class ExtractType(str, Enum):
    """Types of content to extract"""
    TEXT = "text"
    HTML = "html"
    LINKS = "links"
    IMAGES = "images"
    FORMS = "forms"
    TABLES = "tables"
    LISTS = "lists"
    ATTRIBUTES = "attributes"
    METADATA = "metadata"
    ALL = "all"

class ExtractContentSchema(ToolSchema):
    """Schema for content extraction"""
    extract_type: ExtractType = Field(default=ExtractType.TEXT, description="Type of content to extract")
    selector: Optional[str] = Field(default=None, description="CSS selector to target specific elements")
    attribute: Optional[str] = Field(default=None, description="Specific attribute to extract (for ATTRIBUTES type)")
    clean_text: bool = Field(default=True, description="Clean and normalize extracted text")
    include_metadata: bool = Field(default=False, description="Include element metadata")

class ExtractElementSchema(ToolSchema):
    """Schema for extracting specific elements"""
    description: str = Field(description="Human description of elements to find and extract")
    max_results: int = Field(default=10, description="Maximum number of elements to extract")
    include_children: bool = Field(default=False, description="Include child elements")
    format: str = Field(default="text", description="Output format: text, html, json")

class ExtractTableSchema(ToolSchema):
    """Schema for table extraction"""
    selector: Optional[str] = Field(default=None, description="Table selector (finds all tables if not specified)")
    headers: bool = Field(default=True, description="Extract table headers")
    format: str = Field(default="json", description="Output format: json, csv, raw")
    max_rows: Optional[int] = Field(default=None, description="Maximum rows to extract per table")

class ExtractLinksSchema(ToolSchema):
    """Schema for link extraction"""
    selector: Optional[str] = Field(default="a[href]", description="Link selector")
    include_internal: bool = Field(default=True, description="Include internal links")
    include_external: bool = Field(default=True, description="Include external links")
    resolve_relative: bool = Field(default=True, description="Resolve relative URLs")

class SearchContentSchema(ToolSchema):
    """Schema for searching content on page"""
    query: str = Field(description="Search query or pattern")
    search_type: str = Field(default="text", description="Search type: text, regex, xpath")
    case_sensitive: bool = Field(default=False, description="Case sensitive search")
    max_results: int = Field(default=20, description="Maximum results to return")

class ExtractContentTool(BaseTool):
    """Tool for extracting various types of content from pages"""
    
    def __init__(self):
        super().__init__(
            name="extract_content",
            description="Extract specific content types from the current page",
            schema=ExtractContentSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        extract_type_param = params.get("extract_type", ExtractType.TEXT)
        
        # Handle both string and enum inputs
        if isinstance(extract_type_param, str):
            try:
                extract_type = ExtractType(extract_type_param.lower())
            except ValueError:
                extract_type = ExtractType.TEXT
        else:
            extract_type = extract_type_param
            
        selector = params.get("selector")
        attribute = params.get("attribute")
        clean_text = params.get("clean_text", True)
        include_metadata = params.get("include_metadata", False)
        
        # Build extraction instructions
        if selector:
            target = f"elements matching '{selector}'"
        else:
            target = "the page"
        
        if extract_type == ExtractType.ATTRIBUTES and attribute:
            instructions = f"Extract {attribute} attributes from {target}"
        else:
            instructions = f"Extract {extract_type.value} from {target}"
        
        return ToolResult(
            success=True,
            message=f"Content extraction prepared: {extract_type.value}",
            data={
                "action": "extract_content",
                "extract_type": extract_type.value,
                "selector": selector,
                "attribute": attribute,
                "clean_text": clean_text,
                "include_metadata": include_metadata,
                "instructions": instructions
            }
        )

class ExtractElementTool(BaseTool):
    """Tool for finding and extracting elements by description"""
    
    def __init__(self):
        super().__init__(
            name="extract_element",
            description="Find and extract elements based on human description",
            schema=ExtractElementSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        description = params["description"]
        max_results = params.get("max_results", 10)
        include_children = params.get("include_children", False)
        format_type = params.get("format", "text")
        
        instructions = f"Find and extract up to {max_results} elements: '{description}'"
        if include_children:
            instructions += " (including child elements)"
        
        return ToolResult(
            success=True,
            message=f"Element extraction prepared: {description}",
            data={
                "action": "extract_element",
                "description": description,
                "max_results": max_results,
                "include_children": include_children,
                "format": format_type,
                "instructions": instructions
            }
        )

class ExtractTableTool(BaseTool):
    """Tool for extracting structured data from tables"""
    
    def __init__(self):
        super().__init__(
            name="extract_table",
            description="Extract structured data from HTML tables",
            schema=ExtractTableSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params.get("selector")
        headers = params.get("headers", True)
        format_type = params.get("format", "json")
        max_rows = params.get("max_rows")
        
        if selector:
            target = f"table matching '{selector}'"
        else:
            target = "all tables on the page"
        
        instructions = f"Extract data from {target} in {format_type} format"
        if headers:
            instructions += " (include headers)"
        if max_rows:
            instructions += f" (max {max_rows} rows)"
        
        return ToolResult(
            success=True,
            message=f"Table extraction prepared: {target}",
            data={
                "action": "extract_table",
                "selector": selector,
                "headers": headers,
                "format": format_type,
                "max_rows": max_rows,
                "instructions": instructions
            }
        )

class ExtractLinksTool(BaseTool):
    """Tool for extracting links from pages"""
    
    def __init__(self):
        super().__init__(
            name="extract_links",
            description="Extract links from the current page",
            schema=ExtractLinksSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params.get("selector", "a[href]")
        include_internal = params.get("include_internal", True)
        include_external = params.get("include_external", True)
        resolve_relative = params.get("resolve_relative", True)
        
        link_types = []
        if include_internal:
            link_types.append("internal")
        if include_external:
            link_types.append("external")
        
        instructions = f"Extract {' and '.join(link_types)} links from elements matching '{selector}'"
        if resolve_relative:
            instructions += " (resolve relative URLs)"
        
        return ToolResult(
            success=True,
            message=f"Link extraction prepared: {', '.join(link_types)} links",
            data={
                "action": "extract_links",
                "selector": selector,
                "include_internal": include_internal,
                "include_external": include_external,
                "resolve_relative": resolve_relative,
                "current_url": context.get("page_url"),
                "instructions": instructions
            }
        )

class SearchContentTool(BaseTool):
    """Tool for searching content within the current page"""
    
    def __init__(self):
        super().__init__(
            name="search_content",
            description="Search for specific content or patterns within the page",
            schema=SearchContentSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        query = params["query"]
        search_type = params.get("search_type", "text")
        case_sensitive = params.get("case_sensitive", False)
        max_results = params.get("max_results", 20)
        
        sensitivity = "case-sensitive" if case_sensitive else "case-insensitive"
        instructions = f"Search for '{query}' using {search_type} matching ({sensitivity}, max {max_results} results)"
        
        return ToolResult(
            success=True,
            message=f"Content search prepared: '{query}'",
            data={
                "action": "search_content",
                "query": query,
                "search_type": search_type,
                "case_sensitive": case_sensitive,
                "max_results": max_results,
                "instructions": instructions
            }
        )

class GetPageInfoSchema(ToolSchema):
    """Schema for getting page information"""
    include_title: bool = Field(default=True, description="Include page title")
    include_url: bool = Field(default=True, description="Include current URL")
    include_meta: bool = Field(default=True, description="Include meta tags")
    include_status: bool = Field(default=True, description="Include page load status")
    include_performance: bool = Field(default=False, description="Include performance metrics")

class GetPageInfoTool(BaseTool):
    """Tool for getting general page information"""
    
    def __init__(self):
        super().__init__(
            name="get_page_info",
            description="Get general information about the current page",
            schema=GetPageInfoSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        include_title = params.get("include_title", True)
        include_url = params.get("include_url", True)
        include_meta = params.get("include_meta", True)
        include_status = params.get("include_status", True)
        include_performance = params.get("include_performance", False)
        
        info_types = []
        if include_title:
            info_types.append("title")
        if include_url:
            info_types.append("URL")
        if include_meta:
            info_types.append("meta tags")
        if include_status:
            info_types.append("load status")
        if include_performance:
            info_types.append("performance metrics")
        
        instructions = f"Get page {', '.join(info_types)}"
        
        # Provide some context data if available
        page_info = {}
        if context.get("page_title") and include_title:
            page_info["title"] = context["page_title"]
        if context.get("page_url") and include_url:
            page_info["url"] = context["page_url"]
        
        return ToolResult(
            success=True,
            message=f"Page info extraction prepared: {', '.join(info_types)}",
            data={
                "action": "get_page_info",
                "include_title": include_title,
                "include_url": include_url,
                "include_meta": include_meta,
                "include_status": include_status,
                "include_performance": include_performance,
                "current_info": page_info,
                "instructions": instructions
            }
        )

# Helper function to register all extraction tools
def register_extraction_tools():
    """Register all extraction tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    tools = [
        (ExtractContentTool(), ToolType.EXTRACTION),
        (ExtractElementTool(), ToolType.EXTRACTION),
        (ExtractTableTool(), ToolType.EXTRACTION),
        (ExtractLinksTool(), ToolType.EXTRACTION),
        (SearchContentTool(), ToolType.EXTRACTION),
        (GetPageInfoTool(), ToolType.EXTRACTION),
    ]
    
    for tool, tool_type in tools:
        tool_registry.register(tool, tool_type)