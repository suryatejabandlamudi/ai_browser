"""
Rolling Horizon Planning Agent for AI Browser
Advanced AI agent with BrowserOS-inspired architecture but superior local processing.

This is the core intelligence that makes our AI browser competitive with Perplexity Comet.
"""

from typing import Dict, Any, List, Optional, AsyncIterator, Callable
import asyncio
import structlog
from datetime import datetime
from enum import Enum
import json

from ai_client import AIClient
from tools import tool_registry, streaming_executor, BrowserContext, ToolResult
from tools.planning import TaskPlan, TaskStep

logger = structlog.get_logger(__name__)

class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"

class StreamingEvent:
    """Event for streaming updates to UI"""
    def __init__(self, event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }

class RollingHorizonAgent:
    """
    Advanced AI agent with rolling-horizon planning.
    
    Key advantages over cloud-based competitors:
    1. 100% local processing (faster, private)
    2. Sophisticated planning with validation loops
    3. Real-time streaming updates
    4. Advanced error recovery
    5. Apple Silicon optimized inference
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.state = AgentState.IDLE
        self.current_plan: Optional[TaskPlan] = None
        self.execution_context: Dict[str, Any] = {}
        self.event_handlers: List[Callable] = []
        
        # Rolling horizon parameters (inspired by BrowserOS)
        self.planning_horizon = 5  # Plan 5 steps ahead
        self.max_replanning_attempts = 3
        self.confidence_threshold = 0.7
        
        logger.info("Rolling Horizon Agent initialized", 
                   tools_available=len(tool_registry.get_all_tools()))
    
    def add_event_handler(self, handler: Callable):
        """Add handler for streaming events"""
        self.event_handlers.append(handler)
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit streaming event to all handlers"""
        event = StreamingEvent(event_type, data)
        
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error("Event handler failed", error=str(e))
    
    async def execute_task(
        self, 
        user_message: str, 
        browser_context: BrowserContext,
        stream_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute user task with rolling-horizon planning.
        This is the main entry point for AI browser automation.
        """
        
        if stream_handler:
            self.add_event_handler(stream_handler)
        
        try:
            self.state = AgentState.THINKING
            await self.emit_event("agent_state_change", {"state": self.state.value})
            await self.emit_event("thinking_started", {"message": "Analyzing your request..."})
            
            # Phase 1: Task Classification
            classification_result = await self._classify_task(user_message, browser_context)
            task_complexity = classification_result["classification"]
            
            await self.emit_event("thinking_update", {
                "stage": "classification",
                "result": f"Task classified as '{task_complexity}'"
            })
            
            # Phase 2: Execution Strategy Selection
            if task_complexity == "simple":
                result = await self._execute_simple_task(user_message, browser_context)
            else:
                result = await self._execute_complex_task(user_message, browser_context, task_complexity)
            
            self.state = AgentState.COMPLETED if result["success"] else AgentState.FAILED
            await self.emit_event("agent_state_change", {"state": self.state.value})
            
            return result
            
        except Exception as e:
            logger.error("Task execution failed", error=str(e))
            self.state = AgentState.FAILED
            await self.emit_event("agent_state_change", {"state": self.state.value})
            await self.emit_event("execution_failed", {"error": str(e)})
            
            return {
                "success": False,
                "message": "Task execution failed",
                "error": str(e)
            }
    
    async def _classify_task(self, user_message: str, context: BrowserContext) -> Dict[str, Any]:
        """Classify task complexity using our classification tool"""
        
        classification_tool = tool_registry.get_tool("classify_task")
        if not classification_tool:
            # Fallback classification
            return {"classification": "simple", "confidence": 0.5}
        
        params = {
            "user_message": user_message,
            "page_context": context.page_content[:500] if context.page_content else None,
            "page_url": context.current_url
        }
        
        result = await classification_tool.safe_execute(params, context)
        return result.data if result.success else {"classification": "simple"}
    
    async def _execute_simple_task(self, user_message: str, context: BrowserContext) -> Dict[str, Any]:
        """Execute simple, single-step tasks directly"""
        
        await self.emit_event("execution_started", {
            "strategy": "direct_execution",
            "message": "Executing single action..."
        })
        
        # Use AI to determine the best tool for this task
        tool_selection = await self._select_tool_for_task(user_message, context)
        
        if not tool_selection["success"]:
            return {
                "success": False,
                "message": "Could not determine appropriate action",
                "error": tool_selection.get("error")
            }
        
        # Execute the selected tool
        tool_name = tool_selection["tool_name"]
        tool_params = tool_selection["parameters"]
        
        await self.emit_event("tool_execution_started", {
            "tool_name": tool_name,
            "parameters": tool_params
        })
        
        result = await streaming_executor.execute_tool(tool_name, tool_params, context)
        
        await self.emit_event("tool_execution_completed", {
            "tool_name": tool_name,
            "success": result.success,
            "message": result.message
        })
        
        return {
            "success": result.success,
            "message": result.message,
            "strategy": "direct_execution",
            "tool_used": tool_name,
            "result": result.data
        }
    
    async def _execute_complex_task(
        self, 
        user_message: str, 
        context: BrowserContext, 
        task_complexity: str
    ) -> Dict[str, Any]:
        """Execute complex tasks using rolling-horizon planning"""
        
        self.state = AgentState.PLANNING
        await self.emit_event("agent_state_change", {"state": self.state.value})
        await self.emit_event("planning_started", {
            "strategy": "rolling_horizon",
            "message": "Creating execution plan..."
        })
        
        # Create initial plan
        plan_result = await self._create_task_plan(user_message, context, task_complexity)
        
        if not plan_result["success"]:
            return {
                "success": False,
                "message": "Failed to create execution plan",
                "error": plan_result.get("error")
            }
        
        self.current_plan = TaskPlan.model_validate(plan_result["data"]["plan"])
        
        await self.emit_event("plan_created", {
            "plan_id": self.current_plan.id,
            "steps": len(self.current_plan.steps),
            "estimated_duration": self.current_plan.estimated_duration
        })
        
        # Execute plan with rolling-horizon strategy
        execution_result = await self._execute_plan_with_horizons()
        
        return execution_result
    
    async def _create_task_plan(
        self, 
        user_message: str, 
        context: BrowserContext, 
        complexity: str
    ) -> Dict[str, Any]:
        """Create detailed task execution plan"""
        
        planner_tool = tool_registry.get_tool("plan_task")
        if not planner_tool:
            return {"success": False, "error": "Planning tool not available"}
        
        params = {
            "user_intent": user_message,
            "task_complexity": complexity,
            "page_context": context.page_content[:1000] if context.page_content else None,
            "available_tools": tool_registry.get_tool_names(),
            "planning_horizon": self.planning_horizon
        }
        
        result = await planner_tool.safe_execute(params, context)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error if not result.success else None
        }
    
    async def _execute_plan_with_horizons(self) -> Dict[str, Any]:
        """
        Execute plan using rolling-horizon strategy.
        This is where we compete with BrowserOS sophistication.
        """
        
        self.state = AgentState.EXECUTING
        await self.emit_event("agent_state_change", {"state": self.state.value})
        
        executed_steps = []
        replanning_count = 0
        
        while self.current_plan.current_step < len(self.current_plan.steps):
            step = self.current_plan.steps[self.current_plan.current_step]
            
            await self.emit_event("step_execution_started", {
                "step_id": step.id,
                "step_number": self.current_plan.current_step + 1,
                "total_steps": len(self.current_plan.steps),
                "description": step.description
            })
            
            # Execute step
            step_result = await self._execute_step_with_validation(step)
            
            if step_result["success"]:
                step.status = "completed"
                executed_steps.append(step_result)
                self.current_plan.current_step += 1
                
                await self.emit_event("step_completed", {
                    "step_id": step.id,
                    "result": step_result["message"]
                })
                
            else:
                step.status = "failed"
                step.retry_count += 1
                
                await self.emit_event("step_failed", {
                    "step_id": step.id,
                    "error": step_result["error"],
                    "retry_count": step.retry_count
                })
                
                # Retry logic
                if step.retry_count <= step.max_retries:
                    await self.emit_event("step_retrying", {
                        "step_id": step.id,
                        "retry_attempt": step.retry_count
                    })
                    continue
                
                # Replanning logic
                if replanning_count < self.max_replanning_attempts:
                    await self.emit_event("replanning_started", {
                        "reason": "Step execution failed",
                        "failed_step": step.description
                    })
                    
                    replan_success = await self._replan_from_failure(step, step_result["error"])
                    
                    if replan_success:
                        replanning_count += 1
                        continue
                
                # Complete failure
                return {
                    "success": False,
                    "message": f"Task failed at step: {step.description}",
                    "executed_steps": executed_steps,
                    "failed_step": step.description,
                    "error": step_result["error"]
                }
        
        # All steps completed successfully
        return {
            "success": True,
            "message": "Task completed successfully",
            "strategy": "rolling_horizon_planning",
            "executed_steps": executed_steps,
            "total_steps": len(self.current_plan.steps),
            "replanning_count": replanning_count
        }
    
    async def _execute_step_with_validation(self, step: TaskStep) -> Dict[str, Any]:
        """Execute step with validation"""
        
        # Execute the tool
        tool_result = await streaming_executor.execute_tool(
            step.tool_name, 
            step.parameters, 
            BrowserContext()  # In real implementation, would use current context
        )
        
        if not tool_result.success:
            return {
                "success": False,
                "error": tool_result.error,
                "tool_result": tool_result
            }
        
        # Validate step execution
        validator_tool = tool_registry.get_tool("validate_step")
        if validator_tool:
            validation_params = {
                "step": step,
                "execution_result": tool_result.model_dump(),
                "expected_outcome": step.expected_outcome
            }
            
            validation_result = await validator_tool.safe_execute(
                validation_params, 
                BrowserContext()
            )
            
            if validation_result.success and validation_result.data.get("confidence", 0) > self.confidence_threshold:
                return {
                    "success": True,
                    "message": tool_result.message,
                    "validation": validation_result.data,
                    "tool_result": tool_result
                }
            else:
                return {
                    "success": False,
                    "error": "Validation failed - expected outcome not achieved",
                    "validation": validation_result.data if validation_result.success else None,
                    "tool_result": tool_result
                }
        
        # No validation available - trust tool result
        return {
            "success": True,
            "message": tool_result.message,
            "tool_result": tool_result
        }
    
    async def _select_tool_for_task(self, user_message: str, context: BrowserContext) -> Dict[str, Any]:
        """Use AI to select the best tool for a task"""
        
        # Create prompt for tool selection
        available_tools = tool_registry.format_tools_for_ai()
        
        prompt = f"""
        User Request: {user_message}
        
        Available Tools:
        {json.dumps(available_tools, indent=2)}
        
        Select the most appropriate tool and provide parameters.
        
        Response format:
        {{
            "tool_name": "selected_tool_name",
            "parameters": {{"param1": "value1"}},
            "reasoning": "why this tool was selected"
        }}
        """
        
        try:
            # Use local AI to select tool
            ai_response = await self.ai_client.chat(prompt)
            
            # Parse AI response (in real implementation, would use structured output)
            # For now, return a reasonable default
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ["click", "press", "tap"]):
                return {
                    "success": True,
                    "tool_name": "click",
                    "parameters": {"element_description": user_message},
                    "reasoning": "User wants to click something"
                }
            elif any(word in user_lower for word in ["type", "enter", "input"]):
                return {
                    "success": True,
                    "tool_name": "type",
                    "parameters": {"element_description": "input field", "text_content": ""},
                    "reasoning": "User wants to type something"
                }
            elif any(word in user_lower for word in ["navigate", "go to", "visit"]):
                return {
                    "success": True,
                    "tool_name": "navigate", 
                    "parameters": {"url": ""},
                    "reasoning": "User wants to navigate"
                }
            else:
                return {
                    "success": True,
                    "tool_name": "extract_content",
                    "parameters": {"extraction_type": "summary"},
                    "reasoning": "Default to content extraction"
                }
                
        except Exception as e:
            logger.error("Tool selection failed", error=str(e))
            return {
                "success": False,
                "error": f"Failed to select appropriate tool: {str(e)}"
            }
    
    async def _replan_from_failure(self, failed_step: TaskStep, failure_reason: str) -> bool:
        """Replan execution after step failure"""
        
        self.state = AgentState.REPLANNING
        await self.emit_event("agent_state_change", {"state": self.state.value})
        
        # In real implementation, would use AI to create new plan
        # For now, simulate replanning by modifying current plan
        
        await asyncio.sleep(0.5)  # Simulate replanning time
        
        # Simple replanning: retry with modified parameters
        if failed_step.retry_count < failed_step.max_retries:
            failed_step.retry_count = 0  # Reset retry count after replanning
            return True
        
        return False
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current execution state"""
        return {
            "state": self.state.value,
            "current_plan": self.current_plan.model_dump() if self.current_plan else None,
            "tools_available": len(tool_registry.get_all_tools()),
            "planning_horizon": self.planning_horizon
        }