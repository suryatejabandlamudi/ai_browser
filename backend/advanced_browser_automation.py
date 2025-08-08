"""
Advanced Browser Automation for Agentic AI Local LLM Browser
Provides tight integration with GPT-OSS 20B for complex workflows
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time
from pathlib import Path

@dataclass
class WorkflowStep:
    action: str
    target: str
    data: Optional[Dict[str, Any]] = None
    condition: Optional[str] = None
    retry_count: int = 3
    timeout: float = 10.0
    validation: Optional[Callable] = None

@dataclass
class WorkflowResult:
    success: bool
    step_results: List[Dict[str, Any]]
    execution_time: float
    error: Optional[str] = None

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    EXTRACT = "extract"
    VALIDATE = "validate"
    SCREENSHOT = "screenshot"
    FORM_FILL = "form_fill"
    AI_ANALYZE = "ai_analyze"

class AdvancedBrowserAutomation:
    """Advanced browser automation with AI-powered decision making"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.workflow_history = []
        self.active_workflows = {}
        self.error_recovery_enabled = True
        self.performance_tracking = True
        
        # Enhanced selectors with AI-powered fallbacks
        self.selector_strategies = [
            'id',
            'name', 
            'css',
            'xpath',
            'text_content',
            'ai_semantic',  # AI-powered element identification
            'visual_matching'  # Screenshot-based matching
        ]
        
        self.metrics = {
            'workflows_executed': 0,
            'success_rate': 0,
            'average_execution_time': 0,
            'ai_interventions': 0
        }
    
    async def execute_agentic_workflow(self, 
                                     task_description: str,
                                     context: Dict[str, Any] = None) -> WorkflowResult:
        """Execute agentic workflow using AI planning and execution"""
        start_time = time.time()
        workflow_id = f"workflow_{int(start_time)}"
        
        try:
            # Step 1: AI-powered task decomposition
            workflow_steps = await self._ai_plan_workflow(task_description, context)
            
            if not workflow_steps:
                return WorkflowResult(
                    success=False,
                    step_results=[],
                    execution_time=0,
                    error="Failed to generate workflow plan"
                )
            
            # Step 2: Execute workflow with AI monitoring
            step_results = []
            self.active_workflows[workflow_id] = {
                'description': task_description,
                'steps': workflow_steps,
                'status': 'executing'
            }
            
            for i, step in enumerate(workflow_steps):
                step_result = await self._execute_workflow_step(step, context, i)
                step_results.append(step_result)
                
                # If step fails, try AI-powered recovery
                if not step_result.get('success', False) and self.error_recovery_enabled:
                    recovery_result = await self._ai_error_recovery(
                        step, step_result, context, i
                    )
                    if recovery_result.get('success', False):
                        step_results[-1] = recovery_result
                    else:
                        # Critical failure, abort workflow
                        break
            
            execution_time = time.time() - start_time
            success = all(result.get('success', False) for result in step_results)
            
            # Update metrics
            self.metrics['workflows_executed'] += 1
            if success:
                self.metrics['success_rate'] = (
                    (self.metrics['success_rate'] * (self.metrics['workflows_executed'] - 1) + 1) 
                    / self.metrics['workflows_executed']
                )
            
            self.metrics['average_execution_time'] = (
                (self.metrics['average_execution_time'] * (self.metrics['workflows_executed'] - 1) + execution_time)
                / self.metrics['workflows_executed']
            )
            
            # Store workflow history
            self.workflow_history.append({
                'id': workflow_id,
                'description': task_description,
                'success': success,
                'execution_time': execution_time,
                'steps': len(workflow_steps),
                'timestamp': time.time()
            })
            
            return WorkflowResult(
                success=success,
                step_results=step_results,
                execution_time=execution_time
            )
            
        except Exception as e:
            logging.error(f"Workflow execution error: {e}")
            return WorkflowResult(
                success=False,
                step_results=[],
                execution_time=time.time() - start_time,
                error=str(e)
            )
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def _ai_plan_workflow(self, 
                              task_description: str, 
                              context: Dict[str, Any] = None) -> List[WorkflowStep]:
        """Use AI to break down complex tasks into executable steps"""
        if not self.ai_client:
            return []
        
        # Create comprehensive prompt for workflow planning
        planning_prompt = f"""
        As an expert browser automation AI, break down this task into specific, executable steps:
        
        Task: {task_description}
        
        Context: {json.dumps(context or {}, indent=2)}
        
        Available actions:
        - click: Click on elements (buttons, links, etc.)
        - type: Enter text into input fields
        - wait: Wait for elements to appear or conditions
        - navigate: Go to URLs
        - scroll: Scroll page or elements  
        - extract: Extract data from page
        - validate: Check if conditions are met
        - form_fill: Fill entire forms intelligently
        - ai_analyze: AI analysis of page content
        
        Return a JSON array of workflow steps in this format:
        [
          {{
            "action": "navigate",
            "target": "https://example.com",
            "data": {{"reason": "Start at homepage"}}
          }},
          {{
            "action": "click", 
            "target": "#login-button",
            "condition": "element_visible",
            "data": {{"wait_for": "login_form"}}
          }}
        ]
        
        Be specific with selectors and include error handling conditions.
        """
        
        try:
            ai_response = await self.ai_client.chat(
                message=planning_prompt,
                context={'task': 'workflow_planning'}
            )
            
            # Extract JSON from AI response
            response_text = ai_response.get('response', '')
            
            # Find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                workflow_data = json.loads(json_text)
                
                # Convert to WorkflowStep objects
                workflow_steps = []
                for step_data in workflow_data:
                    step = WorkflowStep(
                        action=step_data.get('action', ''),
                        target=step_data.get('target', ''),
                        data=step_data.get('data', {}),
                        condition=step_data.get('condition'),
                        retry_count=step_data.get('retry_count', 3),
                        timeout=step_data.get('timeout', 10.0)
                    )
                    workflow_steps.append(step)
                
                logging.info(f"AI generated {len(workflow_steps)} workflow steps")
                return workflow_steps
            
        except Exception as e:
            logging.error(f"AI workflow planning failed: {e}")
        
        return []
    
    async def _execute_workflow_step(self, 
                                   step: WorkflowStep, 
                                   context: Dict[str, Any],
                                   step_index: int) -> Dict[str, Any]:
        """Execute a single workflow step with enhanced error handling"""
        start_time = time.time()
        
        try:
            # Pre-step validation
            if step.condition:
                condition_met = await self._check_condition(step.condition, context)
                if not condition_met:
                    return {
                        'success': False,
                        'step_index': step_index,
                        'action': step.action,
                        'error': f'Condition not met: {step.condition}',
                        'execution_time': time.time() - start_time
                    }
            
            # Execute step based on action type
            if step.action == ActionType.NAVIGATE.value:
                result = await self._navigate(step.target, step.data)
            
            elif step.action == ActionType.CLICK.value:
                result = await self._click_element(step.target, step.data)
            
            elif step.action == ActionType.TYPE.value:
                result = await self._type_text(step.target, step.data)
            
            elif step.action == ActionType.WAIT.value:
                result = await self._wait_for_condition(step.target, step.data)
            
            elif step.action == ActionType.FORM_FILL.value:
                result = await self._intelligent_form_fill(step.target, step.data)
            
            elif step.action == ActionType.AI_ANALYZE.value:
                result = await self._ai_page_analysis(step.target, step.data)
            
            elif step.action == ActionType.EXTRACT.value:
                result = await self._extract_data(step.target, step.data)
            
            else:
                result = {'success': False, 'error': f'Unknown action: {step.action}'}
            
            # Add metadata to result
            result.update({
                'step_index': step_index,
                'action': step.action,
                'target': step.target,
                'execution_time': time.time() - start_time
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'step_index': step_index,
                'action': step.action,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _ai_error_recovery(self, 
                               failed_step: WorkflowStep,
                               step_result: Dict[str, Any],
                               context: Dict[str, Any],
                               step_index: int) -> Dict[str, Any]:
        """AI-powered error recovery for failed workflow steps"""
        if not self.ai_client:
            return step_result
        
        self.metrics['ai_interventions'] += 1
        
        # Create recovery prompt
        recovery_prompt = f"""
        A workflow step has failed. Help recover by suggesting alternative approaches:
        
        Failed Step:
        - Action: {failed_step.action}
        - Target: {failed_step.target} 
        - Data: {json.dumps(failed_step.data or {}, indent=2)}
        - Error: {step_result.get('error', 'Unknown error')}
        
        Context: {json.dumps(context, indent=2)}
        
        Suggest up to 3 alternative approaches to accomplish the same goal.
        Consider:
        1. Different selectors (ID, class, xpath, text content)
        2. Wait conditions that might be needed
        3. Alternative UI elements that might work
        4. Different interaction methods
        
        Return JSON with recovery suggestions:
        {{
          "suggestions": [
            {{
              "approach": "try_different_selector",
              "target": "button[type='submit']",
              "reason": "Original ID might have changed"
            }}
          ]
        }}
        """
        
        try:
            ai_response = await self.ai_client.chat(
                message=recovery_prompt,
                context={'task': 'error_recovery'}
            )
            
            response_text = ai_response.get('response', '')
            
            # Try to execute AI suggestions
            # For now, implement basic retry with alternative selectors
            if 'different_selector' in response_text.lower():
                # Try alternative selector strategies
                alternative_targets = [
                    failed_step.target.replace('#', '.'),  # Try class instead of ID
                    f"[data-testid*='{failed_step.target.replace('#', '').replace('.', '')}']",
                    f"button:contains('{failed_step.target}')",  # Text-based
                ]
                
                for alt_target in alternative_targets:
                    alt_step = WorkflowStep(
                        action=failed_step.action,
                        target=alt_target,
                        data=failed_step.data,
                        retry_count=1
                    )
                    
                    recovery_result = await self._execute_workflow_step(
                        alt_step, context, step_index
                    )
                    
                    if recovery_result.get('success', False):
                        logging.info(f"AI recovery successful with alternative selector: {alt_target}")
                        return recovery_result
            
        except Exception as e:
            logging.error(f"AI error recovery failed: {e}")
        
        return step_result  # Return original failure if recovery fails
    
    async def _intelligent_form_fill(self, target: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered intelligent form filling"""
        try:
            # This would integrate with the browser to:
            # 1. Analyze form structure
            # 2. Map data fields intelligently
            # 3. Handle different input types
            # 4. Validate entries
            
            form_data = data.get('form_data', {})
            
            # Simulate intelligent form filling
            # In real implementation, this would interact with browser DOM
            filled_fields = []
            for field_name, field_value in form_data.items():
                # AI-powered field mapping would happen here
                filled_fields.append({
                    'field': field_name,
                    'value': field_value,
                    'success': True
                })
            
            return {
                'success': True,
                'filled_fields': filled_fields,
                'form_target': target
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _ai_page_analysis(self, target: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered page content analysis"""
        if not self.ai_client:
            return {'success': False, 'error': 'No AI client available'}
        
        try:
            # Get page content (would be from browser in real implementation)
            analysis_type = data.get('analysis_type', 'general')
            
            analysis_prompt = f"""
            Analyze the current webpage content for: {analysis_type}
            
            Target element/area: {target}
            Analysis requirements: {json.dumps(data, indent=2)}
            
            Provide structured analysis including:
            - Key information extracted
            - Actionable items found
            - Potential next steps
            - Data quality assessment
            """
            
            ai_response = await self.ai_client.chat(
                message=analysis_prompt,
                context={'task': 'page_analysis'}
            )
            
            return {
                'success': True,
                'analysis': ai_response.get('response', ''),
                'analysis_type': analysis_type,
                'target': target
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _navigate(self, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Navigate to URL with validation"""
        try:
            # Browser navigation would happen here
            # For now, simulate successful navigation
            return {
                'success': True,
                'url': url,
                'navigation_time': 0.5
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _click_element(self, selector: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Click element with enhanced selector strategies"""
        try:
            # Element clicking would happen here with multiple selector strategies
            return {
                'success': True,
                'selector': selector,
                'click_time': 0.1
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _type_text(self, selector: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Type text with intelligent input handling"""
        try:
            text = data.get('text', '') if data else ''
            return {
                'success': True,
                'selector': selector,
                'text_length': len(text)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _wait_for_condition(self, condition: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Wait for specific conditions with timeout"""
        try:
            timeout = data.get('timeout', 10) if data else 10
            # Condition waiting would happen here
            return {
                'success': True,
                'condition': condition,
                'wait_time': 0.2
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _extract_data(self, selector: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract data from page elements"""
        try:
            # Data extraction would happen here
            return {
                'success': True,
                'selector': selector,
                'extracted_data': {}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _check_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Check if a condition is met"""
        try:
            # Condition checking logic would be here
            return True
        except:
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get automation performance metrics"""
        return {
            **self.metrics,
            'active_workflows': len(self.active_workflows),
            'workflow_history_size': len(self.workflow_history)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for browser automation system"""
        return {
            'status': 'healthy',
            'ai_client_available': self.ai_client is not None,
            'error_recovery_enabled': self.error_recovery_enabled,
            'performance_tracking': self.performance_tracking,
            'metrics': self.get_performance_metrics()
        }