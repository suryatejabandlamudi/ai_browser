"""
Streaming AI Agent for Real-time Browser Automation
Provides WebSocket-based streaming responses like ChatGPT/Comet for superior UX.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import structlog

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ai_client import AIClient
from tools.base import streaming_executor, tool_registry, BrowserContext, ToolExecutionEvent
from tools.planning import TaskPlan, TaskStep, ClassifyTaskInput

logger = structlog.get_logger(__name__)

class StreamingMessage(BaseModel):
    """Streaming message format"""
    type: str  # "thinking", "tool_execution", "ai_response", "completion", "error"
    content: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
    message_id: str

class ConnectionManager:
    """Manages WebSocket connections for streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected", client_id=client_id)
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client disconnected", client_id=client_id)
    
    async def send_message(self, client_id: str, message: StreamingMessage):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Failed to send message to client", client_id=client_id, error=str(e))
                self.disconnect(client_id)

class StreamingAIAgent:
    """
    Streaming AI Agent that provides real-time feedback during task execution.
    Competes directly with Perplexity Comet's streaming interface.
    """
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.connection_manager = ConnectionManager()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Setup streaming tool execution handler
        streaming_executor.add_event_handler(self._handle_tool_event)
    
    async def _handle_tool_event(self, event: ToolExecutionEvent):
        """Handle tool execution events and broadcast to clients"""
        # Find active sessions that should receive this event
        for session_id, session_data in self.active_sessions.items():
            if session_data.get("listening_to_tools", False):
                client_id = session_data.get("client_id")
                if client_id:
                    await self.connection_manager.send_message(
                        client_id,
                        StreamingMessage(
                            type="tool_execution",
                            content=f"🔧 {event.message}",
                            data={
                                "tool_name": event.tool_name,
                                "stage": event.stage,
                                "event_data": event.data
                            },
                            timestamp=event.timestamp,
                            message_id=str(uuid.uuid4())
                        )
                    )
    
    async def connect_client(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await self.connection_manager.connect(websocket, client_id)
        
        # Send welcome message
        welcome_msg = StreamingMessage(
            type="connection",
            content="🚀 Connected to AI Browser - Ready for intelligent automation!",
            data={"capabilities": list(tool_registry.get_tool_names())},
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4())
        )
        await self.connection_manager.send_message(client_id, welcome_msg)
    
    def disconnect_client(self, client_id: str):
        """Disconnect a WebSocket client"""
        self.connection_manager.disconnect(client_id)
        
        # Clean up sessions
        sessions_to_remove = [
            session_id for session_id, session_data in self.active_sessions.items()
            if session_data.get("client_id") == client_id
        ]
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
    
    async def stream_ai_response(
        self, 
        client_id: str,
        user_message: str,
        context: BrowserContext,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingMessage, None]:
        """
        Stream AI response with real-time thinking, planning, and execution.
        This is the core method that competes with Comet's streaming interface.
        """
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize session
        self.active_sessions[session_id] = {
            "client_id": client_id,
            "listening_to_tools": True,
            "start_time": datetime.now()
        }
        
        try:
            # Phase 1: Show AI thinking
            yield StreamingMessage(
                type="thinking",
                content="🤔 Analyzing your request and current page context...",
                data={"phase": "analysis", "progress": 10},
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
            
            await asyncio.sleep(0.5)  # Brief pause for UX
            
            # Phase 2: Task Classification
            yield StreamingMessage(
                type="thinking",
                content="📊 Classifying task complexity and determining approach...",
                data={"phase": "classification", "progress": 25},
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
            
            # Get task classification (this would use the planning tools)
            task_complexity = await self._classify_user_task(user_message, context)
            
            yield StreamingMessage(
                type="ai_response",
                content=f"📋 Task classified as: **{task_complexity}**",
                data={"task_complexity": task_complexity, "progress": 40},
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
            
            # Phase 3: Planning
            if task_complexity in ["complex", "followup"]:
                yield StreamingMessage(
                    type="thinking",
                    content="🎯 Creating multi-step execution plan...",
                    data={"phase": "planning", "progress": 55},
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
                
                # Create task plan
                task_plan = await self._create_task_plan(user_message, context, task_complexity)
                
                plan_summary = f"Created {len(task_plan.steps)}-step plan:\n"
                for i, step in enumerate(task_plan.steps, 1):
                    plan_summary += f"{i}. {step.description}\n"
                
                yield StreamingMessage(
                    type="ai_response", 
                    content=f"📋 **Execution Plan:**\n{plan_summary}",
                    data={"task_plan": task_plan.model_dump(), "progress": 70},
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
                
                # Execute plan with streaming
                async for execution_msg in self._execute_task_plan_streaming(task_plan, context):
                    yield execution_msg
            else:
                # Simple task - direct AI response + tool execution
                yield StreamingMessage(
                    type="thinking",
                    content="⚡ Generating direct response for simple task...",
                    data={"phase": "direct_response", "progress": 60},
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
                
                # Get AI response
                ai_response = await self.ai_client.get_response(
                    user_message,
                    context.page_content or "",
                    context.current_url or ""
                )
                
                yield StreamingMessage(
                    type="ai_response",
                    content=ai_response.get("message", "Task completed successfully"),
                    data={"ai_actions": ai_response.get("actions", []), "progress": 90},
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
            
            # Final completion
            yield StreamingMessage(
                type="completion",
                content="✅ Task completed! Ready for your next request.",
                data={"session_id": session_id, "progress": 100},
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
            
        except Exception as e:
            logger.error(f"Streaming response failed", session_id=session_id, error=str(e))
            yield StreamingMessage(
                type="error",
                content=f"❌ Sorry, I encountered an error: {str(e)}",
                data={"error": str(e), "session_id": session_id},
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    async def _classify_user_task(self, user_message: str, context: BrowserContext) -> str:
        """Classify user task complexity with improved logic"""
        
        message_lower = user_message.lower()
        
        # Complex task indicators - multi-step processes
        complex_indicators = [
            "fill out", "complete signup", "signup process", "registration", 
            "book", "purchase", "checkout", "order", "payment",
            "multi-step", "workflow", "process", "sequence", 
            "submit", "form", "account", "profile"
        ]
        
        # Follow-up task indicators - sequential actions
        followup_indicators = [
            "then", "after", "next", "also", "and then", "after that",
            "verify", "confirm", "check email", "continue to"
        ]
        
        # Simple task indicators - single actions
        simple_indicators = [
            "click", "search", "find", "navigate", "go to", "open",
            "scroll", "look for", "show me", "what is"
        ]
        
        # Count indicators
        complex_count = sum(1 for indicator in complex_indicators if indicator in message_lower)
        followup_count = sum(1 for indicator in followup_indicators if indicator in message_lower) 
        simple_count = sum(1 for indicator in simple_indicators if indicator in message_lower)
        
        # Classification logic
        if complex_count > 0 or (len(message_lower.split()) > 8 and "form" in message_lower):
            return "complex"
        elif followup_count > 0 and ("then" in message_lower or "after" in message_lower):
            return "followup"
        elif simple_count > 0 or len(message_lower.split()) <= 4:
            return "simple"
        else:
            # Default based on message length and complexity
            if len(message_lower.split()) > 6:
                return "complex"
            else:
                return "simple"
    
    async def _create_task_plan(
        self, 
        user_message: str, 
        context: BrowserContext, 
        complexity: str
    ) -> TaskPlan:
        """Create detailed task execution plan"""
        
        # For now, create a simple plan - this could be enhanced with AI planning
        steps = []
        
        if "form" in user_message.lower():
            steps = [
                TaskStep(
                    tool_name="find_elements",
                    description="Find form fields on the page",
                    parameters={"description": "form inputs and fields"},
                    expected_outcome="List of form elements identified"
                ),
                TaskStep(
                    tool_name="form_fill", 
                    description="Fill out the form intelligently",
                    parameters={"auto_detect_fields": True},
                    expected_outcome="Form filled with provided data"
                ),
                TaskStep(
                    tool_name="click",
                    description="Submit the form",
                    parameters={"text_content": "submit"},
                    expected_outcome="Form submitted successfully"
                )
            ]
        elif "search" in user_message.lower():
            steps = [
                TaskStep(
                    tool_name="find_elements",
                    description="Find search input field",
                    parameters={"description": "search box or input field"},
                    expected_outcome="Search field located"
                ),
                TaskStep(
                    tool_name="type",
                    description="Enter search query",
                    parameters={"text_content": "extracted from user message"},
                    expected_outcome="Search query entered"
                ),
                TaskStep(
                    tool_name="click",
                    description="Click search button",
                    parameters={"text_content": "search"},
                    expected_outcome="Search executed"
                )
            ]
        else:
            # Generic plan
            steps = [
                TaskStep(
                    tool_name="extract_content",
                    description="Analyze current page content",
                    parameters={"extraction_type": "summary"},
                    expected_outcome="Page content understood"
                ),
                TaskStep(
                    tool_name="find_elements",
                    description="Find relevant elements for user task",
                    parameters={"description": user_message},
                    expected_outcome="Target elements identified"
                )
            ]
        
        return TaskPlan(
            user_intent=user_message,
            complexity=complexity,
            steps=steps,
            estimated_duration=len(steps) * 3,  # 3 seconds per step estimate
            success_criteria=[
                "All steps completed successfully",
                "User intent satisfied",
                "No error states encountered"
            ]
        )
    
    async def _execute_task_plan_streaming(
        self, 
        task_plan: TaskPlan, 
        context: BrowserContext
    ) -> AsyncGenerator[StreamingMessage, None]:
        """Execute task plan with streaming progress updates"""
        
        total_steps = len(task_plan.steps)
        
        for i, step in enumerate(task_plan.steps):
            step_progress = int((i / total_steps) * 100)
            
            yield StreamingMessage(
                type="tool_execution",
                content=f"🔄 Step {i+1}/{total_steps}: {step.description}",
                data={
                    "step_id": step.id,
                    "tool_name": step.tool_name,
                    "step_number": i+1,
                    "total_steps": total_steps,
                    "progress": 70 + (step_progress * 0.25)  # 70-95% range
                },
                timestamp=datetime.now(),
                message_id=str(uuid.uuid4())
            )
            
            # Execute the tool
            result = await streaming_executor.execute_tool(
                step.tool_name,
                step.parameters,
                context
            )
            
            if result.success:
                yield StreamingMessage(
                    type="ai_response",
                    content=f"✅ {step.description} - {result.message}",
                    data={
                        "step_result": result.data,
                        "execution_time": result.execution_time_ms
                    },
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
                step.status = "completed"
            else:
                yield StreamingMessage(
                    type="error",
                    content=f"❌ Step failed: {step.description} - {result.error}",
                    data={
                        "step_id": step.id,
                        "error": result.error
                    },
                    timestamp=datetime.now(),
                    message_id=str(uuid.uuid4())
                )
                step.status = "failed"
                # For now, continue with other steps - could implement retry logic
            
            await asyncio.sleep(0.3)  # Brief pause between steps for UX

# Global streaming agent instance
streaming_agent: Optional[StreamingAIAgent] = None

def get_streaming_agent(ai_client: AIClient) -> StreamingAIAgent:
    """Get or create global streaming agent instance"""
    global streaming_agent
    if not streaming_agent:
        streaming_agent = StreamingAIAgent(ai_client)
    return streaming_agent