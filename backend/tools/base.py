"""
Base Tool Architecture for AI Browser
Inspired by BrowserOS-agent tool system but optimized for local AI processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, TypeVar, Generic
from pydantic import BaseModel, Field
from enum import Enum
import structlog
import asyncio
from datetime import datetime

logger = structlog.get_logger(__name__)

class ToolCategory(Enum):
    """Tool categories matching BrowserOS-agent architecture"""
    NAVIGATION = "navigation"
    INTERACTION = "interaction" 
    EXTRACTION = "extraction"
    PLANNING = "planning"
    VALIDATION = "validation"
    UTILITY = "utility"
    TAB_MANAGEMENT = "tab_management"

class ToolResult(BaseModel):
    """Structured tool execution result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time_ms: Optional[int] = None

class BrowserContext(BaseModel):
    """Browser context for tool execution"""
    current_url: Optional[str] = None
    current_tab_id: Optional[str] = None
    page_title: Optional[str] = None
    page_content: Optional[str] = None
    accessibility_tree: Optional[Dict[str, Any]] = None
    interactive_elements: Optional[List[Dict[str, Any]]] = None
    screenshot_path: Optional[str] = None
    user_intent: Optional[str] = None

T = TypeVar('T', bound=BaseModel)

class AIBrowserTool(ABC, Generic[T]):
    """
    Base class for all AI browser tools.
    Inspired by BrowserOS DynamicStructuredTool pattern but optimized for local AI.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        input_schema: type[T],
        requires_browser_context: bool = True,
        can_modify_browser_state: bool = False
    ):
        self.name = name
        self.description = description
        self.category = category
        self.input_schema = input_schema
        self.requires_browser_context = requires_browser_context
        self.can_modify_browser_state = can_modify_browser_state
        
    @abstractmethod
    async def execute(
        self, 
        params: T, 
        context: BrowserContext
    ) -> ToolResult:
        """Execute the tool with validated parameters and context"""
        pass
    
    def format_for_ai(self) -> Dict[str, Any]:
        """Format tool for AI consumption (LangChain style)"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "input_schema": self.input_schema.model_json_schema(),
            "modifies_state": self.can_modify_browser_state
        }
    
    def validate_input(self, raw_params: Dict[str, Any]) -> T:
        """Validate and parse input parameters"""
        try:
            return self.input_schema.model_validate(raw_params)
        except Exception as e:
            logger.error(f"Tool {self.name} input validation failed", error=str(e))
            raise ValueError(f"Invalid parameters for {self.name}: {str(e)}")
    
    async def safe_execute(
        self,
        raw_params: Dict[str, Any],
        context: BrowserContext,
        timeout_seconds: int = 30
    ) -> ToolResult:
        """Safely execute tool with validation, error handling, and timeout"""
        start_time = datetime.now()
        
        try:
            # Validate input
            validated_params = self.validate_input(raw_params)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.execute(validated_params, context),
                timeout=timeout_seconds
            )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = int(execution_time)
            
            logger.info(
                f"Tool executed successfully",
                tool_name=self.name,
                execution_time_ms=result.execution_time_ms,
                success=result.success
            )
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Tool {self.name} timed out after {timeout_seconds}s"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=f"Tool execution timed out",
                error=error_msg,
                execution_time_ms=timeout_seconds * 1000
            )
            
        except Exception as e:
            error_msg = f"Tool {self.name} execution failed: {str(e)}"
            logger.error(error_msg, error=str(e))
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolResult(
                success=False,
                message="Tool execution failed",
                error=error_msg,
                execution_time_ms=int(execution_time)
            )

class ToolRegistry:
    """Registry for all available AI browser tools"""
    
    def __init__(self):
        self.tools: Dict[str, AIBrowserTool] = {}
        self.tools_by_category: Dict[ToolCategory, List[AIBrowserTool]] = {}
        
    def register(self, tool: AIBrowserTool):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool
        
        if tool.category not in self.tools_by_category:
            self.tools_by_category[tool.category] = []
        self.tools_by_category[tool.category].append(tool)
        
        logger.info(f"Tool registered", tool=tool.name, category=tool.category.value)
    
    def get_tool(self, name: str) -> Optional[AIBrowserTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[AIBrowserTool]:
        """Get all tools in a category"""
        return self.tools_by_category.get(category, [])
    
    def get_all_tools(self) -> List[AIBrowserTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def format_tools_for_ai(self) -> List[Dict[str, Any]]:
        """Format all tools for AI consumption"""
        return [tool.format_for_ai() for tool in self.tools.values()]
    
    def get_tool_names(self) -> List[str]:
        """Get all tool names"""
        return list(self.tools.keys())

# Global tool registry instance
tool_registry = ToolRegistry()

class ToolExecutionEvent(BaseModel):
    """Event for tool execution progress"""
    tool_name: str
    stage: str  # "started", "executing", "completed", "failed"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class StreamingToolExecutor:
    """
    Executes tools with streaming progress updates.
    Inspired by BrowserOS EventProcessor pattern.
    """
    
    def __init__(self):
        self.event_handlers: List[callable] = []
        
    def add_event_handler(self, handler: callable):
        """Add event handler for tool execution events"""
        self.event_handlers.append(handler)
    
    async def emit_event(self, event: ToolExecutionEvent):
        """Emit tool execution event to all handlers"""
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler failed", error=str(e))
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: BrowserContext
    ) -> ToolResult:
        """Execute tool with streaming progress events"""
        
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found"
            await self.emit_event(ToolExecutionEvent(
                tool_name=tool_name,
                stage="failed",
                message=error_msg
            ))
            return ToolResult(success=False, message=error_msg)
        
        # Emit start event
        await self.emit_event(ToolExecutionEvent(
            tool_name=tool_name,
            stage="started",
            message=f"Starting {tool_name}",
            data={"params": params}
        ))
        
        # Execute tool
        await self.emit_event(ToolExecutionEvent(
            tool_name=tool_name,
            stage="executing", 
            message=f"Executing {tool_name}..."
        ))
        
        result = await tool.safe_execute(params, context)
        
        # Emit completion event
        if result.success:
            await self.emit_event(ToolExecutionEvent(
                tool_name=tool_name,
                stage="completed",
                message=f"{tool_name} completed successfully",
                data={"result": result.data, "execution_time_ms": result.execution_time_ms}
            ))
        else:
            await self.emit_event(ToolExecutionEvent(
                tool_name=tool_name,
                stage="failed", 
                message=f"{tool_name} failed: {result.error}",
                data={"error": result.error}
            ))
        
        return result

# Global streaming executor
streaming_executor = StreamingToolExecutor()