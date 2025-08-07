#!/usr/bin/env python3
"""
Accessibility Tools for AI Browser
Integrates with Chrome DevTools Accessibility APIs for semantic element understanding
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, validator
from enum import Enum

from .base_tool import BaseTool, ToolSchema, ToolResult

class AccessibilityRole(str, Enum):
    """Common accessibility roles"""
    BUTTON = "button"
    LINK = "link"
    TEXTBOX = "textbox"
    HEADING = "heading"
    LISTITEM = "listitem"
    LIST = "list"
    NAVIGATION = "navigation"
    MAIN = "main"
    BANNER = "banner"
    CONTENTINFO = "contentinfo"
    FORM = "form"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    COMBOBOX = "combobox"
    TAB = "tab"
    TABPANEL = "tabpanel"
    DIALOG = "dialog"
    ALERT = "alert"

class GetAccessibilityTreeSchema(ToolSchema):
    """Schema for getting accessibility tree"""
    max_depth: int = Field(default=5, description="Maximum tree depth to traverse")
    include_invisible: bool = Field(default=False, description="Include invisible elements")
    filter_roles: Optional[List[str]] = Field(default=None, description="Filter by specific roles")
    root_selector: Optional[str] = Field(default=None, description="Root element selector (defaults to document)")

class FindByAccessibilitySchema(ToolSchema):
    """Schema for finding elements by accessibility properties"""
    role: Optional[str] = Field(default=None, description="Element role to find")
    name: Optional[str] = Field(default=None, description="Accessible name to match")
    description: Optional[str] = Field(default=None, description="Description to match")
    level: Optional[int] = Field(default=None, description="Heading level (for headings)")
    expanded: Optional[bool] = Field(default=None, description="Expanded state (for expandable elements)")
    max_results: int = Field(default=10, description="Maximum results to return")

class GetElementAccessibilitySchema(ToolSchema):
    """Schema for getting accessibility info for specific element"""
    selector: str = Field(description="Element selector")
    include_children: bool = Field(default=False, description="Include child elements accessibility info")

class GetAccessibilityTreeTool(BaseTool):
    """Tool for getting the page's accessibility tree"""
    
    def __init__(self):
        super().__init__(
            name="get_accessibility_tree",
            description="Get the accessibility tree of the page for semantic understanding",
            schema=GetAccessibilityTreeSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        max_depth = params.get("max_depth", 5)
        include_invisible = params.get("include_invisible", False)
        filter_roles = params.get("filter_roles")
        root_selector = params.get("root_selector")
        
        instructions = f"Get accessibility tree (depth: {max_depth}"
        if include_invisible:
            instructions += ", including invisible elements"
        if filter_roles:
            instructions += f", roles: {', '.join(filter_roles)}"
        if root_selector:
            instructions += f", root: {root_selector}"
        instructions += ")"
        
        return ToolResult(
            success=True,
            message=f"Accessibility tree query prepared (max depth: {max_depth})",
            data={
                "action": "get_accessibility_tree",
                "max_depth": max_depth,
                "include_invisible": include_invisible,
                "filter_roles": filter_roles,
                "root_selector": root_selector,
                "instructions": instructions
            },
            metadata={
                "requires_devtools": True,
                "api_domain": "Accessibility"
            }
        )

class FindByAccessibilityTool(BaseTool):
    """Tool for finding elements using accessibility properties"""
    
    def __init__(self):
        super().__init__(
            name="find_by_accessibility",
            description="Find elements using accessibility role, name, or description",
            schema=FindByAccessibilitySchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        role = params.get("role")
        name = params.get("name")
        description = params.get("description")
        level = params.get("level")
        expanded = params.get("expanded")
        max_results = params.get("max_results", 10)
        
        search_criteria = []
        if role:
            search_criteria.append(f"role='{role}'")
        if name:
            search_criteria.append(f"name='{name}'")
        if description:
            search_criteria.append(f"description='{description}'")
        if level is not None:
            search_criteria.append(f"level={level}")
        if expanded is not None:
            search_criteria.append(f"expanded={expanded}")
        
        criteria_text = ", ".join(search_criteria)
        instructions = f"Find up to {max_results} elements by accessibility: {criteria_text}"
        
        return ToolResult(
            success=True,
            message=f"Accessibility search prepared: {criteria_text}",
            data={
                "action": "find_by_accessibility",
                "role": role,
                "name": name,
                "description": description,
                "level": level,
                "expanded": expanded,
                "max_results": max_results,
                "instructions": instructions
            },
            metadata={
                "requires_devtools": True,
                "search_criteria": len(search_criteria)
            }
        )

class GetElementAccessibilityTool(BaseTool):
    """Tool for getting accessibility information for a specific element"""
    
    def __init__(self):
        super().__init__(
            name="get_element_accessibility",
            description="Get accessibility information for a specific element",
            schema=GetElementAccessibilitySchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        selector = params["selector"]
        include_children = params.get("include_children", False)
        
        instructions = f"Get accessibility info for element '{selector}'"
        if include_children:
            instructions += " (including children)"
        
        return ToolResult(
            success=True,
            message=f"Element accessibility query prepared: {selector}",
            data={
                "action": "get_element_accessibility",
                "selector": selector,
                "include_children": include_children,
                "instructions": instructions
            },
            metadata={
                "requires_devtools": True
            }
        )

class GetLandmarksSchema(ToolSchema):
    """Schema for getting page landmarks"""
    include_implicit: bool = Field(default=True, description="Include implicit landmarks")

class GetLandmarksTool(BaseTool):
    """Tool for getting page landmarks (navigation, main, banner, etc.)"""
    
    def __init__(self):
        super().__init__(
            name="get_landmarks",
            description="Get page landmarks for navigation and structure understanding",
            schema=GetLandmarksSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        include_implicit = params.get("include_implicit", True)
        
        landmark_roles = [
            AccessibilityRole.NAVIGATION.value,
            AccessibilityRole.MAIN.value, 
            AccessibilityRole.BANNER.value,
            AccessibilityRole.CONTENTINFO.value,
            "search",
            "complementary"
        ]
        
        instructions = f"Get page landmarks: {', '.join(landmark_roles)}"
        if include_implicit:
            instructions += " (including implicit landmarks)"
        
        return ToolResult(
            success=True,
            message="Page landmarks query prepared",
            data={
                "action": "get_landmarks",
                "landmark_roles": landmark_roles,
                "include_implicit": include_implicit,
                "instructions": instructions
            },
            metadata={
                "expected_landmarks": len(landmark_roles)
            }
        )

class GetHeadingsSchema(ToolSchema):
    """Schema for getting page headings"""
    min_level: int = Field(default=1, description="Minimum heading level")
    max_level: int = Field(default=6, description="Maximum heading level")
    include_hidden: bool = Field(default=False, description="Include hidden headings")

class GetHeadingsTool(BaseTool):
    """Tool for getting page heading structure"""
    
    def __init__(self):
        super().__init__(
            name="get_headings",
            description="Get page heading structure for content navigation",
            schema=GetHeadingsSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        min_level = params.get("min_level", 1)
        max_level = params.get("max_level", 6)
        include_hidden = params.get("include_hidden", False)
        
        instructions = f"Get headings (levels {min_level}-{max_level})"
        if include_hidden:
            instructions += " including hidden headings"
        
        return ToolResult(
            success=True,
            message=f"Headings query prepared (h{min_level}-h{max_level})",
            data={
                "action": "get_headings",
                "min_level": min_level,
                "max_level": max_level,
                "include_hidden": include_hidden,
                "instructions": instructions
            }
        )

class GetFormControlsSchema(ToolSchema):
    """Schema for getting form controls"""
    form_selector: Optional[str] = Field(default=None, description="Specific form to analyze")
    include_labels: bool = Field(default=True, description="Include associated labels")
    include_validation: bool = Field(default=True, description="Include validation info")

class GetFormControlsTool(BaseTool):
    """Tool for getting form controls and their accessibility info"""
    
    def __init__(self):
        super().__init__(
            name="get_form_controls",
            description="Get form controls with their accessibility labels and validation",
            schema=GetFormControlsSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        form_selector = params.get("form_selector")
        include_labels = params.get("include_labels", True)
        include_validation = params.get("include_validation", True)
        
        target = f"form '{form_selector}'" if form_selector else "all forms"
        instructions = f"Get form controls from {target}"
        
        features = []
        if include_labels:
            features.append("labels")
        if include_validation:
            features.append("validation")
        
        if features:
            instructions += f" (including {', '.join(features)})"
        
        return ToolResult(
            success=True,
            message=f"Form controls query prepared: {target}",
            data={
                "action": "get_form_controls",
                "form_selector": form_selector,
                "include_labels": include_labels,
                "include_validation": include_validation,
                "instructions": instructions
            }
        )

class GetInteractiveElementsSchema(ToolSchema):
    """Schema for getting interactive elements"""
    include_disabled: bool = Field(default=False, description="Include disabled elements")
    element_types: Optional[List[str]] = Field(default=None, description="Specific element types to include")

class GetInteractiveElementsTool(BaseTool):
    """Tool for getting all interactive elements on the page"""
    
    def __init__(self):
        super().__init__(
            name="get_interactive_elements",
            description="Get all interactive elements (buttons, links, form controls)",
            schema=GetInteractiveElementsSchema
        )
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        include_disabled = params.get("include_disabled", False)
        element_types = params.get("element_types")
        
        default_types = ["button", "link", "textbox", "combobox", "checkbox", "radio", "slider"]
        types_to_find = element_types or default_types
        
        instructions = f"Get interactive elements: {', '.join(types_to_find)}"
        if include_disabled:
            instructions += " (including disabled)"
        
        return ToolResult(
            success=True,
            message=f"Interactive elements query prepared: {len(types_to_find)} types",
            data={
                "action": "get_interactive_elements",
                "element_types": types_to_find,
                "include_disabled": include_disabled,
                "instructions": instructions
            }
        )

# Helper function to register all accessibility tools
def register_accessibility_tools():
    """Register all accessibility tools with the tool registry"""
    from .base_tool import tool_registry, ToolType
    
    # Create new tool type for accessibility
    accessibility_tools = [
        GetAccessibilityTreeTool(),
        FindByAccessibilityTool(),
        GetElementAccessibilityTool(),
        GetLandmarksTool(),
        GetHeadingsTool(),
        GetFormControlsTool(),
        GetInteractiveElementsTool(),
    ]
    
    for tool in accessibility_tools:
        tool_registry.register(tool, ToolType.EXTRACTION)  # Using EXTRACTION type for now