"""
Visual Element Highlighting System for AI Browser
Provides overlay and highlighting functionality for browser elements.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

class HighlightStyle(Enum):
    """Different highlight styles for elements"""
    PRIMARY = "primary"      # Main action element (blue)
    SUCCESS = "success"      # Successful action (green)
    WARNING = "warning"      # Attention needed (orange)
    DANGER = "danger"        # Error or problematic (red)
    INFO = "info"           # Information highlight (cyan)
    HOVER = "hover"         # Hover state (light blue)
    SELECTED = "selected"   # Selected element (purple)

@dataclass
class ElementHighlight:
    """Represents a highlighted element"""
    element_id: str
    selector: str
    style: HighlightStyle
    label: Optional[str] = None
    description: Optional[str] = None
    bounds: Optional[Dict[str, int]] = None
    z_index: int = 1000
    duration: Optional[int] = None  # Auto-remove after milliseconds
    pulse: bool = False
    border_width: int = 2
    opacity: float = 0.8

class VisualElementHighlighter:
    """Manages visual highlighting and overlays for browser elements"""
    
    def __init__(self):
        self.active_highlights: Dict[str, ElementHighlight] = {}
        self.highlight_groups: Dict[str, List[str]] = {}  # group_name -> [element_ids]
        self.overlay_enabled = True
        
        # Define highlight styles
        self.style_definitions = {
            HighlightStyle.PRIMARY: {
                'border_color': '#007bff',
                'background_color': 'rgba(0, 123, 255, 0.1)',
                'text_color': '#007bff',
                'shadow': '0 0 10px rgba(0, 123, 255, 0.5)'
            },
            HighlightStyle.SUCCESS: {
                'border_color': '#28a745',
                'background_color': 'rgba(40, 167, 69, 0.1)',
                'text_color': '#28a745',
                'shadow': '0 0 10px rgba(40, 167, 69, 0.5)'
            },
            HighlightStyle.WARNING: {
                'border_color': '#ffc107',
                'background_color': 'rgba(255, 193, 7, 0.1)',
                'text_color': '#856404',
                'shadow': '0 0 10px rgba(255, 193, 7, 0.5)'
            },
            HighlightStyle.DANGER: {
                'border_color': '#dc3545',
                'background_color': 'rgba(220, 53, 69, 0.1)',
                'text_color': '#dc3545',
                'shadow': '0 0 10px rgba(220, 53, 69, 0.5)'
            },
            HighlightStyle.INFO: {
                'border_color': '#17a2b8',
                'background_color': 'rgba(23, 162, 184, 0.1)',
                'text_color': '#17a2b8',
                'shadow': '0 0 10px rgba(23, 162, 184, 0.5)'
            },
            HighlightStyle.HOVER: {
                'border_color': '#6c757d',
                'background_color': 'rgba(108, 117, 125, 0.1)',
                'text_color': '#6c757d',
                'shadow': '0 0 5px rgba(108, 117, 125, 0.3)'
            },
            HighlightStyle.SELECTED: {
                'border_color': '#6f42c1',
                'background_color': 'rgba(111, 66, 193, 0.1)',
                'text_color': '#6f42c1',
                'shadow': '0 0 15px rgba(111, 66, 193, 0.6)'
            }
        }
    
    async def highlight_element(self, 
                              selector: str,
                              style: HighlightStyle = HighlightStyle.PRIMARY,
                              label: Optional[str] = None,
                              description: Optional[str] = None,
                              duration: Optional[int] = None,
                              pulse: bool = False) -> str:
        """Highlight a specific element on the page"""
        try:
            element_id = f"highlight_{len(self.active_highlights)}"
            
            highlight = ElementHighlight(
                element_id=element_id,
                selector=selector,
                style=style,
                label=label,
                description=description,
                duration=duration,
                pulse=pulse
            )
            
            self.active_highlights[element_id] = highlight
            
            # Generate CSS and JavaScript for highlighting
            highlight_css = self._generate_highlight_css(highlight)
            highlight_js = self._generate_highlight_js(highlight)
            
            logger.info("Element highlighted", 
                       element_id=element_id,
                       selector=selector,
                       style=style.value)
            
            return element_id
            
        except Exception as e:
            logger.error("Failed to highlight element", error=str(e), selector=selector)
            return ""
    
    async def highlight_multiple_elements(self, 
                                        elements: List[Dict[str, Any]],
                                        group_name: str = "multi_highlight") -> List[str]:
        """Highlight multiple elements as a group"""
        try:
            highlighted_ids = []
            
            for i, element_data in enumerate(elements):
                selector = element_data.get('selector', '')
                style = HighlightStyle(element_data.get('style', HighlightStyle.PRIMARY.value))
                label = element_data.get('label', f"Element {i+1}")
                
                highlight_id = await self.highlight_element(
                    selector=selector,
                    style=style,
                    label=label,
                    description=element_data.get('description'),
                    pulse=element_data.get('pulse', False)
                )
                
                if highlight_id:
                    highlighted_ids.append(highlight_id)
            
            # Store group for easier management
            self.highlight_groups[group_name] = highlighted_ids
            
            logger.info("Multiple elements highlighted", 
                       group_name=group_name,
                       count=len(highlighted_ids))
            
            return highlighted_ids
            
        except Exception as e:
            logger.error("Failed to highlight multiple elements", error=str(e))
            return []
    
    async def highlight_accessibility_matches(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Highlight elements from accessibility tree matches"""
        try:
            elements = []
            
            for i, match in enumerate(matches[:5]):  # Limit to top 5 matches
                node = match.get('node', {})
                confidence = match.get('confidence', 0)
                
                # Choose style based on confidence
                if confidence > 0.8:
                    style = HighlightStyle.SUCCESS
                elif confidence > 0.6:
                    style = HighlightStyle.PRIMARY
                else:
                    style = HighlightStyle.INFO
                
                # Get best selector
                selectors = node.get('selectors', [])
                selector = selectors[0] if selectors else f"[aria-label='{node.get('name', '')}']"
                
                elements.append({
                    'selector': selector,
                    'style': style.value,
                    'label': f"{node.get('name', 'Element')} ({confidence:.0%})",
                    'description': f"Match confidence: {confidence:.1%}\nReasons: {', '.join(match.get('reasons', []))}"
                })
            
            return await self.highlight_multiple_elements(elements, "accessibility_matches")
            
        except Exception as e:
            logger.error("Failed to highlight accessibility matches", error=str(e))
            return []
    
    async def create_action_overlay(self, 
                                  action_type: str,
                                  target_selector: str,
                                  instructions: str) -> Dict[str, Any]:
        """Create an overlay showing the next action to be performed"""
        try:
            overlay_data = {
                'type': 'action_overlay',
                'action_type': action_type,
                'target_selector': target_selector,
                'instructions': instructions,
                'css': self._generate_action_overlay_css(),
                'html': self._generate_action_overlay_html(action_type, instructions),
                'js': self._generate_action_overlay_js(target_selector)
            }
            
            logger.info("Action overlay created", 
                       action_type=action_type,
                       target=target_selector)
            
            return overlay_data
            
        except Exception as e:
            logger.error("Failed to create action overlay", error=str(e))
            return {}
    
    def _generate_highlight_css(self, highlight: ElementHighlight) -> str:
        """Generate CSS for element highlighting"""
        style_def = self.style_definitions[highlight.style]
        
        css = f"""
        .ai-browser-highlight-{highlight.element_id} {{
            border: {highlight.border_width}px solid {style_def['border_color']} !important;
            background-color: {style_def['background_color']} !important;
            box-shadow: {style_def['shadow']} !important;
            position: relative !important;
            z-index: {highlight.z_index} !important;
            opacity: {highlight.opacity} !important;
        }}
        
        .ai-browser-highlight-{highlight.element_id}::before {{
            content: "{highlight.label or ''}";
            position: absolute;
            top: -25px;
            left: 0;
            background: {style_def['border_color']};
            color: white;
            padding: 2px 8px;
            font-size: 12px;
            font-weight: bold;
            border-radius: 3px;
            white-space: nowrap;
            z-index: {highlight.z_index + 1};
        }}
        """
        
        if highlight.pulse:
            css += f"""
            @keyframes ai-browser-pulse-{highlight.element_id} {{
                0% {{ box-shadow: 0 0 0 0 {style_def['border_color']}80; }}
                70% {{ box-shadow: 0 0 0 10px {style_def['border_color']}00; }}
                100% {{ box-shadow: 0 0 0 0 {style_def['border_color']}00; }}
            }}
            
            .ai-browser-highlight-{highlight.element_id} {{
                animation: ai-browser-pulse-{highlight.element_id} 2s infinite;
            }}
            """
        
        return css
    
    def _generate_highlight_js(self, highlight: ElementHighlight) -> str:
        """Generate JavaScript for element highlighting"""
        js = f"""
        (function() {{
            const element = document.querySelector('{highlight.selector}');
            if (element) {{
                element.classList.add('ai-browser-highlight-{highlight.element_id}');
                
                // Add tooltip if description exists
                if ('{highlight.description or ''}') {{
                    element.title = '{highlight.description or ''}';
                }}
                
                // Auto-remove after duration
                {f"setTimeout(() => element.classList.remove('ai-browser-highlight-{highlight.element_id}'), {highlight.duration});" if highlight.duration else ""}
            }}
        }})();
        """
        return js
    
    def _generate_action_overlay_css(self) -> str:
        """Generate CSS for action overlays"""
        return """
        .ai-browser-action-overlay {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 300px;
            animation: ai-browser-slide-in 0.3s ease-out;
        }
        
        @keyframes ai-browser-slide-in {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .ai-browser-action-overlay .action-type {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            margin-bottom: 5px;
            opacity: 0.9;
        }
        
        .ai-browser-action-overlay .instructions {
            font-size: 14px;
            line-height: 1.4;
        }
        
        .ai-browser-action-overlay .close-btn {
            position: absolute;
            top: 5px;
            right: 10px;
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            opacity: 0.7;
        }
        
        .ai-browser-action-overlay .close-btn:hover {
            opacity: 1;
        }
        """
    
    def _generate_action_overlay_html(self, action_type: str, instructions: str) -> str:
        """Generate HTML for action overlay"""
        return f"""
        <div id="ai-browser-action-overlay" class="ai-browser-action-overlay">
            <button class="close-btn" onclick="this.parentElement.remove()">&times;</button>
            <div class="action-type">{action_type}</div>
            <div class="instructions">{instructions}</div>
        </div>
        """
    
    def _generate_action_overlay_js(self, target_selector: str) -> str:
        """Generate JavaScript for action overlay positioning"""
        return f"""
        (function() {{
            const targetElement = document.querySelector('{target_selector}');
            const overlay = document.getElementById('ai-browser-action-overlay');
            
            if (targetElement && overlay) {{
                const rect = targetElement.getBoundingClientRect();
                
                // Position overlay near target element
                if (rect.top < window.innerHeight / 2) {{
                    overlay.style.top = (rect.bottom + 10) + 'px';
                }} else {{
                    overlay.style.top = (rect.top - overlay.offsetHeight - 10) + 'px';
                }}
                
                if (rect.left > window.innerWidth / 2) {{
                    overlay.style.right = '20px';
                    overlay.style.left = 'auto';
                }} else {{
                    overlay.style.left = (rect.left) + 'px';
                    overlay.style.right = 'auto';
                }}
            }}
            
            // Auto-remove overlay after 10 seconds
            setTimeout(() => {{
                const overlay = document.getElementById('ai-browser-action-overlay');
                if (overlay) overlay.remove();
            }}, 10000);
        }})();
        """
    
    async def remove_highlight(self, element_id: str) -> bool:
        """Remove a specific highlight"""
        try:
            if element_id in self.active_highlights:
                del self.active_highlights[element_id]
                
                # Remove from any groups
                for group_name, ids in self.highlight_groups.items():
                    if element_id in ids:
                        ids.remove(element_id)
                
                logger.info("Highlight removed", element_id=element_id)
                return True
            return False
            
        except Exception as e:
            logger.error("Failed to remove highlight", error=str(e), element_id=element_id)
            return False
    
    async def remove_highlight_group(self, group_name: str) -> bool:
        """Remove all highlights in a group"""
        try:
            if group_name in self.highlight_groups:
                element_ids = self.highlight_groups[group_name].copy()
                
                for element_id in element_ids:
                    await self.remove_highlight(element_id)
                
                del self.highlight_groups[group_name]
                
                logger.info("Highlight group removed", group_name=group_name, count=len(element_ids))
                return True
            return False
            
        except Exception as e:
            logger.error("Failed to remove highlight group", error=str(e), group_name=group_name)
            return False
    
    async def clear_all_highlights(self) -> int:
        """Remove all active highlights"""
        try:
            count = len(self.active_highlights)
            self.active_highlights.clear()
            self.highlight_groups.clear()
            
            logger.info("All highlights cleared", count=count)
            return count
            
        except Exception as e:
            logger.error("Failed to clear highlights", error=str(e))
            return 0
    
    def get_highlight_data(self) -> Dict[str, Any]:
        """Get all current highlight data for client injection"""
        try:
            highlight_data = {
                'css': [],
                'js': [],
                'highlights': {},
                'groups': self.highlight_groups.copy()
            }
            
            for element_id, highlight in self.active_highlights.items():
                highlight_data['css'].append(self._generate_highlight_css(highlight))
                highlight_data['js'].append(self._generate_highlight_js(highlight))
                highlight_data['highlights'][element_id] = {
                    'selector': highlight.selector,
                    'style': highlight.style.value,
                    'label': highlight.label,
                    'description': highlight.description
                }
            
            return highlight_data
            
        except Exception as e:
            logger.error("Failed to get highlight data", error=str(e))
            return {'css': [], 'js': [], 'highlights': {}, 'groups': {}}

# Global instance
visual_highlighter = VisualElementHighlighter()