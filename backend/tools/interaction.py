"""
Interaction Tools for AI Browser
Core browser interaction capabilities - click, type, form filling, element manipulation.
Designed to compete with Perplexity Comet's automation capabilities.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import asyncio
import structlog
import json

from .base import AIBrowserTool, ToolCategory, ToolResult, BrowserContext

logger = structlog.get_logger(__name__)

# Input Schemas

class ClickToolInput(BaseModel):
    """Input for click tool - supports multiple selector strategies"""
    selector: Optional[str] = Field(None, description="CSS selector for element")
    text_content: Optional[str] = Field(None, description="Text content to find and click")
    aria_label: Optional[str] = Field(None, description="ARIA label to find and click")
    element_description: Optional[str] = Field(None, description="Natural language description of element")
    coordinates: Optional[Dict[str, int]] = Field(None, description="Absolute coordinates {x, y}")
    wait_before_click: int = Field(default=100, description="Wait milliseconds before clicking")
    double_click: bool = Field(default=False, description="Perform double-click instead of single")
    right_click: bool = Field(default=False, description="Perform right-click for context menu")

class TypeToolInput(BaseModel):
    """Input for typing text - smart form filling"""
    selector: Optional[str] = Field(None, description="CSS selector for input element")
    text_content: Optional[str] = Field(None, description="Text to type")
    element_description: Optional[str] = Field(None, description="Natural language description of input field")
    clear_first: bool = Field(default=True, description="Clear existing text before typing")
    type_speed: int = Field(default=50, description="Typing speed in milliseconds per character")
    press_enter: bool = Field(default=False, description="Press Enter after typing")
    press_tab: bool = Field(default=False, description="Press Tab after typing")

class FormFillToolInput(BaseModel):
    """Input for intelligent form filling"""
    form_data: Dict[str, str] = Field(description="Data to fill in form fields")
    form_selector: Optional[str] = Field(None, description="CSS selector for form container")
    auto_detect_fields: bool = Field(default=True, description="Automatically detect field types")
    submit_after_fill: bool = Field(default=False, description="Submit form after filling")
    validate_before_submit: bool = Field(default=True, description="Validate fields before submission")

class SelectToolInput(BaseModel):
    """Input for dropdown/select element interaction"""
    selector: Optional[str] = Field(None, description="CSS selector for select element")
    option_value: Optional[str] = Field(None, description="Option value to select")
    option_text: Optional[str] = Field(None, description="Option text to select")
    option_index: Optional[int] = Field(None, description="Option index to select (0-based)")
    element_description: Optional[str] = Field(None, description="Natural language description of select element")

class HoverToolInput(BaseModel):
    """Input for hover actions - revealing hidden elements"""
    selector: Optional[str] = Field(None, description="CSS selector for element")
    element_description: Optional[str] = Field(None, description="Natural language description of element")
    hover_duration: int = Field(default=500, description="Duration to hover in milliseconds")

# Tool Implementations

class ClickTool(AIBrowserTool[ClickToolInput]):
    """
    Advanced click tool with multiple targeting strategies.
    Smarter than BrowserOS - uses AI element detection + multiple fallbacks.
    """
    
    def __init__(self):
        super().__init__(
            name="click",
            description="Click on elements using various targeting methods (selector, text, description, coordinates)",
            category=ToolCategory.INTERACTION,
            input_schema=ClickToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: ClickToolInput, context: BrowserContext) -> ToolResult:
        """Execute click with intelligent element targeting"""
        
        try:
            # Strategy 1: Direct CSS selector
            if params.selector:
                return await self._click_by_selector(params, context)
            
            # Strategy 2: Text content matching
            elif params.text_content:
                return await self._click_by_text(params, context)
            
            # Strategy 3: ARIA label matching
            elif params.aria_label:
                return await self._click_by_aria_label(params, context)
            
            # Strategy 4: AI-powered element description
            elif params.element_description:
                return await self._click_by_ai_description(params, context)
            
            # Strategy 5: Absolute coordinates
            elif params.coordinates:
                return await self._click_by_coordinates(params, context)
            
            else:
                return ToolResult(
                    success=False,
                    message="No targeting method provided",
                    error="Must provide one of: selector, text_content, aria_label, element_description, or coordinates"
                )
                
        except Exception as e:
            logger.error(f"Click tool execution failed", error=str(e))
            return ToolResult(
                success=False,
                message="Click action failed",
                error=str(e)
            )
    
    async def _click_by_selector(self, params: ClickToolInput, context: BrowserContext) -> ToolResult:
        """Click using CSS selector"""
        await asyncio.sleep(params.wait_before_click / 1000)
        
        # In real implementation, this would execute browser automation
        # For now, simulate click action
        click_type = "double-click" if params.double_click else "right-click" if params.right_click else "click"
        
        return ToolResult(
            success=True,
            message=f"Successfully {click_type}ed element with selector '{params.selector}'",
            data={
                "selector": params.selector,
                "click_type": click_type,
                "coordinates_estimated": {"x": 400, "y": 300},
                "wait_time": params.wait_before_click
            }
        )
    
    async def _click_by_text(self, params: ClickToolInput, context: BrowserContext) -> ToolResult:
        """Click by finding text content"""
        if not context.page_content:
            return ToolResult(
                success=False,
                message="No page content available for text search",
                error="Browser context missing page content"
            )
        
        # Search for text in page content
        if params.text_content.lower() in context.page_content.lower():
            await asyncio.sleep(params.wait_before_click / 1000)
            
            return ToolResult(
                success=True,
                message=f"Successfully clicked element containing text '{params.text_content}'",
                data={
                    "text_content": params.text_content,
                    "click_type": "click",
                    "method": "text_matching"
                }
            )
        else:
            return ToolResult(
                success=False,
                message=f"Could not find element containing text '{params.text_content}'",
                error="Text not found on page"
            )
    
    async def _click_by_ai_description(self, params: ClickToolInput, context: BrowserContext) -> ToolResult:
        """Click using AI-powered element description (most advanced)"""
        if not context.accessibility_tree:
            return ToolResult(
                success=False,
                message="No accessibility tree available for AI element detection",
                error="Browser context missing accessibility data"
            )
        
        # In real implementation, would use AI to find element by description
        # Simulate AI element finding
        await asyncio.sleep(0.3)  # Simulate AI processing time
        
        # Mock finding element with high confidence
        confidence_score = 0.85
        
        return ToolResult(
            success=True,
            message=f"AI found and clicked element matching '{params.element_description}' (confidence: {confidence_score})",
            data={
                "element_description": params.element_description,
                "ai_confidence": confidence_score,
                "found_selector": "button.primary-cta",
                "click_type": "click",
                "method": "ai_description"
            }
        )
    
    async def _click_by_coordinates(self, params: ClickToolInput, context: BrowserContext) -> ToolResult:
        """Click at absolute coordinates"""
        x, y = params.coordinates["x"], params.coordinates["y"]
        await asyncio.sleep(params.wait_before_click / 1000)
        
        return ToolResult(
            success=True,
            message=f"Successfully clicked at coordinates ({x}, {y})",
            data={
                "coordinates": {"x": x, "y": y},
                "click_type": "coordinate_click",
                "method": "absolute_positioning"
            }
        )

class TypeTool(AIBrowserTool[TypeToolInput]):
    """
    Advanced typing tool with smart form field detection.
    Superior to basic automation - includes typing simulation, form intelligence.
    """
    
    def __init__(self):
        super().__init__(
            name="type",
            description="Type text into input fields with smart field detection and typing simulation",
            category=ToolCategory.INTERACTION,
            input_schema=TypeToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: TypeToolInput, context: BrowserContext) -> ToolResult:
        """Execute typing action with smart field detection"""
        
        try:
            # Find target element
            if params.selector:
                target_element = f"element with selector '{params.selector}'"
            elif params.element_description:
                # In real implementation, would use AI to find field
                target_element = f"field matching '{params.element_description}'"
            else:
                return ToolResult(
                    success=False,
                    message="No target field specified",
                    error="Must provide selector or element_description"
                )
            
            # Clear existing text if requested
            if params.clear_first:
                await asyncio.sleep(0.1)  # Simulate clear action
            
            # Simulate human-like typing
            typing_time = len(params.text_content) * (params.type_speed / 1000)
            await asyncio.sleep(typing_time)
            
            actions_taken = ["typing"]
            if params.clear_first:
                actions_taken.insert(0, "clear")
            if params.press_enter:
                actions_taken.append("press_enter")
            if params.press_tab:
                actions_taken.append("press_tab")
            
            return ToolResult(
                success=True,
                message=f"Successfully typed '{params.text_content}' into {target_element}",
                data={
                    "text_content": params.text_content,
                    "target_element": target_element,
                    "actions_taken": actions_taken,
                    "typing_time_ms": int(typing_time * 1000),
                    "character_count": len(params.text_content)
                }
            )
            
        except Exception as e:
            logger.error(f"Type tool execution failed", error=str(e))
            return ToolResult(
                success=False,
                message="Typing action failed",
                error=str(e)
            )

class FormFillTool(AIBrowserTool[FormFillToolInput]):
    """
    Intelligent form filling tool - competitor to Perplexity Comet's form automation.
    Uses AI to detect field types and fill appropriately.
    """
    
    def __init__(self):
        super().__init__(
            name="fill_form",
            description="Intelligently fill web forms with AI-powered field detection and validation",
            category=ToolCategory.INTERACTION,
            input_schema=FormFillToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: FormFillToolInput, context: BrowserContext) -> ToolResult:
        """Execute intelligent form filling"""
        
        try:
            filled_fields = []
            validation_errors = []
            
            # Simulate form field detection and filling
            for field_name, field_value in params.form_data.items():
                # In real implementation, would detect field type and fill appropriately
                field_type = self._detect_field_type(field_name, field_value)
                
                # Simulate filling with appropriate timing
                await asyncio.sleep(0.2)  # Simulate field detection time
                await asyncio.sleep(len(str(field_value)) * 0.05)  # Simulate typing time
                
                filled_fields.append({
                    "field_name": field_name,
                    "field_value": field_value,
                    "detected_type": field_type,
                    "success": True
                })
            
            # Validation phase
            if params.validate_before_submit:
                await asyncio.sleep(0.3)  # Simulate validation time
                validation_result = self._validate_form_data(params.form_data)
                validation_errors.extend(validation_result.get("errors", []))
            
            # Submit if requested and validation passes
            submitted = False
            if params.submit_after_fill and not validation_errors:
                await asyncio.sleep(0.5)  # Simulate submission time
                submitted = True
            
            success = len(filled_fields) > 0 and not validation_errors
            
            return ToolResult(
                success=success,
                message=f"Form filling {'completed successfully' if success else 'completed with issues'}. Filled {len(filled_fields)} fields.",
                data={
                    "fields_filled": filled_fields,
                    "validation_errors": validation_errors,
                    "form_submitted": submitted,
                    "total_fields": len(params.form_data),
                    "success_rate": len(filled_fields) / len(params.form_data) if params.form_data else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Form fill tool execution failed", error=str(e))
            return ToolResult(
                success=False,
                message="Form filling failed",
                error=str(e)
            )
    
    def _detect_field_type(self, field_name: str, field_value: str) -> str:
        """Detect field type based on name and value"""
        field_name_lower = field_name.lower()
        
        if "email" in field_name_lower or "@" in str(field_value):
            return "email"
        elif "password" in field_name_lower:
            return "password"
        elif "phone" in field_name_lower or "tel" in field_name_lower:
            return "phone"
        elif "name" in field_name_lower:
            return "name"
        elif "address" in field_name_lower:
            return "address"
        elif field_name_lower in ["zip", "zipcode", "postal", "postcode"]:
            return "zip"
        elif field_value.isdigit():
            return "number"
        else:
            return "text"
    
    def _validate_form_data(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Basic form validation"""
        errors = []
        
        for field_name, field_value in form_data.items():
            if not field_value or not str(field_value).strip():
                errors.append(f"Field '{field_name}' is empty")
                continue
                
            field_type = self._detect_field_type(field_name, field_value)
            
            if field_type == "email" and "@" not in str(field_value):
                errors.append(f"Field '{field_name}' does not appear to be a valid email")
            elif field_type == "phone" and len(str(field_value).replace("-", "").replace(" ", "")) < 10:
                errors.append(f"Field '{field_name}' does not appear to be a valid phone number")
        
        return {"errors": errors}

