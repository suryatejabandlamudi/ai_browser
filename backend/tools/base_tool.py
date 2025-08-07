#!/usr/bin/env python3
"""
Base Tool System for AI Browser
Implements structured tools with validation and type safety
Based on BrowserOS architecture but adapted for local GPT-OSS processing
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError, Field
from enum import Enum
import json
import asyncio

import structlog

logger = structlog.get_logger(__name__)

class ToolResult(BaseModel):
    """Standardized tool execution result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolSchema(BaseModel):
    """Base schema for tool parameters"""
    pass

class BaseTool(ABC):
    """Abstract base class for all browser automation tools"""
    
    def __init__(self, name: str, description: str, schema: Type[ToolSchema]):
        self.name = name
        self.description = description
        self.schema = schema
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters and context"""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters against the tool's schema"""
        try:
            self.schema.model_validate(params)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for AI model including schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema.model_json_schema()
        }
    
    async def safe_execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute with validation and error handling"""
        try:
            # Validate parameters
            valid, error = self.validate_params(params)
            if not valid:
                return ToolResult(
                    success=False,
                    error=f"Parameter validation failed: {error}"
                )
            
            # Execute tool
            logger.info("Executing tool", tool=self.name, params=params)
            result = await self.execute(params, context)
            
            logger.info("Tool executed", 
                       tool=self.name, 
                       success=result.success,
                       message=result.message)
            
            return result
            
        except Exception as e:
            logger.error("Tool execution failed", tool=self.name, error=str(e))
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

class ToolType(Enum):
    """Categories of tools available"""
    NAVIGATION = "navigation"
    INTERACTION = "interaction" 
    EXTRACTION = "extraction"
    VISUAL = "visual"
    FORM = "form"
    WAIT = "wait"

@dataclass
class ToolExecutionContext:
    """Context passed to tool execution"""
    page_url: str
    page_content: Optional[str] = None
    page_title: Optional[str] = None
    viewport_size: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)

class ToolRegistry:
    """Registry for managing all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tools_by_type: Dict[ToolType, List[BaseTool]] = {}
    
    def register(self, tool: BaseTool, tool_type: ToolType = ToolType.INTERACTION):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool
        
        if tool_type not in self.tools_by_type:
            self.tools_by_type[tool_type] = []
        self.tools_by_type[tool_type].append(tool)
        
        logger.info("Tool registered", tool=tool.name, type=tool_type.value)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """Get all tools of a specific type"""
        return self.tools_by_type.get(tool_type, [])
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for AI model"""
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        return await tool.safe_execute(params, context)

# Global tool registry instance
tool_registry = ToolRegistry()

class ToolManager:
    """High-level tool management and execution"""
    
    def __init__(self, registry: ToolRegistry = tool_registry):
        self.registry = registry
    
    async def execute_tool_chain(self, 
                                tools: List[Dict[str, Any]], 
                                context: ToolExecutionContext) -> List[ToolResult]:
        """Execute a chain of tools in sequence"""
        results = []
        current_context = context.custom_data.copy()
        
        for tool_call in tools:
            tool_name = tool_call.get("name")
            tool_params = tool_call.get("parameters", {})
            
            if not tool_name:
                results.append(ToolResult(
                    success=False,
                    error="Tool name not specified"
                ))
                continue
            
            # Update context with previous results
            execution_context = {
                "page_url": context.page_url,
                "page_content": context.page_content,
                "page_title": context.page_title,
                "viewport_size": context.viewport_size,
                "previous_results": results,
                "chain_context": current_context
            }
            
            result = await self.registry.execute_tool(tool_name, tool_params, execution_context)
            results.append(result)
            
            # Stop chain if tool failed (unless configured to continue)
            if not result.success and tool_call.get("stop_on_failure", True):
                logger.warning("Tool chain stopped due to failure", 
                             tool=tool_name, 
                             error=result.error)
                break
            
            # Update context with result data
            if result.success and result.data:
                current_context.update(result.data)
        
        return results
    
    def get_tools_for_task(self, task_description: str) -> List[BaseTool]:
        """Suggest tools based on task description (simple keyword matching for now)"""
        task_lower = task_description.lower()
        suggested_tools = []
        
        # Navigation tools
        if any(word in task_lower for word in ['navigate', 'go to', 'visit', 'open']):
            suggested_tools.extend(self.registry.get_tools_by_type(ToolType.NAVIGATION))
        
        # Interaction tools
        if any(word in task_lower for word in ['click', 'type', 'enter', 'submit', 'press']):
            suggested_tools.extend(self.registry.get_tools_by_type(ToolType.INTERACTION))
        
        # Extraction tools
        if any(word in task_lower for word in ['extract', 'get', 'find', 'read', 'scrape']):
            suggested_tools.extend(self.registry.get_tools_by_type(ToolType.EXTRACTION))
        
        # Visual tools
        if any(word in task_lower for word in ['screenshot', 'image', 'capture', 'visual']):
            suggested_tools.extend(self.registry.get_tools_by_type(ToolType.VISUAL))
        
        # Form tools
        if any(word in task_lower for word in ['form', 'fill', 'input', 'submit', 'login']):
            suggested_tools.extend(self.registry.get_tools_by_type(ToolType.FORM))
        
        return list(set(suggested_tools))  # Remove duplicates