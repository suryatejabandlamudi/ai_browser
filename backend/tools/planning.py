"""
Planning Tools for AI Browser
Advanced task planning, workflow orchestration, and validation.
Implements BrowserOS-style rolling-horizon planning for superior automation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union, Literal
import asyncio
import structlog
import json
from datetime import datetime
import uuid

from .base import AIBrowserTool, ToolCategory, ToolResult, BrowserContext

logger = structlog.get_logger(__name__)

# Planning Data Models

class TaskStep(BaseModel):
    """Individual step in a task plan"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = Field(description="Name of tool to execute")
    description: str = Field(description="Human-readable description of step")
    parameters: Dict[str, Any] = Field(description="Tool parameters")
    depends_on: Optional[List[str]] = Field(default=[], description="Step IDs this depends on")
    expected_outcome: str = Field(description="Expected result of this step")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=2, description="Maximum retries allowed")
    status: Literal["pending", "executing", "completed", "failed"] = Field(default="pending")

class TaskPlan(BaseModel):
    """Complete task execution plan"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_intent: str = Field(description="Original user request")
    complexity: Literal["simple", "complex", "followup"] = Field(description="Task complexity")
    steps: List[TaskStep] = Field(description="Ordered list of execution steps")
    current_step: int = Field(default=0, description="Currently executing step index")
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_duration: int = Field(description="Estimated completion time in seconds")
    success_criteria: List[str] = Field(description="Criteria for successful completion")

# Input Schemas

class ClassifyTaskInput(BaseModel):
    """Input for task classification"""
    user_message: str = Field(description="User's original request")
    page_context: Optional[str] = Field(None, description="Current page context")
    conversation_history: Optional[List[str]] = Field(default=[], description="Previous messages")
    page_url: Optional[str] = Field(None, description="Current page URL")

class PlanTaskInput(BaseModel):
    """Input for task planning"""
    user_intent: str = Field(description="What the user wants to accomplish")
    task_complexity: Literal["simple", "complex", "followup"] = Field(description="Task complexity level")
    page_context: Optional[str] = Field(None, description="Current page context")
    available_tools: List[str] = Field(description="Available tools for execution")
    planning_horizon: int = Field(default=5, description="Number of steps to plan ahead")

class ValidateStepInput(BaseModel):
    """Input for step validation"""
    step: TaskStep = Field(description="Step to validate")
    execution_result: Dict[str, Any] = Field(description="Result from step execution")
    expected_outcome: str = Field(description="Expected outcome for validation")
    page_state_before: Optional[Dict[str, Any]] = Field(None, description="Page state before step")
    page_state_after: Optional[Dict[str, Any]] = Field(None, description="Page state after step")

class ReplanTaskInput(BaseModel):
    """Input for task replanning"""
    original_plan: TaskPlan = Field(description="Original task plan")
    failed_step: TaskStep = Field(description="Step that failed")
    failure_reason: str = Field(description="Why the step failed")
    current_page_state: Optional[Dict[str, Any]] = Field(None, description="Current page state")

# Tool Implementations

class ClassificationTool(AIBrowserTool[ClassifyTaskInput]):
    """
    Intelligent task classification - determines execution strategy.
    Key to competing with Perplexity Comet's smart automation.
    """
    
    def __init__(self):
        super().__init__(
            name="classify_task",
            description="Classify user requests to determine optimal execution strategy",
            category=ToolCategory.PLANNING,
            input_schema=ClassifyTaskInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: ClassifyTaskInput, context: BrowserContext) -> ToolResult:
        """Classify task complexity and type"""
        
        try:
            # Analyze user message for task complexity indicators
            message_lower = params.user_message.lower()
            
            # Simple task indicators
            simple_indicators = [
                "click", "scroll", "find", "search", "go to", "navigate", 
                "what is", "show me", "extract", "get", "copy"
            ]
            
            # Complex task indicators  
            complex_indicators = [
                "fill out", "complete", "submit", "register", "sign up", "login",
                "buy", "purchase", "order", "checkout", "compare", "analyze",
                "multiple", "several", "all", "every", "batch"
            ]
            
            # Followup task indicators
            followup_indicators = [
                "also", "then", "next", "after that", "continue", "and then",
                "furthermore", "additionally", "moreover"
            ]
            
            # Count indicators
            simple_score = sum(1 for indicator in simple_indicators if indicator in message_lower)
            complex_score = sum(1 for indicator in complex_indicators if indicator in message_lower)
            followup_score = sum(1 for indicator in followup_indicators if indicator in message_lower)
            
            # Consider conversation history for followup detection
            if params.conversation_history and len(params.conversation_history) > 0:
                followup_score += 2
            
            # Determine classification
            if followup_score > 0 and params.conversation_history:
                classification = "followup"
                confidence = 0.7 + min(followup_score * 0.1, 0.3)
            elif complex_score > simple_score or any(word in message_lower for word in ["step", "process", "workflow"]):
                classification = "complex"
                confidence = 0.6 + min(complex_score * 0.1, 0.4)
            else:
                classification = "simple"
                confidence = 0.8 + min(simple_score * 0.05, 0.2)
            
            # Analyze page context for additional hints
            page_hints = []
            if params.page_context:
                if "form" in params.page_context.lower():
                    page_hints.append("form_present")
                    if classification == "simple":
                        classification = "complex"
                        confidence = max(confidence, 0.75)
                
                if "login" in params.page_context.lower() or "sign" in params.page_context.lower():
                    page_hints.append("authentication_page")
                    
                if "checkout" in params.page_context.lower() or "cart" in params.page_context.lower():
                    page_hints.append("ecommerce_flow")
                    classification = "complex"
                    confidence = max(confidence, 0.85)
            
            # Determine execution strategy
            if classification == "simple":
                strategy = "direct_execution"
                estimated_steps = 1
            elif classification == "complex":
                strategy = "rolling_horizon_planning"  
                estimated_steps = 3 + complex_score
            else:  # followup
                strategy = "contextual_continuation"
                estimated_steps = 2
            
            return ToolResult(
                success=True,
                message=f"Task classified as '{classification}' with {confidence:.0%} confidence",
                data={
                    "classification": classification,
                    "confidence": confidence,
                    "execution_strategy": strategy,
                    "estimated_steps": estimated_steps,
                    "indicators": {
                        "simple_score": simple_score,
                        "complex_score": complex_score,
                        "followup_score": followup_score
                    },
                    "page_hints": page_hints,
                    "reasoning": self._generate_reasoning(classification, confidence, page_hints)
                }
            )
            
        except Exception as e:
            logger.error(f"Task classification failed", error=str(e))
            return ToolResult(
                success=False,
                message="Task classification failed",
                error=str(e)
            )
    
    def _generate_reasoning(self, classification: str, confidence: float, page_hints: List[str]) -> str:
        """Generate human-readable reasoning for classification"""
        reasoning_parts = [f"Classified as {classification} task"]
        
        if confidence > 0.8:
            reasoning_parts.append("with high confidence")
        elif confidence > 0.6:
            reasoning_parts.append("with moderate confidence")
        else:
            reasoning_parts.append("with low confidence")
            
        if page_hints:
            reasoning_parts.append(f"based on page context ({', '.join(page_hints)})")
            
        return " ".join(reasoning_parts) + "."

class PlannerTool(AIBrowserTool[PlanTaskInput]):
    """
    Advanced task planner with rolling-horizon strategy.
    Core intelligence for competing with sophisticated AI browsers.
    """
    
    def __init__(self):
        super().__init__(
            name="plan_task",
            description="Create detailed execution plans for complex tasks with rolling-horizon strategy",
            category=ToolCategory.PLANNING,
            input_schema=PlanTaskInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: PlanTaskInput, context: BrowserContext) -> ToolResult:
        """Create comprehensive task execution plan"""
        
        try:
            # Create task plan based on complexity
            if params.task_complexity == "simple":
                plan = await self._create_simple_plan(params, context)
            elif params.task_complexity == "complex":
                plan = await self._create_complex_plan(params, context)
            else:  # followup
                plan = await self._create_followup_plan(params, context)
            
            # Estimate execution time
            total_time = sum(self._estimate_step_time(step) for step in plan.steps)
            plan.estimated_duration = total_time
            
            return ToolResult(
                success=True,
                message=f"Created execution plan with {len(plan.steps)} steps (estimated {total_time}s)",
                data={
                    "plan": plan.model_dump(),
                    "plan_id": plan.id,
                    "step_count": len(plan.steps),
                    "estimated_duration": total_time,
                    "complexity": params.task_complexity,
                    "planning_strategy": "rolling_horizon" if params.task_complexity == "complex" else "direct"
                }
            )
            
        except Exception as e:
            logger.error(f"Task planning failed", error=str(e))
            return ToolResult(
                success=False,
                message="Task planning failed",
                error=str(e)
            )
    
    async def _create_simple_plan(self, params: PlanTaskInput, context: BrowserContext) -> TaskPlan:
        """Create plan for simple, single-step tasks"""
        
        # Determine appropriate tool based on intent
        intent_lower = params.user_intent.lower()
        
        if any(word in intent_lower for word in ["click", "press", "tap"]):
            tool_name = "click"
            tool_params = {"element_description": params.user_intent}
        elif any(word in intent_lower for word in ["type", "enter", "input"]):
            tool_name = "type"
            tool_params = {"element_description": "input field", "text_content": ""}
        elif any(word in intent_lower for word in ["scroll", "move"]):
            tool_name = "scroll"
            tool_params = {"direction": "down"}
        elif any(word in intent_lower for word in ["navigate", "go to", "visit"]):
            tool_name = "navigate"
            tool_params = {"url": ""}
        else:
            tool_name = "extract_content"
            tool_params = {"extraction_type": "summary"}
        
        step = TaskStep(
            tool_name=tool_name,
            description=f"Execute: {params.user_intent}",
            parameters=tool_params,
            expected_outcome="User request completed successfully"
        )
        
        return TaskPlan(
            user_intent=params.user_intent,
            complexity="simple",
            steps=[step],
            success_criteria=["Single action completed without errors"]
        )
    
    async def _create_complex_plan(self, params: PlanTaskInput, context: BrowserContext) -> TaskPlan:
        """Create multi-step plan for complex tasks with rolling-horizon strategy"""
        
        steps = []
        
        # Step 1: Analyze current page state
        steps.append(TaskStep(
            tool_name="refresh_state",
            description="Analyze current page state and available elements",
            parameters={"extract_content": True, "extract_accessibility": True},
            expected_outcome="Page state captured for planning"
        ))
        
        # Analyze intent to determine workflow type
        intent_lower = params.user_intent.lower()
        
        if "form" in intent_lower or "fill" in intent_lower or "submit" in intent_lower:
            # Form filling workflow
            steps.extend(self._create_form_workflow(params))
        elif "buy" in intent_lower or "purchase" in intent_lower or "checkout" in intent_lower:
            # E-commerce workflow  
            steps.extend(self._create_ecommerce_workflow(params))
        elif "login" in intent_lower or "sign" in intent_lower:
            # Authentication workflow
            steps.extend(self._create_auth_workflow(params))
        else:
            # Generic multi-step workflow
            steps.extend(self._create_generic_workflow(params))
        
        # Add validation step
        steps.append(TaskStep(
            tool_name="validate_completion",
            description="Validate that user intent has been fulfilled",
            parameters={"user_intent": params.user_intent, "validation_type": "comprehensive"},
            expected_outcome="Task completion confirmed",
            depends_on=[steps[-1].id] if steps else []
        ))
        
        return TaskPlan(
            user_intent=params.user_intent,
            complexity="complex",
            steps=steps,
            success_criteria=[
                "All workflow steps completed successfully",
                "User intent achieved",
                "No critical errors encountered"
            ]
        )
    
    def _create_form_workflow(self, params: PlanTaskInput) -> List[TaskStep]:
        """Create form-filling workflow steps"""
        return [
            TaskStep(
                tool_name="analyze_form",
                description="Analyze form structure and required fields",
                parameters={"form_selector": "form", "detect_required_fields": True},
                expected_outcome="Form structure identified"
            ),
            TaskStep(
                tool_name="fill_form",
                description="Fill form fields intelligently",
                parameters={"auto_detect_fields": True, "validate_before_submit": True},
                expected_outcome="Form fields populated correctly"
            ),
            TaskStep(
                tool_name="click",
                description="Submit the form",
                parameters={"element_description": "submit button"},
                expected_outcome="Form submitted successfully"
            )
        ]
    
    def _create_ecommerce_workflow(self, params: PlanTaskInput) -> List[TaskStep]:
        """Create e-commerce purchase workflow"""
        return [
            TaskStep(
                tool_name="search_page",
                description="Find product or navigate to product page",
                parameters={"query": "product", "highlight": True},
                expected_outcome="Product located on page"
            ),
            TaskStep(
                tool_name="click",
                description="Add product to cart",
                parameters={"element_description": "add to cart button"},
                expected_outcome="Product added to shopping cart"
            ),
            TaskStep(
                tool_name="navigate",
                description="Go to checkout page",
                parameters={"url": "/checkout"},
                expected_outcome="Checkout page loaded"
            )
        ]
    
    def _create_auth_workflow(self, params: PlanTaskInput) -> List[TaskStep]:
        """Create authentication workflow"""
        return [
            TaskStep(
                tool_name="type",
                description="Enter username/email",
                parameters={"element_description": "username or email field"},
                expected_outcome="Username entered"
            ),
            TaskStep(
                tool_name="type",
                description="Enter password",
                parameters={"element_description": "password field"},
                expected_outcome="Password entered"
            ),
            TaskStep(
                tool_name="click",
                description="Click login button",
                parameters={"element_description": "login or sign in button"},
                expected_outcome="Login attempted"
            )
        ]
    
    def _create_generic_workflow(self, params: PlanTaskInput) -> List[TaskStep]:
        """Create generic multi-step workflow"""
        return [
            TaskStep(
                tool_name="search_page",
                description="Search for relevant elements on page",
                parameters={"query": params.user_intent[:50], "highlight": True},
                expected_outcome="Relevant content found"
            ),
            TaskStep(
                tool_name="click",
                description="Interact with primary element",
                parameters={"element_description": "main interactive element"},
                expected_outcome="Primary interaction completed"
            )
        ]
    
    def _estimate_step_time(self, step: TaskStep) -> int:
        """Estimate execution time for a step in seconds"""
        time_estimates = {
            "click": 1,
            "type": 2, 
            "navigate": 3,
            "scroll": 1,
            "fill_form": 5,
            "search_page": 2,
            "refresh_state": 2,
            "validate_completion": 3
        }
        return time_estimates.get(step.tool_name, 2)

class ValidatorTool(AIBrowserTool[ValidateStepInput]):
    """
    Step execution validator - ensures quality automation.
    Critical for reliability that beats cloud-based competitors.
    """
    
    def __init__(self):
        super().__init__(
            name="validate_step",
            description="Validate that a step executed successfully and achieved expected outcome",
            category=ToolCategory.VALIDATION,
            input_schema=ValidateStepInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: ValidateStepInput, context: BrowserContext) -> ToolResult:
        """Validate step execution results"""
        
        try:
            validation_result = {
                "step_successful": params.execution_result.get("success", False),
                "outcome_achieved": False,
                "confidence": 0.0,
                "issues": [],
                "recommendations": []
            }
            
            # Basic success validation
            if not validation_result["step_successful"]:
                validation_result["issues"].append("Tool execution reported failure")
                validation_result["recommendations"].append("Retry step with adjusted parameters")
                validation_result["confidence"] = 0.0
            else:
                validation_result["confidence"] = 0.7  # Base confidence for successful execution
            
            # Outcome-specific validation
            step_tool = params.step.tool_name
            
            if step_tool == "click":
                validation_result["outcome_achieved"] = self._validate_click_outcome(params)
            elif step_tool == "type":
                validation_result["outcome_achieved"] = self._validate_type_outcome(params)
            elif step_tool == "navigate":
                validation_result["outcome_achieved"] = self._validate_navigation_outcome(params)
            elif step_tool == "fill_form":
                validation_result["outcome_achieved"] = self._validate_form_outcome(params)
            else:
                # Generic validation
                validation_result["outcome_achieved"] = validation_result["step_successful"]
            
            # Adjust confidence based on outcome validation
            if validation_result["outcome_achieved"]:
                validation_result["confidence"] = min(validation_result["confidence"] + 0.2, 1.0)
            else:
                validation_result["confidence"] = max(validation_result["confidence"] - 0.3, 0.0)
                validation_result["issues"].append("Expected outcome not clearly achieved")
            
            # Page state change analysis
            if params.page_state_before and params.page_state_after:
                state_changes = self._analyze_state_changes(params.page_state_before, params.page_state_after)
                validation_result["state_changes"] = state_changes
                
                if state_changes.get("meaningful_changes", False):
                    validation_result["confidence"] += 0.1
                
            overall_success = (validation_result["step_successful"] and 
                             validation_result["outcome_achieved"] and 
                             validation_result["confidence"] > 0.6)
            
            return ToolResult(
                success=overall_success,
                message=f"Step validation {'passed' if overall_success else 'failed'} (confidence: {validation_result['confidence']:.0%})",
                data=validation_result
            )
            
        except Exception as e:
            logger.error(f"Step validation failed", error=str(e))
            return ToolResult(
                success=False,
                message="Step validation failed",
                error=str(e)
            )
    
    def _validate_click_outcome(self, params: ValidateStepInput) -> bool:
        """Validate click action outcome"""
        result_data = params.execution_result.get("data", {})
        return result_data.get("click_type") is not None
    
    def _validate_type_outcome(self, params: ValidateStepInput) -> bool:
        """Validate typing action outcome"""
        result_data = params.execution_result.get("data", {})
        return len(result_data.get("text_content", "")) > 0
    
    def _validate_navigation_outcome(self, params: ValidateStepInput) -> bool:
        """Validate navigation outcome"""
        result_data = params.execution_result.get("data", {})
        return result_data.get("url") is not None
    
    def _validate_form_outcome(self, params: ValidateStepInput) -> bool:
        """Validate form filling outcome"""
        result_data = params.execution_result.get("data", {})
        success_rate = result_data.get("success_rate", 0)
        return success_rate > 0.8
    
    def _analyze_state_changes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze page state changes"""
        # In real implementation, would do deep page state comparison
        return {
            "meaningful_changes": True,  # Mock meaningful change detection
            "url_changed": before.get("url") != after.get("url"),
            "content_changed": before.get("content_hash") != after.get("content_hash"),
            "elements_added": 0,  # Mock element change detection
            "elements_removed": 0
        }

# Register all planning tools
def register_planning_tools():
    """Register all planning tools in the global registry"""
    from .base import tool_registry
    
    tools = [
        ClassificationTool(),
        PlannerTool(),
        ValidatorTool()
    ]
    
    for tool in tools:
        tool_registry.register(tool)