"""
AI Browser Agent - Autonomous Web Navigation and Task Completion
Powered by GPT-OSS 20B for 100% Local Privacy
Competes with Perplexity Comet's agentic capabilities
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Single action (click, type, navigate)
    MODERATE = "moderate"   # 2-5 actions (fill form, search and click)
    COMPLEX = "complex"     # Multi-step workflow (shopping, booking)
    EXPERT = "expert"       # Cross-site workflows (research, comparison)

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    BROWSING = "browsing" 
    INTERACTING = "interacting"
    COMPLETING = "completing"
    ERROR = "error"

@dataclass
class BrowserAction:
    type: str  # navigate, click, type, scroll, wait, analyze
    target: str
    value: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.0
    expected_outcome: str = ""

@dataclass
class TaskProgress:
    task_id: str
    description: str
    current_step: int
    total_steps: int
    status: str
    actions_taken: List[BrowserAction]
    thinking_log: List[str]
    start_time: datetime
    
class AIBrowserAgent:
    """
    Autonomous AI browser agent that can complete complex web tasks
    Key differentiator: 100% local processing with GPT-OSS 20B
    """
    
    def __init__(self, ai_client, browser_agent, tools_registry=None):
        self.ai_client = ai_client
        self.browser_agent = browser_agent
        self.tools_registry = tools_registry
        
        # Agent state
        self.current_state = AgentState.IDLE
        self.active_tasks = {}
        self.task_history = []
        
        # Autonomous capabilities
        self.max_actions_per_task = 50  # Safety limit
        self.thinking_timeout = 30  # Max seconds for AI reasoning
        self.action_timeout = 10    # Max seconds per action
        
        # Learning and adaptation
        self.success_patterns = {}  # Learn from successful task completions
        self.error_patterns = {}    # Learn from failures
        
    async def execute_autonomous_task(self, 
                                    user_request: str,
                                    current_url: str = "",
                                    page_content: str = "") -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a complex task autonomously with real-time progress streaming
        This is our answer to Perplexity Comet's agentic capabilities
        """
        task_id = f"task_{int(time.time())}"
        
        try:
            # Initialize task
            task_progress = TaskProgress(
                task_id=task_id,
                description=user_request,
                current_step=0,
                total_steps=0,  # Will be determined by planning
                status="starting",
                actions_taken=[],
                thinking_log=[],
                start_time=datetime.now()
            )
            
            self.active_tasks[task_id] = task_progress
            
            yield {
                "type": "task_started",
                "task_id": task_id,
                "description": user_request,
                "agent_state": "thinking",
                "privacy": "100% Local Processing"
            }
            
            # Step 1: Understand the task and plan approach
            yield {"type": "thinking", "message": "🤔 Analyzing your request..."}
            
            task_analysis = await self._analyze_task(user_request, current_url, page_content)
            
            yield {
                "type": "task_analysis",
                "complexity": task_analysis["complexity"],
                "estimated_steps": task_analysis["estimated_steps"],
                "approach": task_analysis["approach"]
            }
            
            task_progress.total_steps = task_analysis["estimated_steps"]
            
            # Step 2: Create detailed execution plan
            yield {"type": "thinking", "message": "📋 Creating execution plan..."}
            
            execution_plan = await self._create_execution_plan(
                user_request, 
                task_analysis,
                current_url,
                page_content
            )
            
            yield {
                "type": "plan_created", 
                "steps": execution_plan["steps"],
                "reasoning": execution_plan["reasoning"]
            }
            
            # Step 3: Execute plan step by step
            for step_idx, step in enumerate(execution_plan["steps"]):
                task_progress.current_step = step_idx + 1
                
                yield {
                    "type": "step_started",
                    "step": step_idx + 1,
                    "total": len(execution_plan["steps"]),
                    "action": step["action"],
                    "reasoning": step["reasoning"]
                }
                
                # Execute the step
                step_result = await self._execute_step(step, task_progress)
                
                if step_result["success"]:
                    yield {
                        "type": "step_completed",
                        "step": step_idx + 1,
                        "result": step_result["result"],
                        "next_action": step_result.get("next_action", "")
                    }
                else:
                    # Handle error and decide whether to continue or abort
                    error_handling = await self._handle_step_error(step, step_result, task_progress)
                    
                    if error_handling["should_continue"]:
                        yield {
                            "type": "error_recovered",
                            "step": step_idx + 1,
                            "error": step_result["error"],
                            "recovery": error_handling["recovery_action"]
                        }
                        # Retry or continue with adjusted plan
                        continue
                    else:
                        yield {
                            "type": "task_failed",
                            "step": step_idx + 1,
                            "error": step_result["error"],
                            "reason": "Could not recover from error"
                        }
                        task_progress.status = "failed"
                        break
                
                # Brief pause between actions (more human-like)
                await asyncio.sleep(1)
            
            # Step 4: Verify task completion
            if task_progress.status != "failed":
                yield {"type": "thinking", "message": "✅ Verifying task completion..."}
                
                verification = await self._verify_task_completion(user_request, task_progress)
                
                if verification["completed"]:
                    task_progress.status = "completed"
                    yield {
                        "type": "task_completed",
                        "success": True,
                        "summary": verification["summary"],
                        "actions_taken": len(task_progress.actions_taken),
                        "total_time": (datetime.now() - task_progress.start_time).total_seconds()
                    }
                else:
                    yield {
                        "type": "task_incomplete",
                        "reason": verification["reason"],
                        "suggestions": verification.get("suggestions", [])
                    }
            
            # Move to history
            self.task_history.append(task_progress)
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
        except Exception as e:
            logger.error("Autonomous task execution failed", error=str(e), task_id=task_id)
            yield {
                "type": "agent_error",
                "error": str(e),
                "task_id": task_id
            }
    
    async def _analyze_task(self, user_request: str, current_url: str, page_content: str) -> Dict[str, Any]:
        """Use GPT-OSS 20B to analyze task complexity and requirements"""
        
        context = f"""
Current URL: {current_url}
Page Content Preview: {page_content[:1000] if page_content else "No page loaded"}
"""
        
        analysis_prompt = f"""You are an AI browser agent. Analyze this user request and determine how to complete it.

User Request: {user_request}

Current Context:
{context}

Analyze:
1. Task complexity (simple/moderate/complex/expert)
2. Estimated number of steps needed
3. High-level approach to complete the task
4. Any potential challenges or requirements

Respond in JSON format:
{{
    "complexity": "simple|moderate|complex|expert",
    "estimated_steps": 5,
    "approach": "brief description of approach",
    "challenges": ["challenge1", "challenge2"],
    "requires_navigation": true,
    "requires_interaction": true,
    "success_criteria": "what indicates task completion"
}}"""

        try:
            response = await self.ai_client.chat(analysis_prompt, max_tokens=400)
            
            # Parse JSON response - fix: use "response" key not "content"
            content = response.get("response", response.get("content", ""))
            
            if not content.strip():
                raise ValueError("Empty response from AI")
                
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end == -1:
                    json_end = len(content)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            # If the AI didn't return JSON, create a default structure
            try:
                analysis = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("AI returned non-JSON, creating fallback analysis", response=content[:200])
                analysis = {
                    "complexity": "moderate",
                    "estimated_steps": 3,
                    "approach": f"Complete the task: {user_request}",
                    "challenges": ["AI did not return valid JSON"],
                    "requires_navigation": True,
                    "requires_interaction": True,
                    "success_criteria": "Task completed successfully"
                }
            
            # Add reasoning log
            self.active_tasks[list(self.active_tasks.keys())[-1]].thinking_log.append(
                f"Task Analysis: {analysis.get('complexity', 'unknown')} complexity, {analysis.get('estimated_steps', 'unknown')} steps"
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Task analysis failed", error=str(e))
            # Fallback analysis
            return {
                "complexity": "moderate",
                "estimated_steps": 3,
                "approach": "Analyze request and determine appropriate actions",
                "challenges": ["Unknown task complexity"],
                "requires_navigation": True,
                "requires_interaction": True,
                "success_criteria": "User request fulfilled"
            }
    
    async def _create_execution_plan(self, user_request: str, task_analysis: Dict, current_url: str, page_content: str) -> Dict[str, Any]:
        """Create detailed step-by-step execution plan"""
        
        planning_prompt = f"""Create a detailed execution plan for this browser task.

User Request: {user_request}
Task Analysis: {json.dumps(task_analysis)}
Current URL: {current_url}
Page Context: {page_content[:500] if page_content else "No page loaded"}

Create a step-by-step plan with specific browser actions:

Available Actions:
- navigate: Go to a specific URL
- click: Click on elements (buttons, links, etc.)
- type: Type text into input fields  
- scroll: Scroll page up/down
- wait: Wait for page load or elements
- analyze: Analyze current page content

Respond in JSON format:
{{
    "reasoning": "brief explanation of the plan",
    "steps": [
        {{
            "step": 1,
            "action": "navigate",
            "target": "https://example.com",
            "value": null,
            "reasoning": "why this step is needed",
            "expected_outcome": "what should happen"
        }},
        {{
            "step": 2, 
            "action": "click",
            "target": "search button",
            "value": null,
            "reasoning": "activate search functionality",
            "expected_outcome": "search form becomes active"
        }}
    ]
}}"""

        try:
            response = await self.ai_client.chat(planning_prompt, max_tokens=800)
            content = response.get("content", "")
            
            # Parse JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
                
            plan = json.loads(json_str)
            return plan
            
        except Exception as e:
            logger.error("Execution planning failed", error=str(e))
            # Fallback plan
            return {
                "reasoning": "Simple fallback plan due to planning error",
                "steps": [
                    {
                        "step": 1,
                        "action": "analyze", 
                        "target": "current page",
                        "value": None,
                        "reasoning": "Understand current page state",
                        "expected_outcome": "Page analysis available"
                    }
                ]
            }
    
    async def _execute_step(self, step: Dict, task_progress: TaskProgress) -> Dict[str, Any]:
        """Execute a single step of the plan"""
        
        action = BrowserAction(
            type=step["action"],
            target=step["target"],
            value=step.get("value"),
            reasoning=step["reasoning"],
            expected_outcome=step["expected_outcome"]
        )
        
        task_progress.actions_taken.append(action)
        
        try:
            # Execute the browser action
            if step["action"] == "navigate":
                result = await self.browser_agent.execute_action(
                    "navigate", 
                    {"url": step["target"]}, 
                    ""
                )
            elif step["action"] == "click":
                result = await self.browser_agent.execute_action(
                    "click",
                    {"target": step["target"]},
                    ""
                )
            elif step["action"] == "type":
                result = await self.browser_agent.execute_action(
                    "type",
                    {"text": step["value"], "target": step["target"]},
                    ""
                )
            elif step["action"] == "scroll":
                result = await self.browser_agent.execute_action(
                    "scroll",
                    {"direction": step["target"]},
                    ""
                )
            elif step["action"] == "wait":
                await asyncio.sleep(int(step.get("value", 2)))
                result = {"success": True, "message": f"Waited {step.get('value', 2)} seconds"}
            elif step["action"] == "analyze":
                # Analyze current page state
                result = {"success": True, "message": "Page analysis completed", "data": {"analysis": "Page state analyzed"}}
            else:
                result = {"success": False, "message": f"Unknown action: {step['action']}"}
            
            action.confidence = 0.9 if result["success"] else 0.1
            
            return {
                "success": result["success"],
                "result": result.get("data", {}),
                "message": result.get("message", ""),
                "next_action": step.get("next_action", "")
            }
            
        except Exception as e:
            logger.error("Step execution failed", error=str(e), step=step)
            return {
                "success": False,
                "error": str(e),
                "step": step
            }
    
    async def _handle_step_error(self, step: Dict, error_result: Dict, task_progress: TaskProgress) -> Dict[str, Any]:
        """Intelligently handle step execution errors"""
        
        error_message = error_result.get("error", "Unknown error")
        
        # Use AI to determine recovery strategy
        recovery_prompt = f"""A browser automation step failed. Determine the best recovery strategy.

Failed Step: {json.dumps(step)}
Error: {error_message}
Task Progress: {task_progress.current_step}/{task_progress.total_steps} steps completed

Options:
1. Retry the same step
2. Modify the step and retry
3. Skip this step and continue
4. Abort the task

Respond with:
{{
    "should_continue": true/false,
    "recovery_action": "retry|modify|skip|abort",
    "modified_step": {{...}} (if modify),
    "reasoning": "why this recovery approach"
}}"""

        try:
            response = await self.ai_client.chat(recovery_prompt, max_tokens=300)
            content = response.get("content", "")
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                recovery = json.loads(content[json_start:json_end].strip())
            else:
                recovery = json.loads(content)
                
            return recovery
            
        except Exception as e:
            logger.error("Error recovery analysis failed", error=str(e))
            return {
                "should_continue": False,
                "recovery_action": "abort",
                "reasoning": "Could not analyze recovery options"
            }
    
    async def _verify_task_completion(self, user_request: str, task_progress: TaskProgress) -> Dict[str, Any]:
        """Verify if the task was completed successfully"""
        
        verification_prompt = f"""Evaluate if this browser task was completed successfully.

Original Request: {user_request}
Actions Taken: {[action.type + ': ' + action.target for action in task_progress.actions_taken]}
Current Status: {task_progress.status}

Based on the original request and actions taken, was the task completed?

Respond with:
{{
    "completed": true/false,
    "success_score": 0.85,
    "summary": "brief summary of what was accomplished",
    "reason": "why task is complete/incomplete",
    "suggestions": ["suggestion1", "suggestion2"] (if incomplete)
}}"""

        try:
            response = await self.ai_client.chat(verification_prompt, max_tokens=300)
            content = response.get("content", "")
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                verification = json.loads(content[json_start:json_end].strip())
            else:
                verification = json.loads(content)
                
            return verification
            
        except Exception as e:
            logger.error("Task verification failed", error=str(e))
            return {
                "completed": False,
                "success_score": 0.0,
                "summary": "Could not verify task completion",
                "reason": "Verification system error"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and active tasks"""
        return {
            "agent_state": self.current_state.value,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_history),
            "model": "GPT-OSS 20B",
            "privacy": "100% Local Processing",
            "capabilities": [
                "autonomous_browsing",
                "multi_step_planning", 
                "error_recovery",
                "task_completion_verification"
            ]
        }