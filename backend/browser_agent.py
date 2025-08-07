"""
Browser Agent for AI Browser
Handles browser automation actions and coordinates with the AI model.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)

@dataclass
class WorkflowStep:
    """Represents a single step in a multi-step workflow"""
    id: str
    action: Dict[str, Any]
    status: str = "pending"  # pending, executing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = None  # List of step IDs this step depends on
    validation_rules: List[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.validation_rules is None:
            self.validation_rules = []
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass 
class Workflow:
    """Represents a complete multi-step workflow"""
    id: str
    name: str
    steps: List[WorkflowStep]
    status: str = "pending"  # pending, executing, completed, failed, paused
    current_step: int = 0
    context: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now()

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    WAIT = "wait"
    FIND = "find"
    EXTRACT = "extract"

class BrowserAgent:
    def __init__(self):
        self.action_handlers = {
            ActionType.CLICK.value: self._handle_click,
            ActionType.TYPE.value: self._handle_type,
            ActionType.NAVIGATE.value: self._handle_navigate,
            ActionType.SCROLL.value: self._handle_scroll,
            ActionType.WAIT.value: self._handle_wait,
            ActionType.FIND.value: self._handle_find,
            ActionType.EXTRACT.value: self._handle_extract,
        }
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_history: List[Workflow] = []
    
    async def parse_actions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse potential browser actions from AI response"""
        actions = []
        
        try:
            # Look for action patterns in the AI response
            action_patterns = [
                # Explicit action format: ACTION(parameters)
                (r'CLICK\(([^)]+)\)', ActionType.CLICK),
                (r'TYPE\(([^)]+)\)', ActionType.TYPE),
                (r'NAVIGATE\(([^)]+)\)', ActionType.NAVIGATE),
                (r'SCROLL\(([^)]+)\)', ActionType.SCROLL),
                
                # Natural language patterns
                (r'click (?:the |on )?["\']([^"\']+)["\']', ActionType.CLICK),
                (r'click (?:the )?(\w+(?:\s+\w+)*) button', ActionType.CLICK),
                (r'type ["\']([^"\']+)["\']', ActionType.TYPE),
                (r'enter ["\']([^"\']+)["\']', ActionType.TYPE),
                (r'navigate to ["\']([^"\']+)["\']', ActionType.NAVIGATE),
                (r'go to ["\']([^"\']+)["\']', ActionType.NAVIGATE),
                (r'scroll (\w+)', ActionType.SCROLL),
            ]
            
            for pattern, action_type in action_patterns:
                matches = re.finditer(pattern, ai_response, re.IGNORECASE)
                for match in matches:
                    param = match.group(1)
                    
                    if action_type == ActionType.CLICK:
                        actions.append({
                            'type': action_type.value,
                            'parameters': {'target': param.strip()}
                        })
                    elif action_type == ActionType.TYPE:
                        # Extract target if specified
                        if ' in ' in param or ' into ' in param:
                            parts = re.split(r' in | into ', param, 1)
                            if len(parts) == 2:
                                text, target = parts
                                actions.append({
                                    'type': action_type.value,
                                    'parameters': {'text': text.strip(), 'target': target.strip()}
                                })
                            else:
                                actions.append({
                                    'type': action_type.value,
                                    'parameters': {'text': param.strip()}
                                })
                        else:
                            actions.append({
                                'type': action_type.value,
                                'parameters': {'text': param.strip()}
                            })
                    elif action_type == ActionType.NAVIGATE:
                        actions.append({
                            'type': action_type.value,
                            'parameters': {'url': param.strip()}
                        })
                    elif action_type == ActionType.SCROLL:
                        actions.append({
                            'type': action_type.value,
                            'parameters': {'direction': param.strip().lower()}
                        })
            
            # Look for JSON action blocks
            json_actions = self._extract_json_actions(ai_response)
            actions.extend(json_actions)
            
            logger.debug("Parsed actions from AI response", 
                        response_preview=ai_response[:200],
                        actions_count=len(actions))
            
            return actions
            
        except Exception as e:
            logger.error("Failed to parse actions", error=str(e))
            return []
    
    def _extract_json_actions(self, text: str) -> List[Dict[str, Any]]:
        """Extract action blocks in JSON format from text"""
        actions = []
        
        # Look for JSON blocks
        json_pattern = r'```json\s*(\[.*?\])\s*```'
        matches = re.finditer(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                json_text = match.group(1)
                parsed_actions = json.loads(json_text)
                
                if isinstance(parsed_actions, list):
                    for action in parsed_actions:
                        if isinstance(action, dict) and 'type' in action:
                            actions.append(action)
                            
            except json.JSONDecodeError:
                continue
        
        return actions
    
    async def execute_action(self, 
                           action_type: str, 
                           parameters: Dict[str, Any],
                           page_url: str) -> Dict[str, Any]:
        """Execute a browser automation action"""
        try:
            logger.info("Executing browser action", 
                       action_type=action_type,
                       parameters=parameters,
                       url=page_url)
            
            if action_type not in self.action_handlers:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}",
                    "data": None
                }
            
            handler = self.action_handlers[action_type]
            result = await handler(parameters, page_url)
            
            logger.info("Action executed", 
                       action_type=action_type,
                       success=result["success"],
                       message=result["message"])
            
            return result
            
        except Exception as e:
            logger.error("Action execution failed", 
                        action_type=action_type,
                        error=str(e))
            return {
                "success": False,
                "message": f"Action execution failed: {str(e)}",
                "data": None
            }
    
    async def _handle_click(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle click action with enhanced accessibility-based element finding"""
        target = parameters.get('target', '')
        
        if not target:
            return {
                "success": False,
                "message": "No target specified for click action",
                "data": None
            }
        
        try:
            # Try to use accessibility tree for enhanced element finding
            from accessibility_tree import accessibility_extractor
            
            # Extract accessibility tree for the page
            tree = await accessibility_extractor.extract_accessibility_tree(page_url)
            
            # Search for elements matching the target description
            matches = await accessibility_extractor.find_elements_by_description(tree, target)
            
            if matches:
                # Use the best match
                best_match = matches[0]
                element = best_match["node"]
                
                # Get multiple selector options
                selectors = element.get("selectors", [])
                primary_selector = selectors[0] if selectors else None
                
                return {
                    "success": True,
                    "message": f"Click action prepared for target: {target} (found with {best_match['confidence']:.1%} confidence)",
                    "data": {
                        "action": "click",
                        "selector_type": "accessibility",
                        "selector_value": primary_selector or target,
                        "selectors": selectors,  # Multiple fallback selectors
                        "element_info": {
                            "id": element.get("id"),
                            "name": element.get("name"),
                            "role": element.get("role"),
                            "bounds": element.get("bounds")
                        },
                        "match_confidence": best_match["confidence"],
                        "match_reasons": best_match["reasons"],
                        "instructions": f"Click on {element.get('name', target)} ({element.get('role', 'element')})"
                    }
                }
            else:
                # Fallback to basic text-based selector
                return {
                    "success": True,
                    "message": f"Click action prepared for target: {target} (basic selector)",
                    "data": {
                        "action": "click",
                        "selector_type": "text",
                        "selector_value": target,
                        "instructions": f"Find and click element containing text '{target}' or with matching selector"
                    }
                }
                
        except Exception as e:
            logger.warning("Failed to use accessibility tree for click action", error=str(e))
            
            # Fallback to original implementation
            return {
                "success": True,
                "message": f"Click action prepared for target: {target}",
                "data": {
                    "action": "click",
                    "selector_type": "text",  # or "id", "class", "css"
                    "selector_value": target,
                    "instructions": f"Find and click element containing text '{target}' or with matching selector"
                }
            }
    
    async def _handle_type(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle type action with enhanced accessibility-based field finding"""
        text = parameters.get('text', '')
        target = parameters.get('target', '')
        
        if not text:
            return {
                "success": False,
                "message": "No text specified for type action",
                "data": None
            }
        
        try:
            # If target is specified, try to find it using accessibility tree
            if target:
                from accessibility_tree import accessibility_extractor
                
                # Extract accessibility tree for the page
                tree = await accessibility_extractor.extract_accessibility_tree(page_url)
                
                # Search for input fields matching the target description
                search_query = f"{target} input textbox field"
                matches = await accessibility_extractor.find_elements_by_description(tree, search_query)
                
                # Filter for input-type elements
                input_matches = [m for m in matches if m["node"].get("role") in ["textbox", "combobox"]]
                
                if input_matches:
                    # Use the best input match
                    best_match = input_matches[0]
                    element = best_match["node"]
                    
                    # Get selector options
                    selectors = element.get("selectors", [])
                    primary_selector = selectors[0] if selectors else None
                    
                    return {
                        "success": True,
                        "message": f"Type action prepared: '{text}' in {element.get('name', target)}",
                        "data": {
                            "action": "type",
                            "text": text,
                            "target": target,
                            "selector_type": "accessibility",
                            "selector_value": primary_selector or target,
                            "selectors": selectors,
                            "element_info": {
                                "id": element.get("id"),
                                "name": element.get("name"),
                                "role": element.get("role"),
                                "placeholder": element.get("properties", {}).get("placeholder")
                            },
                            "match_confidence": best_match["confidence"],
                            "instructions": f"Type '{text}' in {element.get('name', 'input field')}"
                        }
                    }
            
            # Fallback to original implementation
            return {
                "success": True,
                "message": f"Type action prepared: '{text}'" + (f" in {target}" if target else ""),
                "data": {
                    "action": "type",
                    "text": text,
                    "target": target,
                    "selector_type": "auto",  # Auto-detect input field
                    "instructions": f"Type '{text}'" + (f" in field '{target}'" if target else " in focused input field")
                }
            }
            
        except Exception as e:
            logger.warning("Failed to use accessibility tree for type action", error=str(e))
            
            # Fallback to original implementation
            return {
                "success": True,
                "message": f"Type action prepared: '{text}'" + (f" in {target}" if target else ""),
                "data": {
                    "action": "type",
                    "text": text,
                    "target": target,
                    "selector_type": "auto",
                    "instructions": f"Type '{text}'" + (f" in field '{target}'" if target else " in focused input field")
                }
            }
    
    async def _handle_navigate(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle navigate action"""
        url = parameters.get('url', '')
        
        if not url:
            return {
                "success": False,
                "message": "No URL specified for navigate action",
                "data": None
            }
        
        # Validate and normalize URL
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('/'):
                url = 'https://' + url
            else:
                # Relative URL - resolve against current page
                from urllib.parse import urljoin
                url = urljoin(page_url, url)
        
        return {
            "success": True,
            "message": f"Navigate action prepared to: {url}",
            "data": {
                "action": "navigate",
                "url": url,
                "instructions": f"Navigate to {url}"
            }
        }
    
    async def _handle_scroll(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle scroll action"""
        direction = parameters.get('direction', 'down').lower()
        amount = parameters.get('amount', 'page')  # 'page', 'half', or pixel amount
        
        if direction not in ['up', 'down', 'left', 'right']:
            direction = 'down'
        
        return {
            "success": True,
            "message": f"Scroll action prepared: {direction} by {amount}",
            "data": {
                "action": "scroll",
                "direction": direction,
                "amount": amount,
                "instructions": f"Scroll {direction} by {amount}"
            }
        }
    
    async def _handle_wait(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle wait action"""
        duration = parameters.get('duration', 1)  # seconds
        condition = parameters.get('condition', None)  # element to wait for
        
        return {
            "success": True,
            "message": f"Wait action prepared: {duration}s" + (f" for {condition}" if condition else ""),
            "data": {
                "action": "wait",
                "duration": duration,
                "condition": condition,
                "instructions": f"Wait {duration} seconds" + (f" for element '{condition}'" if condition else "")
            }
        }
    
    async def _handle_find(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle find element action"""
        query = parameters.get('query', '')
        
        if not query:
            return {
                "success": False,
                "message": "No query specified for find action",
                "data": None
            }
        
        return {
            "success": True,
            "message": f"Find action prepared for: {query}",
            "data": {
                "action": "find",
                "query": query,
                "instructions": f"Find elements matching '{query}'"
            }
        }
    
    async def _handle_extract(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Handle extract data action"""
        target = parameters.get('target', 'text')
        selector = parameters.get('selector', '')
        
        return {
            "success": True,
            "message": f"Extract action prepared: {target}" + (f" from {selector}" if selector else ""),
            "data": {
                "action": "extract",
                "target": target,
                "selector": selector,
                "instructions": f"Extract {target}" + (f" from elements matching '{selector}'" if selector else " from page")
            }
        }
    
    def suggest_actions_for_page(self, page_content: str, user_intent: str) -> List[str]:
        """Suggest possible actions based on page content and user intent"""
        suggestions = []
        
        # Simple heuristics for common actions
        if "login" in user_intent.lower() or "sign in" in user_intent.lower():
            if "password" in page_content.lower():
                suggestions.append("This looks like a login page. I can help you fill in the username and password fields.")
            if "sign in" in page_content.lower() or "login" in page_content.lower():
                suggestions.append("I can click the sign-in button for you.")
        
        if "search" in user_intent.lower():
            if "search" in page_content.lower() or "input" in page_content.lower():
                suggestions.append("I can help you search by typing in the search box.")
        
        if "buy" in user_intent.lower() or "purchase" in user_intent.lower():
            if "add to cart" in page_content.lower() or "buy now" in page_content.lower():
                suggestions.append("I can add this item to your cart or proceed with purchase.")
        
        return suggestions
    
    async def create_workflow(self, 
                            name: str,
                            actions: List[Dict[str, Any]], 
                            user_intent: str = "",
                            page_url: str = "") -> str:
        """Create a new multi-step workflow from a list of actions"""
        import uuid
        
        workflow_id = str(uuid.uuid4())
        
        # Convert actions to workflow steps
        steps = []
        for i, action in enumerate(actions):
            step_id = f"{workflow_id}_step_{i}"
            
            # Add validation rules based on action type
            validation_rules = self._get_validation_rules(action, user_intent)
            
            step = WorkflowStep(
                id=step_id,
                action=action,
                validation_rules=validation_rules
            )
            
            # Add dependencies (sequential by default)
            if i > 0:
                step.dependencies = [f"{workflow_id}_step_{i-1}"]
            
            steps.append(step)
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            steps=steps,
            context={
                "user_intent": user_intent,
                "page_url": page_url,
                "start_time": datetime.now().isoformat()
            }
        )
        
        self.active_workflows[workflow_id] = workflow
        
        logger.info("Created multi-step workflow", 
                   workflow_id=workflow_id,
                   steps_count=len(steps),
                   name=name)
        
        return workflow_id
    
    def _get_validation_rules(self, action: Dict[str, Any], user_intent: str) -> List[Dict[str, Any]]:
        """Generate validation rules for an action based on its type and context"""
        rules = []
        action_type = action.get('type', '')
        
        if action_type == 'navigate':
            rules.append({
                'type': 'url_change',
                'description': 'Verify page URL changed successfully',
                'expected_url_pattern': action.get('parameters', {}).get('url', '')
            })
            rules.append({
                'type': 'page_load',
                'description': 'Wait for page to fully load',
                'timeout': 10
            })
        
        elif action_type == 'click':
            rules.append({
                'type': 'element_exists',
                'description': 'Verify target element exists before clicking',
                'selector': action.get('parameters', {}).get('target', '')
            })
            rules.append({
                'type': 'element_clickable',
                'description': 'Verify element is clickable',
                'selector': action.get('parameters', {}).get('target', '')
            })
        
        elif action_type == 'type':
            rules.append({
                'type': 'input_field',
                'description': 'Verify input field is available and focusable',
                'selector': action.get('parameters', {}).get('target', 'input')
            })
        
        # Add intent-based validation
        if 'login' in user_intent.lower():
            if action_type == 'type' and 'password' in str(action.get('parameters', {})).lower():
                rules.append({
                    'type': 'secure_input',
                    'description': 'Verify password field is secure',
                    'check_type': 'password'
                })
        
        return rules
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a multi-step workflow with validation and error recovery"""
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "message": f"Workflow {workflow_id} not found",
                "data": None
            }
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = "executing"
        
        logger.info("Starting workflow execution", 
                   workflow_id=workflow_id,
                   total_steps=len(workflow.steps))
        
        try:
            for i, step in enumerate(workflow.steps):
                workflow.current_step = i
                
                # Check dependencies
                if not await self._check_step_dependencies(step, workflow):
                    step.status = "failed"
                    step.error = f"Dependencies not met: {step.dependencies}"
                    workflow.status = "failed"
                    break
                
                # Execute step with retries
                step_result = await self._execute_step_with_retries(step, workflow)
                
                if not step_result["success"]:
                    # Try error recovery
                    recovery_result = await self._attempt_error_recovery(step, workflow, step_result)
                    
                    if not recovery_result["success"]:
                        workflow.status = "failed"
                        logger.error("Workflow failed at step", 
                                   workflow_id=workflow_id,
                                   step_id=step.id,
                                   error=step.error)
                        break
                
                # Update workflow context with step results
                if step.result and step.result.get("data"):
                    workflow.context[f"step_{i}_result"] = step.result["data"]
                
                logger.info("Workflow step completed", 
                           workflow_id=workflow_id,
                           step_id=step.id,
                           status=step.status)
            
            # Check if all steps completed successfully
            if all(step.status == "completed" for step in workflow.steps):
                workflow.status = "completed"
                logger.info("Workflow completed successfully", 
                           workflow_id=workflow_id)
            
        except Exception as e:
            workflow.status = "failed"
            logger.error("Workflow execution failed", 
                        workflow_id=workflow_id,
                        error=str(e))
        
        # Move to history
        self.workflow_history.append(workflow)
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
        
        return {
            "success": workflow.status == "completed",
            "message": f"Workflow {workflow.status}",
            "data": {
                "workflow_id": workflow_id,
                "status": workflow.status,
                "steps_completed": sum(1 for s in workflow.steps if s.status == "completed"),
                "total_steps": len(workflow.steps),
                "context": workflow.context
            }
        }
    
    async def _check_step_dependencies(self, step: WorkflowStep, workflow: Workflow) -> bool:
        """Check if all dependencies for a step are satisfied"""
        if not step.dependencies:
            return True
        
        for dep_id in step.dependencies:
            dep_step = next((s for s in workflow.steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != "completed":
                return False
        
        return True
    
    async def _execute_step_with_retries(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute a workflow step with automatic retries"""
        step.status = "executing"
        
        for attempt in range(step.max_retries + 1):
            step.retry_count = attempt
            
            try:
                # Validate pre-conditions
                validation_result = await self._validate_step_preconditions(step, workflow)
                if not validation_result["success"]:
                    if attempt < step.max_retries:
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        step.status = "failed"
                        step.error = f"Pre-condition validation failed: {validation_result['message']}"
                        return validation_result
                
                # Execute the action
                action = step.action
                result = await self.execute_action(
                    action.get('type', ''),
                    action.get('parameters', {}),
                    workflow.context.get('page_url', '')
                )
                
                # Validate post-conditions
                if result["success"]:
                    post_validation = await self._validate_step_postconditions(step, workflow, result)
                    if post_validation["success"]:
                        step.status = "completed"
                        step.result = result
                        return result
                    else:
                        result = post_validation
                
                # If we get here, the step failed
                if attempt < step.max_retries:
                    logger.warning("Step failed, retrying", 
                                 step_id=step.id,
                                 attempt=attempt + 1,
                                 error=result.get("message", "Unknown error"))
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    step.status = "failed"
                    step.error = result.get("message", "Step execution failed")
                    return result
                    
            except Exception as e:
                if attempt < step.max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    step.status = "failed"
                    step.error = str(e)
                    return {
                        "success": False,
                        "message": f"Step execution failed after {step.max_retries} retries: {str(e)}",
                        "data": None
                    }
        
        return {
            "success": False,
            "message": "Step execution failed after all retries",
            "data": None
        }
    
    async def _validate_step_preconditions(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Validate preconditions before executing a step"""
        for rule in step.validation_rules:
            if rule['type'] == 'element_exists':
                # In a real implementation, this would check if element exists on page
                # For now, we simulate success
                pass
            elif rule['type'] == 'page_load':
                # Wait for page load
                await asyncio.sleep(0.5)
        
        return {"success": True, "message": "Pre-conditions validated"}
    
    async def _validate_step_postconditions(self, step: WorkflowStep, workflow: Workflow, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate postconditions after executing a step"""
        for rule in step.validation_rules:
            if rule['type'] == 'url_change':
                # In a real implementation, this would verify URL change
                pass
            elif rule['type'] == 'element_clickable':
                # In a real implementation, this would verify element state
                pass
        
        return {"success": True, "message": "Post-conditions validated"}
    
    async def _attempt_error_recovery(self, step: WorkflowStep, workflow: Workflow, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from step execution errors"""
        error_message = error_result.get("message", "").lower()
        
        # Common recovery strategies
        if "element not found" in error_message:
            # Try waiting for element to appear
            logger.info("Attempting recovery: waiting for element", step_id=step.id)
            await asyncio.sleep(2)
            return await self._execute_step_with_retries(step, workflow)
        
        elif "page not loaded" in error_message:
            # Try refreshing the page
            logger.info("Attempting recovery: page refresh", step_id=step.id)
            # In real implementation, would send refresh command to browser
            await asyncio.sleep(1)
            return await self._execute_step_with_retries(step, workflow)
        
        elif "network error" in error_message:
            # Wait and retry
            logger.info("Attempting recovery: network retry", step_id=step.id)
            await asyncio.sleep(3)
            return await self._execute_step_with_retries(step, workflow)
        
        # No recovery strategy available
        return {
            "success": False,
            "message": f"No recovery strategy for error: {error_message}",
            "data": None
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            # Check history
            workflow = next((w for w in self.workflow_history if w.id == workflow_id), None)
            if not workflow:
                return {
                    "success": False,
                    "message": "Workflow not found",
                    "data": None
                }
        
        return {
            "success": True,
            "message": "Workflow status retrieved",
            "data": {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "status": workflow.status,
                "current_step": workflow.current_step,
                "total_steps": len(workflow.steps),
                "steps": [
                    {
                        "id": step.id,
                        "status": step.status,
                        "retry_count": step.retry_count,
                        "error": step.error
                    } for step in workflow.steps
                ],
                "context": workflow.context,
                "created_at": workflow.created_at.isoformat()
            }
        }
    
    def pause_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Pause an active workflow"""
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "message": f"Active workflow {workflow_id} not found",
                "data": None
            }
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = "paused"
        
        logger.info("Workflow paused", workflow_id=workflow_id)
        
        return {
            "success": True,
            "message": f"Workflow {workflow_id} paused",
            "data": {"workflow_id": workflow_id, "status": "paused"}
        }
    
    def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Resume a paused workflow"""
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "message": f"Active workflow {workflow_id} not found",
                "data": None
            }
        
        workflow = self.active_workflows[workflow_id]
        if workflow.status != "paused":
            return {
                "success": False,
                "message": f"Workflow {workflow_id} is not paused (status: {workflow.status})",
                "data": None
            }
        
        workflow.status = "executing"
        logger.info("Workflow resumed", workflow_id=workflow_id)
        
        return {
            "success": True,
            "message": f"Workflow {workflow_id} resumed",
            "data": {"workflow_id": workflow_id, "status": "executing"}
        }
    
    async def cleanup(self):
        """Clean up resources"""
        # Cancel any running workflows
        for workflow_id in list(self.active_workflows.keys()):
            workflow = self.active_workflows[workflow_id]
            if workflow.status == "executing":
                workflow.status = "cancelled"
                self.workflow_history.append(workflow)
                del self.active_workflows[workflow_id]
                logger.info("Cancelled workflow during cleanup", workflow_id=workflow_id)
        
        logger.info("Browser agent cleanup completed")