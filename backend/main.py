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

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_client import AIClient
from browser_agent import BrowserAgent
from content_extractor import ContentExtractor

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
content_extractor: Optional[ContentExtractor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global ai_client, browser_agent, content_extractor
    
    logger.info("Starting AI Browser Backend...")
    
    # Initialize components
    ai_client = AIClient()
    browser_agent = BrowserAgent()
    content_extractor = ContentExtractor()
    
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

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_model": "gpt-oss:20b",
        "backend": "ollama",
        "timestamp": structlog.processors.TimeStamper()._make_stamper(fmt="iso")()
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

# WebSocket for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time AI chat"""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            if message_data.get("type") == "chat":
                # Stream AI response
                async for chunk in ai_client.stream_chat(
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
                    
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await websocket.close(code=1000)

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )