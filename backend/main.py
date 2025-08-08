#!/usr/bin/env python3
"""
AI Browser Backend - Local Comet Alternative
Provides API endpoints for browser automation and AI interactions using GPT-OSS 20B via Ollama.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from datetime import datetime

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_client import AIClient
from browser_agent import BrowserAgent
try:
    from browser_agent_enhanced import BrowserAgentEnhanced
except ImportError:
    BrowserAgentEnhanced = None

try:
    from structured_agent import StructuredAgent
except ImportError:
    StructuredAgent = None
try:
    from content_extractor import ContentExtractor
except ImportError:
    from content_extractor_minimal import ContentExtractor
from accessibility_tree import AccessibilityTreeExtractor
from task_classifier import IntelligentTaskClassifier, TaskClassification
from visual_highlighter import VisualElementHighlighter
from form_intelligence import IntelligentFormProcessor
from context_memory import CrossTabMemoryManager
from visual_processor import VisualProcessor
from streaming_agent import get_streaming_agent, StreamingMessage
from tools.base import BrowserContext

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global instances
ai_client: Optional[AIClient] = None
browser_agent: Optional[BrowserAgent] = None
enhanced_agent: Optional[BrowserAgentEnhanced] = None
structured_agent: Optional[StructuredAgent] = None
content_extractor: Optional[ContentExtractor] = None
accessibility_extractor: Optional[AccessibilityTreeExtractor] = None
task_classifier: Optional[IntelligentTaskClassifier] = None
visual_highlighter: Optional[VisualElementHighlighter] = None
form_processor: Optional[IntelligentFormProcessor] = None
memory_manager: Optional[CrossTabMemoryManager] = None
visual_processor: Optional[VisualProcessor] = None

# Import new tool system and rolling horizon agent
try:
    from tools import tool_registry, BrowserContext
    from rolling_horizon_agent import RollingHorizonAgent
    rolling_horizon_agent: Optional[RollingHorizonAgent] = None
    TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced tool system not available: {e}")
    TOOLS_AVAILABLE = False
    tool_registry = None
    rolling_horizon_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global ai_client, browser_agent, enhanced_agent, structured_agent, content_extractor, accessibility_extractor, task_classifier, visual_highlighter, form_processor, memory_manager, visual_processor, rolling_horizon_agent
    
    logger.info("Starting AI Browser Backend...")
    
    # Initialize components
    ai_client = AIClient()
    browser_agent = BrowserAgent()
    enhanced_agent = BrowserAgentEnhanced(ai_client) if BrowserAgentEnhanced else None
    structured_agent = StructuredAgent(ai_client) if StructuredAgent else None
    content_extractor = ContentExtractor()
    accessibility_extractor = AccessibilityTreeExtractor()
    task_classifier = IntelligentTaskClassifier()
    visual_highlighter = VisualElementHighlighter()
    form_processor = IntelligentFormProcessor()
    memory_manager = CrossTabMemoryManager()
    visual_processor = VisualProcessor()
    
    # Initialize new rolling horizon agent
    if TOOLS_AVAILABLE:
        rolling_horizon_agent = RollingHorizonAgent()
        logger.info(f"🤖 Rolling Horizon Agent initialized with {len(tool_registry.get_all_tools())} tools")
    
    # Initialize memory manager
    await memory_manager.initialize()
    
    # Test Ollama connection
    if await ai_client.test_connection():
        logger.info("✅ GPT-OSS 20B connection verified")
    else:
        logger.error("❌ Failed to connect to Ollama/GPT-OSS")
        raise RuntimeError("Cannot start without AI model connection")
    
    logger.info("🚀 AI Browser Backend ready!")
    yield
    
    # Cleanup
    logger.info("Shutting down AI Browser Backend...")
    if browser_agent:
        await browser_agent.cleanup()
    if memory_manager:
        await memory_manager.cleanup()

# Initialize FastAPI
app = FastAPI(
    title="AI Browser Backend",
    description="Local AI-powered browser automation using GPT-OSS 20B",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Browser extensions need broad access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    page_url: Optional[str] = None
    page_content: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class PageSummaryRequest(BaseModel):
    url: str
    content: Optional[str] = None

class PageSummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    metadata: Dict[str, Any]

class ActionRequest(BaseModel):
    action_type: str  # click, type, navigate, etc.
    parameters: Dict[str, Any]
    page_url: str

class ActionResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None

class StructuredChatRequest(BaseModel):
    message: str
    page_url: Optional[str] = None
    page_content: Optional[str] = None
    page_title: Optional[str] = None
    viewport_size: Optional[Dict[str, int]] = None
    
class StructuredChatResponse(BaseModel):
    success: bool
    message: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    task_complexity: str
    metadata: Dict[str, Any]

class WorkflowRequest(BaseModel):
    name: str
    actions: List[Dict[str, Any]]
    user_intent: Optional[str] = ""
    page_url: Optional[str] = ""

class WorkflowResponse(BaseModel):
    success: bool
    message: str
    workflow_id: str
    data: Optional[Dict[str, Any]] = None

class AccessibilityRequest(BaseModel):
    page_url: str
    page_content: Optional[str] = None

class ElementSearchRequest(BaseModel):
    page_url: str
    page_content: Optional[str] = None
    description: str

class TaskClassificationRequest(BaseModel):
    user_input: str
    page_url: Optional[str] = None
    page_content: Optional[str] = None
    tab_id: Optional[str] = None

class TaskClassificationResponse(BaseModel):
    success: bool
    message: str
    classification: Dict[str, Any]

class HighlightRequest(BaseModel):
    selector: str
    style: Optional[str] = "primary"
    label: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    pulse: Optional[bool] = False

class FormAnalysisRequest(BaseModel):
    form_html: str
    page_url: Optional[str] = ""

class FormAnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis: Dict[str, Any]

class ContextQueryRequest(BaseModel):
    query: str
    context_types: Optional[List[str]] = None
    tab_id: Optional[str] = None
    domain: Optional[str] = None
    limit: Optional[int] = 20

class ScreenshotRequest(BaseModel):
    page_url: str
    viewport_width: Optional[int] = 1280
    viewport_height: Optional[int] = 720
    full_page: Optional[bool] = True

class ElementScreenshotRequest(BaseModel):
    selector: str
    page_url: str
    padding: Optional[int] = 10

class OCRRequest(BaseModel):
    image_path: str
    language: Optional[str] = 'eng'
    confidence_threshold: Optional[float] = 0.5

class VisualAnalysisRequest(BaseModel):
    screenshot_path: str
    analysis_types: Optional[List[str]] = None

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    
    try:
        from tools import tool_registry
        tools_info = {
            "total_registered": len(tool_registry.tools),
            "categories": len(tool_registry.tools_by_category)
        }
    except ImportError:
        tools_info = {
            "total_registered": 0,
            "categories": 0,
            "error": "Tools system not available"
        }
    
    return {
        "status": "healthy",
        "ai_model": "gpt-oss:20b",
        "backend": "ollama",
        "agents": {
            "browser_agent": browser_agent is not None,
            "enhanced_agent": enhanced_agent is not None,
            "structured_agent": structured_agent is not None,
            "task_classifier": task_classifier is not None,
            "visual_highlighter": visual_highlighter is not None,
            "form_processor": form_processor is not None,
            "memory_manager": memory_manager is not None,
            "visual_processor": visual_processor is not None
        },
        "tools": tools_info,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Main chat endpoint for AI interactions"""
    try:
        logger.info("Processing chat request", message_preview=request.message[:100])
        
        # Build context from page if provided
        context = {}
        if request.page_url and request.page_content:
            # Extract clean content
            cleaned_content = await content_extractor.extract_main_content(
                request.page_content, request.page_url
            )
            context.update({
                "page_url": request.page_url,
                "page_content": cleaned_content,
                "has_page_context": True
            })
        
        # Get AI response
        ai_response = await ai_client.chat(
            message=request.message,
            context=context
        )
        
        # Parse potential actions from AI response
        actions = await browser_agent.parse_actions(ai_response.get("raw_response", ""))
        
        return ChatResponse(
            response=ai_response["content"],
            actions=actions,
            metadata={
                "model": "gpt-oss:20b",
                "tokens_used": ai_response.get("usage", {}),
                "has_actions": len(actions) > 0 if actions else False
            }
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@app.post("/api/chat/enhanced", response_model=ChatResponse)
async def enhanced_chat_with_ai(request: ChatRequest):
    """Enhanced chat endpoint with intelligent planning and action parsing"""
    try:
        logger.info("Processing enhanced chat request", message_preview=request.message[:100])
        
        # Build page context
        page_context = {}
        if request.page_url and request.page_content:
            cleaned_content = await content_extractor.extract_main_content(
                request.page_content, request.page_url
            )
            page_context = {
                "page_url": request.page_url,
                "page_content": cleaned_content,
                "has_page_context": True
            }
        
        # Process task with enhanced agent
        result = await enhanced_agent.process_task(request.message, page_context)
        
        # Add to conversation history
        enhanced_agent.add_to_history(request.message, result["response"])
        
        return ChatResponse(
            response=result["response"],
            actions=result.get("actions", []),
            metadata={
                "model": "gpt-oss:20b",
                "task_type": result.get("task_type"),
                "plan_confidence": result.get("plan_confidence"),
                "enhanced_agent": True,
                **result.get("metadata", {})
            }
        )
        
    except Exception as e:
        logger.error("Enhanced chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Enhanced AI chat failed: {str(e)}")

@app.post("/api/chat/structured", response_model=StructuredChatResponse)
async def structured_chat_with_ai(request: StructuredChatRequest):
    """Structured chat endpoint using validated tools and schemas"""
    try:
        logger.info("Processing structured chat request", message_preview=request.message[:100])
        
        # Build page context
        page_context = {
            "url": request.page_url or "",
            "content": request.page_content,
            "title": request.page_title,
            "viewport_size": request.viewport_size or {}
        }
        
        # Process request with structured agent
        result = await structured_agent.process_request(request.message, page_context)
        
        return StructuredChatResponse(
            success=result.success,
            message=result.message,
            tool_calls=result.tool_calls,
            tool_results=[r.model_dump() for r in result.tool_results],
            task_complexity=result.task_complexity.value,
            metadata={
                "model": "gpt-oss:20b",
                "structured_tools": True,
                **result.metadata
            }
        )
        
    except Exception as e:
        logger.error("Structured chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Structured AI chat failed: {str(e)}")

@app.post("/api/summarize", response_model=PageSummaryResponse)
async def summarize_page(request: PageSummaryRequest):
    """Summarize web page content"""
    try:
        logger.info("Summarizing page", url=request.url)
        
        # Get page content if not provided
        if not request.content:
            page_content = await content_extractor.fetch_page_content(request.url)
        else:
            page_content = request.content
            
        # Extract main content
        cleaned_content = await content_extractor.extract_main_content(page_content, request.url)
        
        # Generate summary via AI
        summary_response = await ai_client.summarize(
            content=cleaned_content,
            url=request.url
        )
        
        return PageSummaryResponse(
            summary=summary_response["summary"],
            key_points=summary_response.get("key_points", []),
            metadata={
                "url": request.url,
                "content_length": len(cleaned_content),
                "model": "gpt-oss:20b"
            }
        )
        
    except Exception as e:
        logger.error("Page summarization failed", error=str(e), url=request.url)
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/api/action", response_model=ActionResponse)
async def execute_action(request: ActionRequest):
    """Execute browser automation action"""
    try:
        logger.info("Executing browser action", 
                   action=request.action_type, 
                   url=request.page_url)
        
        result = await browser_agent.execute_action(
            action_type=request.action_type,
            parameters=request.parameters,
            page_url=request.page_url
        )
        
        return ActionResponse(
            success=result["success"],
            message=result["message"],
            result=result.get("data")
        )
        
    except Exception as e:
        logger.error("Action execution failed", error=str(e), action=request.action_type)
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")

@app.get("/api/tools")
async def get_available_tools():
    """Get information about all available structured tools"""
    try:
        from tools import get_available_tools
        tools_info = get_available_tools()
        
        return {
            "tools": tools_info,
            "total_tools": sum(len(tools) for tools in tools_info.values()),
            "tool_categories": list(tools_info.keys())
        }
        
    except Exception as e:
        logger.error("Failed to get tools info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tools info: {str(e)}")

@app.get("/api/agent/stats")
async def get_agent_stats():
    """Get statistics about agent usage and performance"""
    try:
        stats = {}
        
        if structured_agent:
            stats["structured_agent"] = structured_agent.get_conversation_summary()
        
        if enhanced_agent:
            stats["enhanced_agent"] = {
                "conversation_history_length": len(enhanced_agent.conversation_history),
                "current_context_keys": list(enhanced_agent.current_context.keys())
            }
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get agent stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent stats: {str(e)}")

@app.post("/api/workflow/create", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowRequest):
    """Create a new multi-step workflow"""
    try:
        logger.info("Creating workflow", name=request.name, actions_count=len(request.actions))
        
        workflow_id = await browser_agent.create_workflow(
            name=request.name,
            actions=request.actions,
            user_intent=request.user_intent,
            page_url=request.page_url
        )
        
        return WorkflowResponse(
            success=True,
            message=f"Workflow '{request.name}' created successfully",
            workflow_id=workflow_id,
            data={
                "workflow_id": workflow_id,
                "name": request.name,
                "steps_count": len(request.actions)
            }
        )
        
    except Exception as e:
        logger.error("Workflow creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")

@app.post("/api/workflow/{workflow_id}/execute", response_model=WorkflowResponse)
async def execute_workflow(workflow_id: str):
    """Execute a multi-step workflow"""
    try:
        logger.info("Executing workflow", workflow_id=workflow_id)
        
        result = await browser_agent.execute_workflow(workflow_id)
        
        return WorkflowResponse(
            success=result["success"],
            message=result["message"],
            workflow_id=workflow_id,
            data=result.get("data")
        )
        
    except Exception as e:
        logger.error("Workflow execution failed", error=str(e), workflow_id=workflow_id)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get the status of a workflow"""
    try:
        result = browser_agent.get_workflow_status(workflow_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result["data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", error=str(e), workflow_id=workflow_id)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@app.post("/api/workflow/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause an active workflow"""
    try:
        result = browser_agent.pause_workflow(workflow_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to pause workflow", error=str(e), workflow_id=workflow_id)
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")

@app.post("/api/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow"""
    try:
        result = browser_agent.resume_workflow(workflow_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to resume workflow", error=str(e), workflow_id=workflow_id)
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")

@app.get("/api/workflows")
async def list_workflows():
    """List all active and recent workflows"""
    try:
        active_workflows = []
        for workflow_id, workflow in browser_agent.active_workflows.items():
            active_workflows.append({
                "id": workflow_id,
                "name": workflow.name,
                "status": workflow.status,
                "current_step": workflow.current_step,
                "total_steps": len(workflow.steps),
                "created_at": workflow.created_at.isoformat()
            })
        
        recent_workflows = []
        for workflow in browser_agent.workflow_history[-10:]:  # Last 10 workflows
            recent_workflows.append({
                "id": workflow.id,
                "name": workflow.name,
                "status": workflow.status,
                "total_steps": len(workflow.steps),
                "completed_steps": sum(1 for s in workflow.steps if s.status == "completed"),
                "created_at": workflow.created_at.isoformat()
            })
        
        return {
            "active_workflows": active_workflows,
            "recent_workflows": recent_workflows,
            "total_active": len(active_workflows),
            "total_history": len(browser_agent.workflow_history)
        }
        
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@app.post("/api/accessibility/extract")
async def extract_accessibility_tree(request: AccessibilityRequest):
    """Extract accessibility tree from a web page"""
    try:
        logger.info("Extracting accessibility tree", url=request.page_url)
        
        tree = await accessibility_extractor.extract_accessibility_tree(
            page_url=request.page_url,
            page_content=request.page_content
        )
        
        # Generate AI-friendly summary
        summary = accessibility_extractor.generate_ai_friendly_summary(tree)
        
        return {
            "success": True,
            "message": "Accessibility tree extracted successfully",
            "data": {
                "tree": tree,
                "summary": summary,
                "url": request.page_url,
                "nodes_count": len(tree.get("nodes", [])),
                "interactive_count": tree.get("interactive_nodes", 0)
            }
        }
        
    except Exception as e:
        logger.error("Failed to extract accessibility tree", error=str(e), url=request.page_url)
        raise HTTPException(status_code=500, detail=f"Accessibility extraction failed: {str(e)}")

@app.post("/api/accessibility/search")
async def search_elements_by_description(request: ElementSearchRequest):
    """Find elements by AI description using accessibility tree"""
    try:
        logger.info("Searching elements by description", 
                   url=request.page_url, 
                   description=request.description)
        
        # First extract accessibility tree if needed
        tree = await accessibility_extractor.extract_accessibility_tree(
            page_url=request.page_url,
            page_content=request.page_content
        )
        
        # Search for elements matching the description
        matches = await accessibility_extractor.find_elements_by_description(
            tree=tree,
            description=request.description
        )
        
        return {
            "success": True,
            "message": f"Found {len(matches)} element matches",
            "data": {
                "matches": matches,
                "search_description": request.description,
                "url": request.page_url,
                "total_elements_searched": len(tree.get("nodes", []))
            }
        }
        
    except Exception as e:
        logger.error("Failed to search elements", error=str(e), description=request.description)
        raise HTTPException(status_code=500, detail=f"Element search failed: {str(e)}")

@app.get("/api/accessibility/{page_url:path}/element/{element_id}/context")
async def get_element_context(page_url: str, element_id: str):
    """Get contextual information about a specific element"""
    try:
        # Get cached tree or extract new one
        tree = await accessibility_extractor.extract_accessibility_tree(page_url)
        
        # Get element context
        context = await accessibility_extractor.get_element_context(tree, element_id)
        
        if "error" in context:
            raise HTTPException(status_code=404, detail=context["error"])
        
        return {
            "success": True,
            "message": "Element context retrieved",
            "data": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get element context", error=str(e), element_id=element_id)
        raise HTTPException(status_code=500, detail=f"Failed to get element context: {str(e)}")

@app.post("/api/task/classify", response_model=TaskClassificationResponse)
async def classify_user_task(request: TaskClassificationRequest):
    """Classify user task for intelligent planning"""
    try:
        logger.info("Classifying user task", input_preview=request.user_input[:100])
        
        # Build page context
        page_context = {}
        if request.page_url and request.page_content:
            page_context = {
                'page_url': request.page_url,
                'page_content': request.page_content
            }
        
        # Classify the task
        classification = await task_classifier.classify_task(request.user_input, page_context)
        
        return TaskClassificationResponse(
            success=True,
            message="Task classified successfully",
            classification={
                'complexity': classification.complexity.value,
                'category': classification.category.value,
                'confidence': classification.confidence,
                'intent_summary': classification.intent_summary,
                'suggested_actions': classification.suggested_actions,
                'requires_page_context': classification.requires_page_context,
                'estimated_steps': classification.estimated_steps,
                'potential_challenges': classification.potential_challenges,
                'success_criteria': classification.success_criteria
            }
        )
        
    except Exception as e:
        logger.error("Task classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Task classification failed: {str(e)}")

@app.post("/api/visual/highlight")
async def highlight_element(request: HighlightRequest):
    """Highlight an element on the page"""
    try:
        from visual_highlighter import HighlightStyle
        
        style = HighlightStyle(request.style) if request.style else HighlightStyle.PRIMARY
        
        highlight_id = await visual_highlighter.highlight_element(
            selector=request.selector,
            style=style,
            label=request.label,
            description=request.description,
            duration=request.duration,
            pulse=request.pulse or False
        )
        
        return {
            "success": True,
            "message": "Element highlighted successfully",
            "highlight_id": highlight_id,
            "data": visual_highlighter.get_highlight_data()
        }
        
    except Exception as e:
        logger.error("Failed to highlight element", error=str(e))
        raise HTTPException(status_code=500, detail=f"Element highlighting failed: {str(e)}")

@app.post("/api/visual/highlight/accessibility")
async def highlight_accessibility_matches(request: ElementSearchRequest):
    """Highlight elements from accessibility tree matches"""
    try:
        # First get accessibility tree
        tree = await accessibility_extractor.extract_accessibility_tree(
            page_url=request.page_url,
            page_content=request.page_content
        )
        
        # Find matching elements
        matches = await accessibility_extractor.find_elements_by_description(
            tree=tree,
            description=request.description
        )
        
        # Highlight the matches
        highlighted_ids = await visual_highlighter.highlight_accessibility_matches(matches)
        
        return {
            "success": True,
            "message": f"Highlighted {len(highlighted_ids)} matching elements",
            "highlighted_ids": highlighted_ids,
            "matches": matches,
            "data": visual_highlighter.get_highlight_data()
        }
        
    except Exception as e:
        logger.error("Failed to highlight accessibility matches", error=str(e))
        raise HTTPException(status_code=500, detail=f"Accessibility highlighting failed: {str(e)}")

@app.delete("/api/visual/highlight/{highlight_id}")
async def remove_highlight(highlight_id: str):
    """Remove a specific highlight"""
    try:
        success = await visual_highlighter.remove_highlight(highlight_id)
        
        if success:
            return {"success": True, "message": "Highlight removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Highlight not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove highlight", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to remove highlight: {str(e)}")

@app.delete("/api/visual/highlight/group/{group_name}")
async def remove_highlight_group(group_name: str):
    """Remove all highlights in a group"""
    try:
        success = await visual_highlighter.remove_highlight_group(group_name)
        
        if success:
            return {"success": True, "message": f"Highlight group '{group_name}' removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Highlight group not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove highlight group", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to remove highlight group: {str(e)}")

@app.delete("/api/visual/highlight")
async def clear_all_highlights():
    """Clear all active highlights"""
    try:
        count = await visual_highlighter.clear_all_highlights()
        return {"success": True, "message": f"Cleared {count} highlights"}
        
    except Exception as e:
        logger.error("Failed to clear highlights", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear highlights: {str(e)}")

@app.post("/api/form/analyze", response_model=FormAnalysisResponse)
async def analyze_form(request: FormAnalysisRequest):
    """Analyze a form for intelligent processing"""
    try:
        logger.info("Analyzing form", url=request.page_url)
        
        analysis = await form_processor.analyze_form(
            form_html=request.form_html,
            page_url=request.page_url
        )
        
        return FormAnalysisResponse(
            success=True,
            message="Form analyzed successfully",
            analysis={
                'form_id': analysis.form_id,
                'form_type': analysis.form_type.value,
                'action_url': analysis.action_url,
                'method': analysis.method,
                'fields': [
                    {
                        'id': field.id,
                        'name': field.name,
                        'field_type': field.field_type.value,
                        'label': field.label,
                        'placeholder': field.placeholder,
                        'required': field.required,
                        'current_value': field.current_value,
                        'selectors': field.selectors,
                        'validation_rules': field.validation_rules,
                        'auto_fill_suggestion': field.auto_fill_suggestion,
                        'confidence': field.confidence
                    } for field in analysis.fields
                ],
                'submit_buttons': analysis.submit_buttons,
                'completion_percentage': analysis.completion_percentage,
                'validation_errors': analysis.validation_errors,
                'auto_fill_available': analysis.auto_fill_available,
                'estimated_completion_time': analysis.estimated_completion_time
            }
        )
        
    except Exception as e:
        logger.error("Form analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Form analysis failed: {str(e)}")

@app.post("/api/form/{form_id}/auto-fill-plan")
async def generate_auto_fill_plan(form_id: str, request: FormAnalysisRequest):
    """Generate auto-fill plan for a form"""
    try:
        # First analyze the form
        analysis = await form_processor.analyze_form(
            form_html=request.form_html,
            page_url=request.page_url
        )
        
        # Generate auto-fill plan
        plan = await form_processor.generate_auto_fill_plan(analysis)
        
        return {
            "success": True,
            "message": "Auto-fill plan generated",
            "plan": plan
        }
        
    except Exception as e:
        logger.error("Failed to generate auto-fill plan", error=str(e))
        raise HTTPException(status_code=500, detail=f"Auto-fill plan generation failed: {str(e)}")

@app.post("/api/memory/context")
async def store_context_item(request: Dict[str, Any]):
    """Store a context item in memory"""
    try:
        from context_memory import ContextType, MemoryScope
        
        context_type = ContextType(request.get('context_type', 'conversation'))
        scope = MemoryScope(request.get('scope', 'session'))
        
        item_id = await memory_manager.store_context(
            context_type=context_type,
            content=request.get('content', {}),
            scope=scope,
            tab_id=request.get('tab_id'),
            domain=request.get('domain'),
            ttl_hours=request.get('ttl_hours')
        )
        
        return {"success": True, "message": "Context stored", "item_id": item_id}
        
    except Exception as e:
        logger.error("Failed to store context", error=str(e))
        raise HTTPException(status_code=500, detail=f"Context storage failed: {str(e)}")

@app.post("/api/memory/query")
async def query_context(request: ContextQueryRequest):
    """Query relevant context from memory"""
    try:
        from context_memory import ContextType
        
        context_types = None
        if request.context_types:
            context_types = [ContextType(ct) for ct in request.context_types]
        
        context_items = await memory_manager.get_relevant_context(
            query=request.query,
            context_types=context_types,
            tab_id=request.tab_id,
            domain=request.domain,
            limit=request.limit or 20
        )
        
        # Convert to serializable format
        items = []
        for item in context_items:
            items.append({
                'id': item.id,
                'context_type': item.context_type.value,
                'scope': item.scope.value,
                'content': item.content,
                'metadata': item.metadata,
                'tab_id': item.tab_id,
                'domain': item.domain,
                'timestamp': item.timestamp.isoformat(),
                'relevance_score': item.relevance_score
            })
        
        return {
            "success": True,
            "message": f"Found {len(items)} relevant context items",
            "items": items
        }
        
    except Exception as e:
        logger.error("Failed to query context", error=str(e))
        raise HTTPException(status_code=500, detail=f"Context query failed: {str(e)}")

@app.get("/api/memory/conversation/{tab_id}")
async def get_conversation_history(tab_id: str, limit: int = 10):
    """Get conversation history for a tab"""
    try:
        conversations = await memory_manager.get_conversation_history(
            tab_id=tab_id,
            limit=limit
        )
        
        return {
            "success": True,
            "message": f"Retrieved {len(conversations)} conversation items",
            "conversations": conversations
        }
        
    except Exception as e:
        logger.error("Failed to get conversation history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@app.post("/api/memory/tab/{tab_id}/register")
async def register_tab(tab_id: str):
    """Register a new tab"""
    try:
        await memory_manager.register_tab(tab_id)
        return {"success": True, "message": f"Tab {tab_id} registered"}
        
    except Exception as e:
        logger.error("Failed to register tab", error=str(e))
        raise HTTPException(status_code=500, detail=f"Tab registration failed: {str(e)}")

@app.delete("/api/memory/tab/{tab_id}")
async def unregister_tab(tab_id: str):
    """Unregister a tab"""
    try:
        await memory_manager.unregister_tab(tab_id)
        return {"success": True, "message": f"Tab {tab_id} unregistered"}
        
    except Exception as e:
        logger.error("Failed to unregister tab", error=str(e))
        raise HTTPException(status_code=500, detail=f"Tab unregistration failed: {str(e)}")

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    try:
        stats = await memory_manager.get_memory_stats()
        return {"success": True, "data": stats}
        
    except Exception as e:
        logger.error("Failed to get memory stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

@app.post("/api/visual/screenshot/page")
async def capture_page_screenshot(request: ScreenshotRequest):
    """Capture a screenshot of the current page"""
    try:
        logger.info("Capturing page screenshot", url=request.page_url)
        
        screenshot = await visual_processor.capture_page_screenshot(
            page_url=request.page_url,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            full_page=request.full_page
        )
        
        return {
            "success": True,
            "message": "Page screenshot captured successfully",
            "screenshot": {
                "image_path": screenshot.image_path,
                "width": screenshot.width,
                "height": screenshot.height,
                "format": screenshot.format,
                "timestamp": screenshot.timestamp
            }
        }
        
    except Exception as e:
        logger.error("Failed to capture page screenshot", error=str(e))
        raise HTTPException(status_code=500, detail=f"Screenshot capture failed: {str(e)}")

@app.post("/api/visual/screenshot/element")
async def capture_element_screenshot(request: ElementScreenshotRequest):
    """Capture a screenshot of a specific element"""
    try:
        logger.info("Capturing element screenshot", selector=request.selector)
        
        screenshot = await visual_processor.capture_element_screenshot(
            selector=request.selector,
            page_url=request.page_url,
            padding=request.padding
        )
        
        return {
            "success": True,
            "message": "Element screenshot captured successfully",
            "screenshot": {
                "image_path": screenshot.image_path,
                "width": screenshot.width,
                "height": screenshot.height,
                "format": screenshot.format,
                "timestamp": screenshot.timestamp
            }
        }
        
    except Exception as e:
        logger.error("Failed to capture element screenshot", error=str(e))
        raise HTTPException(status_code=500, detail=f"Element screenshot failed: {str(e)}")

@app.post("/api/visual/ocr")
async def extract_text_from_image(request: OCRRequest):
    """Extract text from an image using OCR"""
    try:
        logger.info("Extracting text from image", image_path=request.image_path)
        
        ocr_result = await visual_processor.extract_text_from_image(
            image_path=request.image_path,
            language=request.language,
            confidence_threshold=request.confidence_threshold
        )
        
        return {
            "success": True,
            "message": "OCR text extraction completed",
            "result": {
                "text": ocr_result.text,
                "confidence": ocr_result.confidence,
                "bounding_boxes": ocr_result.bounding_boxes,
                "language": ocr_result.language,
                "processing_time": ocr_result.processing_time
            }
        }
        
    except Exception as e:
        logger.error("Failed to extract text from image", error=str(e))
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

@app.post("/api/visual/analyze/layout")
async def analyze_page_layout(request: VisualAnalysisRequest):
    """Analyze page layout from screenshot"""
    try:
        logger.info("Analyzing page layout", screenshot_path=request.screenshot_path)
        
        layout_analysis = await visual_processor.analyze_page_layout(request.screenshot_path)
        
        return {
            "success": True,
            "message": "Page layout analysis completed",
            "analysis": layout_analysis
        }
        
    except Exception as e:
        logger.error("Failed to analyze page layout", error=str(e))
        raise HTTPException(status_code=500, detail=f"Layout analysis failed: {str(e)}")

@app.post("/api/visual/find-elements")
async def find_visual_elements(request: VisualAnalysisRequest):
    """Find UI elements in screenshot using computer vision"""
    try:
        element_types = request.analysis_types or ['button', 'input', 'link', 'image']
        logger.info("Finding visual elements", types=element_types)
        
        elements = await visual_processor.find_visual_elements(
            screenshot_path=request.screenshot_path,
            element_types=element_types
        )
        
        return {
            "success": True,
            "message": f"Found {len(elements)} visual elements",
            "elements": elements
        }
        
    except Exception as e:
        logger.error("Failed to find visual elements", error=str(e))
        raise HTTPException(status_code=500, detail=f"Visual element detection failed: {str(e)}")

@app.delete("/api/visual/cleanup")
async def cleanup_temp_files():
    """Clean up temporary screenshot files"""
    try:
        await visual_processor.cleanup_temp_files()
        return {"success": True, "message": "Temporary files cleaned up"}
        
    except Exception as e:
        logger.error("Failed to cleanup temp files", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# WebSocket for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time AI chat and workflow streaming"""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message based on type
            if message_data.get("type") == "chat":
                # Stream AI response
                async for chunk in ai_client.chat_stream(
                    message=message_data["message"],
                    context=message_data.get("context", {})
                ):
                    await websocket.send_text(json.dumps({
                        "type": "chat_chunk",
                        "content": chunk
                    }))
                
                # Send completion signal
                await websocket.send_text(json.dumps({
                    "type": "chat_complete"
                }))
            
            elif message_data.get("type") == "workflow_execute":
                # Stream workflow execution progress
                workflow_id = message_data.get("workflow_id")
                if not workflow_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No workflow_id provided"
                    }))
                    continue
                
                # Send workflow start notification
                await websocket.send_text(json.dumps({
                    "type": "workflow_start",
                    "workflow_id": workflow_id
                }))
                
                # Execute workflow and stream progress
                try:
                    # Get workflow info
                    status_result = browser_agent.get_workflow_status(workflow_id)
                    if status_result["success"]:
                        workflow_data = status_result["data"]
                        total_steps = workflow_data["total_steps"]
                        
                        # Send initial progress
                        await websocket.send_text(json.dumps({
                            "type": "workflow_progress",
                            "workflow_id": workflow_id,
                            "current_step": 0,
                            "total_steps": total_steps,
                            "status": "starting"
                        }))
                    
                    # Execute the workflow
                    result = await browser_agent.execute_workflow(workflow_id)
                    
                    # Send final result
                    await websocket.send_text(json.dumps({
                        "type": "workflow_complete",
                        "workflow_id": workflow_id,
                        "success": result["success"],
                        "message": result["message"],
                        "data": result.get("data")
                    }))
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "workflow_error",
                        "workflow_id": workflow_id,
                        "error": str(e)
                    }))
            
            elif message_data.get("type") == "workflow_status":
                # Get workflow status
                workflow_id = message_data.get("workflow_id")
                if workflow_id:
                    try:
                        result = browser_agent.get_workflow_status(workflow_id)
                        await websocket.send_text(json.dumps({
                            "type": "workflow_status_response",
                            "workflow_id": workflow_id,
                            "success": result["success"],
                            "data": result.get("data") if result["success"] else None,
                            "message": result["message"]
                        }))
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to get workflow status: {str(e)}"
                        }))
                        
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await websocket.close(code=1000)

# New Advanced AI Agent Endpoints (Phase 2)
@app.post("/api/agent/rolling-horizon/execute")
async def execute_with_rolling_horizon(request: ChatRequest):
    """Execute task using advanced rolling-horizon planning agent"""
    try:
        if not TOOLS_AVAILABLE or not rolling_horizon_agent:
            raise HTTPException(status_code=503, detail="Advanced agent system not available")
        
        logger.info("Rolling horizon execution", message=request.message[:100])
        
        # Create browser context from request
        browser_context = BrowserContext(
            current_url=request.page_url,
            page_title=getattr(request, 'page_title', None),
            page_content=request.page_content if hasattr(request, 'page_content') else None
        )
        
        # Execute task with rolling horizon agent
        result = await rolling_horizon_agent.execute_task(
            user_message=request.message,
            browser_context=browser_context
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "strategy": result.get("strategy", "rolling_horizon"),
            "data": result
        }
        
    except Exception as e:
        logger.error("Rolling horizon execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@app.websocket("/ws/agent/stream")
async def websocket_agent_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming agent execution with real-time updates"""
    await websocket.accept()
    
    try:
        logger.info("Agent streaming WebSocket connected")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "execute_task":
                user_message = message_data.get("message", "")
                context_data = message_data.get("context", {})
                
                # Create browser context
                browser_context = BrowserContext(
                    current_url=context_data.get("page_url"),
                    page_title=context_data.get("page_title"), 
                    page_content=context_data.get("page_content")
                )
                
                # Define streaming handler
                async def stream_handler(event):
                    """Send streaming events to WebSocket client"""
                    await websocket.send_text(json.dumps(event.to_dict()))
                
                try:
                    if TOOLS_AVAILABLE and rolling_horizon_agent:
                        # Use advanced rolling horizon agent
                        result = await rolling_horizon_agent.execute_task(
                            user_message=user_message,
                            browser_context=browser_context,
                            stream_handler=stream_handler
                        )
                    else:
                        # Fallback to basic chat
                        await websocket.send_text(json.dumps({
                            "type": "thinking_started",
                            "data": {"message": "Processing your request..."},
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        ai_response = await ai_client.chat(user_message)
                        result = {
                            "success": True,
                            "message": ai_response.get("content", "Task completed"),
                            "strategy": "basic_chat"
                        }
                    
                    # Send final result
                    await websocket.send_text(json.dumps({
                        "type": "execution_complete",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "execution_error",
                        "data": {"error": str(e)},
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif message_data.get("type") == "tool_execute":
                # Direct tool execution
                tool_name = message_data.get("tool_name")
                tool_params = message_data.get("parameters", {})
                
                if TOOLS_AVAILABLE and tool_registry:
                    try:
                        # Create minimal context
                        context = BrowserContext()
                        
                        # Execute tool with streaming
                        from tools import streaming_executor
                        
                        async def tool_stream_handler(event):
                            await websocket.send_text(json.dumps({
                                "type": "tool_event",
                                "data": event.model_dump(),
                                "timestamp": datetime.now().isoformat()
                            }))
                        
                        streaming_executor.add_event_handler(tool_stream_handler)
                        
                        result = await streaming_executor.execute_tool(tool_name, tool_params, context)
                        
                        await websocket.send_text(json.dumps({
                            "type": "tool_complete",
                            "data": {
                                "tool_name": tool_name,
                                "success": result.success,
                                "message": result.message,
                                "result": result.data
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "tool_error",
                            "data": {"tool_name": tool_name, "error": str(e)},
                            "timestamp": datetime.now().isoformat()
                        }))
                        
    except WebSocketDisconnect:
        logger.info("Agent streaming WebSocket disconnected")
    except Exception as e:
        logger.error("Agent streaming WebSocket error", error=str(e))
        await websocket.close(code=1000)

@app.get("/api/tools/available")
async def get_available_tools():
    """Get list of all available tools"""
    try:
        if not TOOLS_AVAILABLE or not tool_registry:
            return {
                "tools_available": False,
                "message": "Advanced tool system not loaded",
                "tools": []
            }
        
        tools = tool_registry.format_tools_for_ai()
        
        return {
            "tools_available": True,
            "total_tools": len(tools),
            "tools": tools,
            "categories": {
                category.value: len(tool_registry.get_tools_by_category(category))
                for category in tool_registry.tools_by_category.keys()
            }
        }
        
    except Exception as e:
        logger.error("Failed to get available tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

# WebSocket Endpoints for Streaming AI Responses

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time streaming AI responses.
    Competes directly with Perplexity Comet's streaming interface.
    """
    streaming_agent = get_streaming_agent(ai_client)
    await streaming_agent.connect_client(websocket, client_id)
    
    try:
        while True:
            # Wait for user messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            page_url = message_data.get("page_url", "")
            page_content = message_data.get("page_content", "")
            
            if not user_message:
                continue
            
            # Create browser context
            context = BrowserContext(
                current_url=page_url,
                page_content=page_content,
                current_tab_id=message_data.get("tab_id"),
                page_title=message_data.get("page_title"),
                user_intent=user_message
            )
            
            # Stream AI response
            async for response_msg in streaming_agent.stream_ai_response(
                client_id=client_id,
                user_message=user_message,
                context=context,
                session_id=message_data.get("session_id")
            ):
                await streaming_agent.connection_manager.send_message(client_id, response_msg)
                
    except WebSocketDisconnect:
        streaming_agent.disconnect_client(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}", error=str(e))
        streaming_agent.disconnect_client(client_id)

@app.get("/api/streaming/status")
async def get_streaming_status():
    """Get status of streaming connections and active sessions"""
    try:
        streaming_agent = get_streaming_agent(ai_client)
        
        return {
            "success": True,
            "message": "Streaming system operational",
            "data": {
                "active_connections": len(streaming_agent.connection_manager.active_connections),
                "active_sessions": len(streaming_agent.active_sessions),
                "supported_message_types": ["thinking", "tool_execution", "ai_response", "completion", "error"]
            }
        }
        
    except Exception as e:
        logger.error("Failed to get streaming status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Streaming status failed: {str(e)}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )