#!/usr/bin/env python3
"""
Enhanced Browser Agent - Intelligent Action Parsing and Planning
Based on BrowserOS architecture but adapted for GPT-OSS 20B local processing
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

import structlog

# Set up logger
logger = structlog.get_logger(__name__)

class TaskType(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    FOLLOWUP = "followup"

class ActionType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    EXTRACT = "extract"
    WAIT = "wait"
    SCREENSHOT = "screenshot"

@dataclass
class Action:
    type: ActionType
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    direction: Optional[str] = None
    amount: Optional[int] = None
    reasoning: Optional[str] = None

@dataclass 
class Plan:
    steps: List[Action]
    task_type: TaskType
    confidence: float

class TaskClassifier:
    """Classifies tasks as simple vs complex using GPT-OSS"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    async def classify_task(self, task: str, context: Dict[str, Any]) -> TaskType:
        """Classify if task needs planning or can be executed directly"""
        
        prompt = f"""
        Analyze this browser task and classify it:
        
        Task: "{task}"
        Context: Page is at {context.get('url', 'unknown')}
        
        Classification Rules:
        - SIMPLE: Single action (click button, navigate to URL, scroll, extract text)
        - COMPLEX: Multiple steps needed (search + click result, fill form + submit, multi-page workflow)
        - FOLLOWUP: Continues from previous conversation
        
        Respond with just: SIMPLE, COMPLEX, or FOLLOWUP
        """
        
        try:
            response = await self.ai_client.chat(prompt, context={})
            classification = response["content"].strip().upper()
            
            if "SIMPLE" in classification:
                return TaskType.SIMPLE
            elif "COMPLEX" in classification:  
                return TaskType.COMPLEX
            elif "FOLLOWUP" in classification:
                return TaskType.FOLLOWUP
            else:
                # Default to simple for unclear cases
                return TaskType.SIMPLE
                
        except Exception as e:
            logger.error("Classification failed", error=str(e))
            return TaskType.SIMPLE

class ActionPlanner:
    """Creates multi-step plans for complex tasks"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    async def create_plan(self, task: str, context: Dict[str, Any]) -> Plan:
        """Generate a step-by-step plan for complex tasks"""
        
        prompt = f"""
        You are an expert browser automation planner. Create a step-by-step plan for this task.
        
        TASK: "{task}"
        CURRENT PAGE: {context.get('url', 'unknown')}
        
        AVAILABLE ACTIONS:
        - NAVIGATE: Go to a URL  
        - CLICK: Click an element
        - TYPE: Type text in an element
        - SCROLL: Scroll page (up/down/top/bottom)
        - EXTRACT: Get text/data from page
        - WAIT: Wait for page to load
        - SCREENSHOT: Take page screenshot
        
        RESPOND WITH ONLY VALID JSON - NO OTHER TEXT:
        
        {{
            "steps": [
                {{
                    "action": "NAVIGATE",
                    "url": "https://google.com", 
                    "reasoning": "Go to Google homepage"
                }},
                {{
                    "action": "CLICK",
                    "selector": "input[name='q']",
                    "reasoning": "Focus search input field"
                }},
                {{
                    "action": "TYPE",
                    "text": "AI news",
                    "reasoning": "Enter search query"
                }},
                {{
                    "action": "CLICK",
                    "selector": "input[type='submit']",
                    "reasoning": "Submit search"
                }}
            ],
            "confidence": 0.9
        }}
        
        IMPORTANT: Return ONLY the JSON object, no explanations, no markdown formatting.
        """
        
        try:
            response = await self.ai_client.chat(prompt, context={})
            content = response["content"].strip()
            
            # Try to extract JSON if response has extra text
            if not content.startswith('{'):
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            plan_data = json.loads(content)
            
            steps = []
            for step in plan_data.get("steps", []):
                action_type = ActionType(step["action"].lower())
                action = Action(
                    type=action_type,
                    selector=step.get("selector"),
                    text=step.get("text"), 
                    url=step.get("url"),
                    direction=step.get("direction"),
                    amount=step.get("amount"),
                    reasoning=step.get("reasoning")
                )
                steps.append(action)
            
            return Plan(
                steps=steps,
                task_type=TaskType.COMPLEX,
                confidence=plan_data.get("confidence", 0.7)
            )
            
        except Exception as e:
            logger.error("Planning failed", error=str(e))
            # Fallback simple plan
            return Plan(
                steps=[Action(type=ActionType.EXTRACT, reasoning="Fallback: extract page info")],
                task_type=TaskType.SIMPLE, 
                confidence=0.3
            )

class ActionParser:
    """Parses AI responses into executable browser actions"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    async def parse_action(self, response: str, context: Dict[str, Any]) -> List[Action]:
        """Extract actionable commands from AI response"""
        
        # Keywords that indicate actions
        action_keywords = {
            "click": ActionType.CLICK,
            "navigate": ActionType.NAVIGATE,
            "type": ActionType.TYPE, 
            "scroll": ActionType.SCROLL,
            "extract": ActionType.EXTRACT,
            "screenshot": ActionType.SCREENSHOT
        }
        
        actions = []
        
        # Simple keyword-based parsing
        response_lower = response.lower()
        
        for keyword, action_type in action_keywords.items():
            if keyword in response_lower:
                # Extract relevant parameters based on action type
                if action_type == ActionType.NAVIGATE:
                    # Look for URLs
                    import re
                    urls = re.findall(r'https?://[^\s]+', response)
                    if urls:
                        actions.append(Action(type=action_type, url=urls[0]))
                
                elif action_type == ActionType.CLICK:
                    # Look for quoted selectors or button descriptions
                    actions.append(Action(type=action_type, selector="button", reasoning="Parsed click action"))
                
                elif action_type == ActionType.TYPE:
                    # Look for quoted text
                    import re
                    quoted_text = re.findall(r'"([^"]*)"', response)
                    if quoted_text:
                        actions.append(Action(type=action_type, text=quoted_text[0]))
                
                else:
                    actions.append(Action(type=action_type))
        
        return actions if actions else [Action(type=ActionType.EXTRACT, reasoning="Default extraction")]

