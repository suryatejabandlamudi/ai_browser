#!/usr/bin/env python3
"""
Structured AI Agent for Browser Automation
Uses the new tool system for reliable and validated browser interactions
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

import structlog

try:
    from tools import (
        get_tool_manager,
        create_tool_execution_context,
        ToolManager,
        ToolResult,
        ToolExecutionContext
    )
except ImportError:
    # Create dummy classes if tools aren't available
    class ToolManager:
        def get_available_tools(self): return {}
        async def execute_tool(self, name, params): return {"success": False, "error": "Tools not available"}
    
    class ToolResult:
        def __init__(self, success=False, message="", data=None, error=None):
            self.success = success
            self.message = message
            self.data = data
            self.error = error
    
    class ToolExecutionContext:
        def __init__(self, page_url="", page_content=""):
            self.page_url = page_url
            self.page_content = page_content
    
    def get_tool_manager():
        return ToolManager()
    
    def create_tool_execution_context(page_url="", page_content=""):
        return ToolExecutionContext(page_url, page_content)

logger = structlog.get_logger(__name__)

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Single tool execution
    MODERATE = "moderate"  # 2-3 tool executions
    COMPLEX = "complex"    # Multi-step planning required

@dataclass
class AgentResponse:
    """Structured response from the AI agent"""
    success: bool
    message: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[ToolResult]
    task_complexity: TaskComplexity
    metadata: Dict[str, Any]

class StructuredAgent:
    """AI agent that uses structured tools for browser automation"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.tool_manager = get_tool_manager()
        self.conversation_history = []
        
    async def process_request(self, 
                            user_request: str, 
                            page_context: Dict[str, Any]) -> AgentResponse:
        """Process a user request using structured tools"""
        
        logger.info("Processing structured request", request=user_request[:100])
        
        try:
            # Create execution context
            context = create_tool_execution_context(
                page_url=page_context.get("url", ""),
                page_content=page_context.get("content"),
                page_title=page_context.get("title"),
                viewport_size=page_context.get("viewport_size"),
                conversation_history=self.conversation_history[-5:]  # Last 5 interactions
            )
            
            # Classify task complexity
            complexity = await self._classify_complexity(user_request, page_context)
            
            # Generate tool calls based on complexity
            if complexity == TaskComplexity.SIMPLE:
                tool_calls = await self._generate_simple_tool_calls(user_request, context)
            elif complexity == TaskComplexity.MODERATE:
                tool_calls = await self._generate_moderate_tool_calls(user_request, context)
            else:  # COMPLEX
                tool_calls = await self._generate_complex_tool_calls(user_request, context)
            
            # Execute tool calls
            tool_results = await self._execute_tool_chain(tool_calls, context)
            
            # Generate response message
            response_message = await self._generate_response_message(
                user_request, tool_calls, tool_results, complexity
            )
            
            # Store in conversation history
            self.conversation_history.append({
                "user_request": user_request,
                "tool_calls": tool_calls,
                "tool_results": [r.model_dump() for r in tool_results],
                "response": response_message,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return AgentResponse(
                success=all(r.success for r in tool_results),
                message=response_message,
                tool_calls=tool_calls,
                tool_results=tool_results,
                task_complexity=complexity,
                metadata={
                    "total_tools": len(tool_calls),
                    "successful_tools": len([r for r in tool_results if r.success]),
                    "execution_time": sum(r.metadata.get("execution_time", 0) for r in tool_results)
                }
            )
            
        except Exception as e:
            logger.error("Structured agent processing failed", error=str(e))
            return AgentResponse(
                success=False,
                message=f"I encountered an error: {str(e)}",
                tool_calls=[],
                tool_results=[],
                task_complexity=TaskComplexity.SIMPLE,
                metadata={"error": str(e)}
            )
    
    async def _classify_complexity(self, 
                                 user_request: str, 
                                 page_context: Dict[str, Any]) -> TaskComplexity:
        """Classify the complexity of the user request"""
        
        prompt = f"""
        Analyze this browser automation request and classify its complexity:
        
        REQUEST: "{user_request}"
        PAGE: {page_context.get('url', 'unknown')}
        
        Classification rules:
        - SIMPLE: Single action (click button, extract text, navigate to URL, take screenshot)
        - MODERATE: 2-3 related actions (search then click result, fill form then submit)  
        - COMPLEX: Multi-step workflow with validation (online shopping, account setup, data collection)
        
        Respond with just one word: SIMPLE, MODERATE, or COMPLEX
        """
        
        try:
            response = await self.ai_client.chat(prompt, context={})
            classification = response["content"].strip().upper()
            
            if "SIMPLE" in classification:
                return TaskComplexity.SIMPLE
            elif "MODERATE" in classification:
                return TaskComplexity.MODERATE
            elif "COMPLEX" in classification:
                return TaskComplexity.COMPLEX
            else:
                return TaskComplexity.SIMPLE  # Default fallback
                
        except Exception as e:
            logger.warning("Complexity classification failed", error=str(e))
            return TaskComplexity.SIMPLE
    
    async def _generate_simple_tool_calls(self, 
                                        user_request: str, 
                                        context: ToolExecutionContext) -> List[Dict[str, Any]]:
        """Generate tool calls for simple tasks"""
        
        # Get available tools
        tool_definitions = self.tool_manager.registry.get_tool_definitions()
        
        prompt = f"""
        You are a browser automation expert. Generate a single tool call to fulfill this request:
        
        REQUEST: "{user_request}"
        CURRENT PAGE: {context.page_url}
        
        AVAILABLE TOOLS:
        {json.dumps(tool_definitions, indent=2)}
        
        Respond with a JSON array containing exactly ONE tool call:
        
        [
            {{
                "name": "tool_name",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }}
            }}
        ]
        
        IMPORTANT: Respond with ONLY the JSON array, no other text.
        """
        
        return await self._extract_tool_calls_from_ai_response(prompt)
    
    async def _generate_moderate_tool_calls(self, 
                                          user_request: str, 
                                          context: ToolExecutionContext) -> List[Dict[str, Any]]:
        """Generate tool calls for moderate complexity tasks"""
        
        tool_definitions = self.tool_manager.registry.get_tool_definitions()
        
        prompt = f"""
        You are a browser automation expert. Generate 2-3 tool calls to fulfill this request:
        
        REQUEST: "{user_request}"
        CURRENT PAGE: {context.page_url}
        
        AVAILABLE TOOLS:
        {json.dumps(tool_definitions, indent=2)}
        
        Plan the sequence of 2-3 tools needed. Consider:
        - What actions are required?
        - What order should they be executed?
        - Do I need to wait for page changes?
        
        Respond with a JSON array containing 2-3 tool calls:
        
        [
            {{
                "name": "first_tool",
                "parameters": {{ ... }}
            }},
            {{
                "name": "second_tool", 
                "parameters": {{ ... }}
            }}
        ]
        
        IMPORTANT: Respond with ONLY the JSON array, no other text.
        """
        
        return await self._extract_tool_calls_from_ai_response(prompt)
    
    async def _generate_complex_tool_calls(self, 
                                         user_request: str, 
                                         context: ToolExecutionContext) -> List[Dict[str, Any]]:
        """Generate tool calls for complex multi-step tasks"""
        
        tool_definitions = self.tool_manager.registry.get_tool_definitions()
        
        prompt = f"""
        You are a browser automation expert. Create a detailed plan for this complex task:
        
        REQUEST: "{user_request}"
        CURRENT PAGE: {context.page_url}
        
        AVAILABLE TOOLS:
        {json.dumps(tool_definitions, indent=2)}
        
        This is a complex task requiring multiple steps with potential validation.
        Consider:
        1. Breaking down into logical phases
        2. Adding waits for page loads
        3. Extracting information to validate progress
        4. Error recovery strategies
        
        Generate 3-8 tool calls in logical sequence:
        
        [
            {{
                "name": "navigate", 
                "parameters": {{ "url": "https://example.com" }}
            }},
            {{
                "name": "wait_for_page_load",
                "parameters": {{ "event": "load" }}
            }},
            {{
                "name": "extract_content",
                "parameters": {{ "extract_type": "text" }}
            }}
        ]
        
        IMPORTANT: Respond with ONLY the JSON array, no other text.
        """
        
        return await self._extract_tool_calls_from_ai_response(prompt)
    
    async def _extract_tool_calls_from_ai_response(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract tool calls from AI response with robust parsing"""
        
        try:
            response = await self.ai_client.chat(prompt, context={})
            content = response["content"].strip()
            
            # Try to extract JSON from the response
            if not content.startswith('['):
                # Look for JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    raise ValueError("No JSON array found in response")
            
            tool_calls = json.loads(content)
            
            if not isinstance(tool_calls, list):
                raise ValueError("Response is not a JSON array")
            
            # Validate tool calls
            validated_calls = []
            for call in tool_calls:
                if isinstance(call, dict) and "name" in call:
                    validated_calls.append({
                        "name": call["name"],
                        "parameters": call.get("parameters", {})
                    })
            
            return validated_calls
            
        except Exception as e:
            logger.error("Failed to extract tool calls", error=str(e))
            # Fallback to extract_content as a safe default
            return [{
                "name": "extract_content",
                "parameters": {"extract_type": "text"}
            }]
    
    async def _execute_tool_chain(self, 
                                tool_calls: List[Dict[str, Any]], 
                                context: ToolExecutionContext) -> List[ToolResult]:
        """Execute a chain of tool calls"""
        
        return await self.tool_manager.execute_tool_chain(tool_calls, context)
    
    async def _generate_response_message(self, 
                                       user_request: str,
                                       tool_calls: List[Dict[str, Any]],
                                       tool_results: List[ToolResult],
                                       complexity: TaskComplexity) -> str:
        """Generate a human-readable response message"""
        
        # Count successful vs failed tools
        successful = len([r for r in tool_results if r.success])
        total = len(tool_results)
        
        if successful == 0:
            return "I wasn't able to complete your request. Please check if the page is accessible and try again."
        
        if successful == total:
            if complexity == TaskComplexity.SIMPLE:
                return f"I've completed your request: {user_request}"
            else:
                action_summary = ", ".join([call["name"] for call in tool_calls])
                return f"I've completed your request by performing these actions: {action_summary}"
        else:
            return f"I partially completed your request ({successful}/{total} actions successful). Some actions may have failed due to page changes or element availability."
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation history"""
        
        if not self.conversation_history:
            return {"total_interactions": 0}
        
        return {
            "total_interactions": len(self.conversation_history),
            "successful_interactions": len([h for h in self.conversation_history 
                                          if all(r.get("success", False) for r in h.get("tool_results", []))]),
            "most_used_tools": self._get_most_used_tools(),
            "last_interaction": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def _get_most_used_tools(self) -> Dict[str, int]:
        """Get statistics on most frequently used tools"""
        
        tool_counts = {}
        for interaction in self.conversation_history:
            for tool_call in interaction.get("tool_calls", []):
                tool_name = tool_call.get("name")
                if tool_name:
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        # Sort by usage count
        return dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))