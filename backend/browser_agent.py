"""
Browser Agent for AI Browser
Handles browser automation actions and coordinates with the AI model.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

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
        """Handle click action"""
        target = parameters.get('target', '')
        
        if not target:
            return {
                "success": False,
                "message": "No target specified for click action",
                "data": None
            }
        
        # For now, return instructions for the browser extension to handle
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
        """Handle type action"""
        text = parameters.get('text', '')
        target = parameters.get('target', '')
        
        if not text:
            return {
                "success": False,
                "message": "No text specified for type action",
                "data": None
            }
        
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
    
    async def cleanup(self):
        """Clean up resources"""
        # Placeholder for cleanup logic (e.g., closing browser instances)
        logger.info("Browser agent cleanup completed")