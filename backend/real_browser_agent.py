"""
Real Browser Agent - Actually executes browser automation
No more mock responses - generates real actions for Chrome extension
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    WAIT = "wait"

class RealBrowserAgent:
    """Browser agent that generates REAL executable browser actions"""
    
    def __init__(self):
        self.action_handlers = {
            ActionType.CLICK.value: self._handle_click,
            ActionType.TYPE.value: self._handle_type,
            ActionType.NAVIGATE.value: self._handle_navigate,
            ActionType.SCROLL.value: self._handle_scroll,
            ActionType.WAIT.value: self._handle_wait,
        }
    
    async def execute_action(self, 
                           action_type: str, 
                           parameters: Dict[str, Any],
                           page_url: str) -> Dict[str, Any]:
        """Generate real browser action that extension can execute"""
        try:
            logger.info("Preparing real browser action", 
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
            
            logger.info("Real action prepared", 
                       action_type=action_type,
                       success=result["success"],
                       executable=result.get("data", {}).get("executable", False))
            
            return result
            
        except Exception as e:
            logger.error("Real action preparation failed", 
                        action_type=action_type,
                        error=str(e))
            return {
                "success": False,
                "message": f"Action preparation failed: {str(e)}",
                "data": None
            }
    
    async def _handle_click(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Generate real click action for Chrome extension"""
        target = parameters.get('target', '')
        
        if not target:
            return {
                "success": False,
                "message": "No target specified for click action",
                "data": None
            }
        
        # Find the best CSS selector for the target
        selector = self._find_element_selector(target)
        
        return {
            "success": True,
            "message": f"Real click action ready for: {target}",
            "data": {
                "type": "CLICK",
                "selector": selector,
                "target_description": target,
                "executable": True,
                "action_id": f"click_{hash(target)}_{int(asyncio.get_event_loop().time())}"
            }
        }
    
    async def _handle_type(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Generate real type action for Chrome extension"""
        text = parameters.get('text', '')
        target = parameters.get('target', '')
        
        if not text:
            return {
                "success": False,
                "message": "No text specified for type action",
                "data": None
            }
        
        # Find the best CSS selector for the input field
        selector = self._find_input_selector(target)
        
        return {
            "success": True,
            "message": f"Real type action ready: '{text}' in {target or 'input field'}",
            "data": {
                "type": "TYPE",
                "selector": selector,
                "text": text,
                "target_description": target,
                "executable": True,
                "action_id": f"type_{hash(text + target)}_{int(asyncio.get_event_loop().time())}"
            }
        }
    
    async def _handle_navigate(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Generate real navigation action for Chrome extension"""
        url = parameters.get('url', '')
        
        if not url:
            return {
                "success": False,
                "message": "No URL specified for navigate action",
                "data": None
            }
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('/'):
                url = 'https://' + url
        
        return {
            "success": True,
            "message": f"Real navigation action ready: {url}",
            "data": {
                "type": "NAVIGATE",
                "url": url,
                "executable": True,
                "action_id": f"nav_{hash(url)}_{int(asyncio.get_event_loop().time())}"
            }
        }
    
    async def _handle_scroll(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Generate real scroll action for Chrome extension"""
        direction = parameters.get('direction', 'down')
        amount = parameters.get('amount', 500)
        
        return {
            "success": True,
            "message": f"Real scroll action ready: {direction} by {amount}px",
            "data": {
                "type": "SCROLL",
                "direction": direction,
                "amount": amount,
                "executable": True,
                "action_id": f"scroll_{direction}_{int(asyncio.get_event_loop().time())}"
            }
        }
    
    async def _handle_wait(self, parameters: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """Generate real wait action"""
        duration = parameters.get('duration', 1000)  # milliseconds
        
        return {
            "success": True,
            "message": f"Real wait action ready: {duration}ms",
            "data": {
                "type": "WAIT",
                "duration": duration,
                "executable": True,
                "action_id": f"wait_{duration}_{int(asyncio.get_event_loop().time())}"
            }
        }
    
    def _find_element_selector(self, target: str) -> str:
        """Find the best CSS selector for the target element"""
        target_lower = target.lower()
        
        # Button selectors
        if 'button' in target_lower:
            if 'login' in target_lower or 'sign in' in target_lower:
                return "button[type='submit'], input[type='submit'], .login-btn, #login, [data-testid*='login'], button:contains('Login'), button:contains('Sign in'), a[href*='login']"
            elif 'search' in target_lower:
                return "button[type='submit'], input[type='submit'], .search-btn, #search-btn, [data-testid*='search'], button:contains('Search'), .search-submit"
            elif 'submit' in target_lower:
                return "button[type='submit'], input[type='submit'], .submit-btn, [data-testid*='submit'], button:contains('Submit')"
            else:
                clean_target = target.replace(' ', '').replace('button', '').strip()
                return f"button:contains('{target}'), button:contains('{clean_target}'), input[value*='{target}'], [aria-label*='{target}']"
        
        # Link selectors
        elif 'link' in target_lower or target_lower.startswith('click'):
            link_text = target.replace('click', '').replace('link', '').strip()
            return f"a:contains('{link_text}'), a:contains('{target}'), [href*='{link_text.replace(' ', '-')}'], [title*='{target}']"
        
        # Input field selectors
        elif 'input' in target_lower or 'field' in target_lower or 'box' in target_lower:
            return self._find_input_selector(target)
        
        # Generic element selector
        else:
            clean_target = target.replace(' ', '-').lower()
            return f"#{clean_target}, .{clean_target}, [data-testid*='{clean_target}'], [aria-label*='{target}'], [title*='{target}'], *:contains('{target}')"
    
    def _find_input_selector(self, target: str) -> str:
        """Find the best CSS selector for input fields"""
        if not target:
            return "input:not([type='hidden']), textarea, [contenteditable='true']"
            
        target_lower = target.lower()
        
        # Specific input types
        if 'email' in target_lower:
            return "input[type='email'], input[name*='email'], input[placeholder*='email'], #email, .email-field, .email-input"
        elif 'password' in target_lower:
            return "input[type='password'], input[name*='password'], input[placeholder*='password'], #password, .password-field, .password-input"
        elif 'search' in target_lower:
            return "input[type='search'], input[name*='search'], input[placeholder*='search'], #search, .search-field, .search-input, [role='searchbox']"
        elif 'username' in target_lower or 'user' in target_lower:
            return "input[name*='username'], input[name*='user'], input[placeholder*='username'], #username, .username-field, .user-input"
        elif 'phone' in target_lower or 'tel' in target_lower:
            return "input[type='tel'], input[name*='phone'], input[placeholder*='phone'], #phone, .phone-field"
        elif 'message' in target_lower or 'comment' in target_lower:
            return "textarea, input[name*='message'], input[placeholder*='message'], #message, .message-field, [role='textbox']"
        elif 'name' in target_lower and 'first' in target_lower:
            return "input[name*='first'], input[placeholder*='first'], #first-name, .first-name-field"
        elif 'name' in target_lower and 'last' in target_lower:
            return "input[name*='last'], input[placeholder*='last'], #last-name, .last-name-field"
        elif 'name' in target_lower:
            return "input[name*='name'], input[placeholder*='name'], #name, .name-field"
        else:
            # Generic input selector
            clean_target = target.replace(' ', '_').lower()
            return f"input[name*='{clean_target}'], input[placeholder*='{target}'], textarea[name*='{clean_target}'], #{clean_target}, .{clean_target}, [data-testid*='{clean_target}']"

# Global instance
real_browser_agent = RealBrowserAgent()