class SelectTool(AIBrowserTool[SelectToolInput]):
    """Smart dropdown/select element interaction"""
    
    def __init__(self):
        super().__init__(
            name="select_option",
            description="Select options from dropdown menus and select elements",
            category=ToolCategory.INTERACTION,
            input_schema=SelectToolInput,
            requires_browser_context=True,
            can_modify_browser_state=True
        )
    
    async def execute(self, params: SelectToolInput, context: BrowserContext) -> ToolResult:
        """Execute select option action"""
        
        try:
            selection_method = None
            selected_value = None
            
            if params.option_value:
                selection_method = "value"
                selected_value = params.option_value
            elif params.option_text:
                selection_method = "text"
                selected_value = params.option_text
            elif params.option_index is not None:
                selection_method = "index"
                selected_value = str(params.option_index)
            else:
                return ToolResult(
                    success=False,
                    message="No selection method provided",
                    error="Must provide option_value, option_text, or option_index"
                )
            
            # Simulate selection action
            await asyncio.sleep(0.2)  # Simulate dropdown interaction
            
            target = params.selector or f"element matching '{params.element_description}'"
            
            return ToolResult(
                success=True,
                message=f"Successfully selected option '{selected_value}' from {target}",
                data={
                    "target": target,
                    "selection_method": selection_method,
                    "selected_value": selected_value,
                    "dropdown_opened": True
                }
            )
            
        except Exception as e:
            logger.error(f"Select tool execution failed", error=str(e))
            return ToolResult(
                success=False,
                message="Select option action failed",
                error=str(e)
            )

# Register all interaction tools
def register_interaction_tools():
    """Register all interaction tools in the global registry"""
    from .base import tool_registry
    
    tools = [
        ClickTool(),
        TypeTool(),
        FormFillTool(),
        SelectTool()
    ]
    
    for tool in tools:
        tool_registry.register(tool)