class BrowserAgentEnhanced:
    """Enhanced Browser Agent with intelligent planning and action parsing"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.classifier = TaskClassifier(ai_client)
        self.planner = ActionPlanner(ai_client) 
        self.parser = ActionParser(ai_client)
        
        self.conversation_history = []
        self.current_context = {}
    
    async def process_task(self, task: str, page_context: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point - process any browser task intelligently"""
        
        logger.info("Processing task", task=task[:100])
        
        try:
            # Update context
            self.current_context.update(page_context)
            
            # Step 1: Classify the task
            task_type = await self.classifier.classify_task(task, self.current_context)
            logger.info("Task classified", type=task_type.value)
            
            # Step 2: Handle based on type
            if task_type == TaskType.SIMPLE:
                return await self.handle_simple_task(task)
            elif task_type == TaskType.COMPLEX:
                return await self.handle_complex_task(task)
            else:  # FOLLOWUP
                return await self.handle_followup_task(task)
                
        except Exception as e:
            logger.error("Task processing failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "actions": [],
                "response": "I encountered an error processing your request."
            }
    
    async def handle_simple_task(self, task: str) -> Dict[str, Any]:
        """Handle simple tasks with direct AI response + action parsing"""
        
        # Get AI response with current context
        ai_response = await self.ai_client.chat(
            message=task,
            context=self.current_context
        )
        
        # Parse actions from response
        actions = await self.parser.parse_action(ai_response["content"], self.current_context)
        
        return {
            "success": True,
            "response": ai_response["content"],
            "actions": [self._action_to_dict(action) for action in actions],
            "task_type": "simple",
            "metadata": ai_response.get("usage", {})
        }
    
    async def handle_complex_task(self, task: str) -> Dict[str, Any]:
        """Handle complex tasks with planning"""
        
        # Create plan
        plan = await self.planner.create_plan(task, self.current_context)
        
        # Convert plan to response format
        response = f"I'll help you {task}. Here's my plan:\n\n"
        for i, step in enumerate(plan.steps, 1):
            response += f"{i}. {step.reasoning}\n"
        
        return {
            "success": True,
            "response": response,
            "actions": [self._action_to_dict(action) for action in plan.steps],
            "task_type": "complex", 
            "plan_confidence": plan.confidence,
            "metadata": {"planned_steps": len(plan.steps)}
        }
    
    async def handle_followup_task(self, task: str) -> Dict[str, Any]:
        """Handle followup tasks using conversation history"""
        
        # Add conversation context
        context_with_history = {
            **self.current_context,
            "conversation_history": self.conversation_history[-3:]  # Last 3 messages
        }
        
        ai_response = await self.ai_client.chat(
            message=task,
            context=context_with_history
        )
        
        actions = await self.parser.parse_action(ai_response["content"], context_with_history)
        
        return {
            "success": True,
            "response": ai_response["content"],
            "actions": [self._action_to_dict(action) for action in actions],
            "task_type": "followup",
            "metadata": ai_response.get("usage", {})
        }
    
    def _action_to_dict(self, action: Action) -> Dict[str, Any]:
        """Convert Action to dictionary for JSON serialization"""
        return {
            "type": action.type.value,
            "selector": action.selector,
            "text": action.text,
            "url": action.url, 
            "direction": action.direction,
            "amount": action.amount,
            "reasoning": action.reasoning
        }
    
    def add_to_history(self, user_message: str, ai_response: str):
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "user": user_message,
            "ai": ai_response,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]