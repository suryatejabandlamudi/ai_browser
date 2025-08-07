"""
Accessibility Tree Integration for AI Browser
Provides enhanced element detection using Chrome DevTools accessibility APIs.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

class ElementRole(Enum):
    """Common accessibility roles for web elements"""
    BUTTON = "button"
    LINK = "link"
    TEXTBOX = "textbox"
    COMBOBOX = "combobox"
    LISTBOX = "listbox"
    MENUITEM = "menuitem"
    TAB = "tab"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SLIDER = "slider"
    PROGRESSBAR = "progressbar"
    HEADING = "heading"
    IMAGE = "img"
    LIST = "list"
    LISTITEM = "listitem"
    TABLE = "table"
    CELL = "cell"
    COLUMNHEADER = "columnheader"
    ROWHEADER = "rowheader"
    FORM = "form"
    MAIN = "main"
    NAVIGATION = "navigation"
    COMPLEMENTARY = "complementary"
    BANNER = "banner"
    CONTENTINFO = "contentinfo"

@dataclass
class AccessibilityNode:
    """Represents a node in the accessibility tree"""
    id: str
    role: str
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    bounds: Optional[Dict[str, int]] = None
    children: List['AccessibilityNode'] = None
    properties: Dict[str, Any] = None
    dom_path: Optional[str] = None
    selectors: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.properties is None:
            self.properties = {}
        if self.selectors is None:
            self.selectors = []

class AccessibilityTreeExtractor:
    """Extracts and processes accessibility tree information for AI-driven element detection"""
    
    def __init__(self):
        self.cached_trees = {}  # URL -> accessibility tree cache
        self.element_descriptions = {}  # Cache for AI-friendly element descriptions
        
    async def extract_accessibility_tree(self, page_url: str, page_content: str = None) -> Dict[str, Any]:
        """Extract accessibility tree from a web page"""
        try:
            logger.info("Extracting accessibility tree", url=page_url)
            
            # In a real implementation, this would use Chrome DevTools Protocol
            # For now, we simulate accessibility tree extraction from HTML
            
            if page_content:
                tree = await self._simulate_accessibility_tree(page_content, page_url)
            else:
                # In real implementation, fetch via CDP
                tree = await self._get_cached_tree(page_url)
            
            # Cache the result
            self.cached_trees[page_url] = tree
            
            logger.info("Accessibility tree extracted", 
                       url=page_url, 
                       nodes_count=len(tree.get("nodes", [])))
            
            return tree
            
        except Exception as e:
            logger.error("Failed to extract accessibility tree", error=str(e), url=page_url)
            return {"nodes": [], "error": str(e)}
    
    async def _simulate_accessibility_tree(self, html_content: str, page_url: str) -> Dict[str, Any]:
        """Simulate accessibility tree extraction from HTML content"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            nodes = []
            
            # Extract interactive elements
            interactive_selectors = {
                'button': {'role': ElementRole.BUTTON.value, 'priority': 'high'},
                'input[type="button"]': {'role': ElementRole.BUTTON.value, 'priority': 'high'},
                'input[type="submit"]': {'role': ElementRole.BUTTON.value, 'priority': 'high'},
                'input[type="text"]': {'role': ElementRole.TEXTBOX.value, 'priority': 'high'},
                'input[type="email"]': {'role': ElementRole.TEXTBOX.value, 'priority': 'high'},
                'input[type="password"]': {'role': ElementRole.TEXTBOX.value, 'priority': 'high'},
                'input[type="search"]': {'role': ElementRole.TEXTBOX.value, 'priority': 'high'},
                'textarea': {'role': ElementRole.TEXTBOX.value, 'priority': 'high'},
                'select': {'role': ElementRole.COMBOBOX.value, 'priority': 'high'},
                'a[href]': {'role': ElementRole.LINK.value, 'priority': 'medium'},
                'input[type="checkbox"]': {'role': ElementRole.CHECKBOX.value, 'priority': 'medium'},
                'input[type="radio"]': {'role': ElementRole.RADIO.value, 'priority': 'medium'},
                'img[alt]': {'role': ElementRole.IMAGE.value, 'priority': 'low'},
                'h1, h2, h3, h4, h5, h6': {'role': ElementRole.HEADING.value, 'priority': 'medium'},
                'form': {'role': ElementRole.FORM.value, 'priority': 'medium'},
                'nav': {'role': ElementRole.NAVIGATION.value, 'priority': 'low'},
                'main': {'role': ElementRole.MAIN.value, 'priority': 'low'}
            }
            
            node_id = 0
            for selector, info in interactive_selectors.items():
                elements = soup.select(selector)
                for element in elements:
                    node_id += 1
                    
                    # Extract element properties
                    name = self._extract_element_name(element)
                    description = self._extract_element_description(element)
                    value = element.get('value') or element.get_text(strip=True)[:100]
                    
                    # Generate selectors
                    selectors = self._generate_selectors(element)
                    
                    # Create accessibility node
                    node = AccessibilityNode(
                        id=f"node_{node_id}",
                        role=info['role'],
                        name=name,
                        description=description,
                        value=value if len(value) < 100 else value[:100] + "...",
                        bounds=self._estimate_bounds(element),
                        selectors=selectors,
                        properties={
                            'tag_name': element.name,
                            'priority': info['priority'],
                            'id': element.get('id'),
                            'class': element.get('class', []),
                            'type': element.get('type'),
                            'href': element.get('href'),
                            'disabled': element.get('disabled', False),
                            'required': element.get('required', False),
                            'placeholder': element.get('placeholder')
                        }
                    )
                    
                    nodes.append(node)
            
            return {
                "nodes": [self._node_to_dict(node) for node in nodes],
                "url": page_url,
                "timestamp": asyncio.get_event_loop().time(),
                "total_nodes": len(nodes),
                "interactive_nodes": len([n for n in nodes if n.properties.get('priority') in ['high', 'medium']])
            }
            
        except Exception as e:
            logger.error("Failed to simulate accessibility tree", error=str(e))
            return {"nodes": [], "error": str(e)}
    
    def _extract_element_name(self, element) -> str:
        """Extract human-readable name for an element"""
        # Check aria-label first
        if element.get('aria-label'):
            return element['aria-label']
        
        # Check aria-labelledby
        if element.get('aria-labelledby'):
            # In real implementation, would resolve the reference
            return f"Labeled by: {element['aria-labelledby']}"
        
        # For buttons, use text content
        if element.name in ['button', 'a']:
            text = element.get_text(strip=True)
            if text:
                return text[:50]
        
        # For inputs, check labels
        if element.name == 'input':
            # Check for associated label
            element_id = element.get('id')
            if element_id:
                # Find label with matching for attribute
                parent_soup = element.find_parent('html') or element.find_parent('body')
                if parent_soup:
                    label = parent_soup.find('label', {'for': element_id})
                    if label:
                        return label.get_text(strip=True)
            
            # Check placeholder
            placeholder = element.get('placeholder')
            if placeholder:
                return f"Input: {placeholder}"
            
            # Check type
            input_type = element.get('type', 'text')
            return f"{input_type.title()} input"
        
        # For images, use alt text
        if element.name == 'img':
            alt = element.get('alt')
            if alt:
                return f"Image: {alt}"
        
        # For headings, use text content
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = element.get_text(strip=True)
            if text:
                return f"{element.name.upper()}: {text[:50]}"
        
        # Fallback to element type
        return element.name.title()
    
    def _extract_element_description(self, element) -> str:
        """Extract detailed description for AI understanding"""
        descriptions = []
        
        # Add role/type information
        if element.name == 'input':
            input_type = element.get('type', 'text')
            descriptions.append(f"{input_type} input field")
        else:
            descriptions.append(f"{element.name} element")
        
        # Add state information
        if element.get('disabled'):
            descriptions.append("disabled")
        if element.get('required'):
            descriptions.append("required")
        if element.get('checked'):
            descriptions.append("checked")
        
        # Add context information
        classes = element.get('class', [])
        if classes:
            relevant_classes = [c for c in classes if any(keyword in c.lower() 
                                                       for keyword in ['btn', 'button', 'primary', 'secondary', 'submit', 'cancel', 'close', 'menu', 'nav'])]
            if relevant_classes:
                descriptions.append(f"classes: {', '.join(relevant_classes)}")
        
        return ", ".join(descriptions)
    
    def _generate_selectors(self, element) -> List[str]:
        """Generate multiple selector options for an element"""
        selectors = []
        
        # ID selector (highest priority)
        if element.get('id'):
            selectors.append(f"#{element['id']}")
        
        # Class selectors
        classes = element.get('class', [])
        if classes:
            for cls in classes[:3]:  # Limit to first 3 classes
                selectors.append(f".{cls}")
            if len(classes) > 1:
                selectors.append(f".{'.'.join(classes[:2])}")
        
        # Attribute selectors
        if element.get('name'):
            selectors.append(f"[name='{element['name']}']")
        if element.get('type'):
            selectors.append(f"[type='{element['type']}']")
        if element.get('aria-label'):
            selectors.append(f"[aria-label='{element['aria-label']}']")
        
        # Text-based selectors for buttons/links
        if element.name in ['button', 'a']:
            text = element.get_text(strip=True)
            if text and len(text) < 50:
                # CSS selector for text content is complex, note for AI
                selectors.append(f"button:contains('{text}')")  # jQuery-style for reference
        
        # Tag selector (lowest priority)
        selectors.append(element.name)
        
        return selectors
    
    def _estimate_bounds(self, element) -> Dict[str, int]:
        """Estimate element bounds (in real implementation, would get from CDP)"""
        # Simulate bounds - in real implementation, get from Chrome DevTools
        return {
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 30
        }
    
    def _node_to_dict(self, node: AccessibilityNode) -> Dict[str, Any]:
        """Convert AccessibilityNode to dictionary for JSON serialization"""
        return {
            "id": node.id,
            "role": node.role,
            "name": node.name,
            "description": node.description,
            "value": node.value,
            "bounds": node.bounds,
            "selectors": node.selectors,
            "properties": node.properties,
            "children": [self._node_to_dict(child) for child in node.children]
        }
    
    async def _get_cached_tree(self, page_url: str) -> Dict[str, Any]:
        """Get cached accessibility tree or return empty"""
        return self.cached_trees.get(page_url, {"nodes": [], "cached": True})
    
    async def find_elements_by_description(self, 
                                         tree: Dict[str, Any], 
                                         description: str) -> List[Dict[str, Any]]:
        """Find elements in accessibility tree by AI description"""
        try:
            logger.info("Finding elements by description", description=description)
            
            nodes = tree.get("nodes", [])
            matches = []
            
            # Convert description to lowercase for matching
            desc_lower = description.lower()
            
            # Keywords for different element types
            button_keywords = ['button', 'btn', 'click', 'submit', 'send', 'save', 'cancel', 'close', 'ok']
            input_keywords = ['input', 'field', 'textbox', 'text', 'type', 'enter', 'search']
            link_keywords = ['link', 'href', 'navigate', 'go to', 'visit']
            
            for node in nodes:
                score = 0
                reasons = []
                
                # Check name match
                if node.get("name") and node["name"].lower() in desc_lower:
                    score += 10
                    reasons.append(f"name matches: {node['name']}")
                
                # Check role relevance
                role = node.get("role", "")
                if role == "button" and any(kw in desc_lower for kw in button_keywords):
                    score += 8
                    reasons.append("button role matches description")
                elif role == "textbox" and any(kw in desc_lower for kw in input_keywords):
                    score += 8
                    reasons.append("input role matches description")
                elif role == "link" and any(kw in desc_lower for kw in link_keywords):
                    score += 8
                    reasons.append("link role matches description")
                
                # Check value/content match
                if node.get("value") and node["value"].lower() in desc_lower:
                    score += 6
                    reasons.append(f"value matches: {node['value']}")
                
                # Check properties
                properties = node.get("properties", {})
                if properties.get("class"):
                    for cls in properties["class"]:
                        if cls.lower() in desc_lower:
                            score += 4
                            reasons.append(f"class matches: {cls}")
                
                # Check element priority
                priority = properties.get("priority", "low")
                if priority == "high":
                    score += 2
                elif priority == "medium":
                    score += 1
                
                # If we have a reasonable match, add it
                if score >= 5:
                    matches.append({
                        "node": node,
                        "score": score,
                        "reasons": reasons,
                        "confidence": min(score / 15, 1.0)  # Normalize to 0-1
                    })
            
            # Sort by score (highest first)
            matches.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info("Element search completed", 
                       description=description,
                       matches_found=len(matches))
            
            return matches[:5]  # Return top 5 matches
            
        except Exception as e:
            logger.error("Failed to find elements by description", error=str(e))
            return []
    
    async def get_element_context(self, 
                                tree: Dict[str, Any], 
                                element_id: str) -> Dict[str, Any]:
        """Get contextual information about an element"""
        try:
            nodes = tree.get("nodes", [])
            target_node = None
            
            # Find the target node
            for node in nodes:
                if node.get("id") == element_id:
                    target_node = node
                    break
            
            if not target_node:
                return {"error": f"Element {element_id} not found"}
            
            # Get surrounding context
            context = {
                "element": target_node,
                "nearby_elements": [],
                "form_context": None,
                "navigation_context": None
            }
            
            # Find nearby interactive elements
            target_bounds = target_node.get("bounds", {})
            if target_bounds:
                for node in nodes:
                    if node.get("id") == element_id:
                        continue
                    
                    node_bounds = node.get("bounds", {})
                    if self._are_elements_nearby(target_bounds, node_bounds):
                        context["nearby_elements"].append({
                            "id": node["id"],
                            "name": node.get("name"),
                            "role": node.get("role"),
                            "distance": self._calculate_distance(target_bounds, node_bounds)
                        })
            
            # Sort nearby elements by distance
            context["nearby_elements"].sort(key=lambda x: x.get("distance", 1000))
            context["nearby_elements"] = context["nearby_elements"][:5]
            
            return context
            
        except Exception as e:
            logger.error("Failed to get element context", error=str(e))
            return {"error": str(e)}
    
    def _are_elements_nearby(self, bounds1: Dict[str, int], bounds2: Dict[str, int], threshold: int = 100) -> bool:
        """Check if two elements are visually nearby"""
        if not bounds1 or not bounds2:
            return False
        
        distance = self._calculate_distance(bounds1, bounds2)
        return distance <= threshold
    
    def _calculate_distance(self, bounds1: Dict[str, int], bounds2: Dict[str, int]) -> float:
        """Calculate visual distance between two elements"""
        if not bounds1 or not bounds2:
            return float('inf')
        
        # Calculate center points
        center1_x = bounds1.get("x", 0) + bounds1.get("width", 0) / 2
        center1_y = bounds1.get("y", 0) + bounds1.get("height", 0) / 2
        center2_x = bounds2.get("x", 0) + bounds2.get("width", 0) / 2
        center2_y = bounds2.get("y", 0) + bounds2.get("height", 0) / 2
        
        # Euclidean distance
        return ((center2_x - center1_x) ** 2 + (center2_y - center1_y) ** 2) ** 0.5
    
    def generate_ai_friendly_summary(self, tree: Dict[str, Any]) -> str:
        """Generate an AI-friendly summary of the page's interactive elements"""
        try:
            nodes = tree.get("nodes", [])
            if not nodes:
                return "No interactive elements found on this page."
            
            # Group elements by type
            element_groups = {}
            for node in nodes:
                role = node.get("role", "unknown")
                if role not in element_groups:
                    element_groups[role] = []
                element_groups[role].append(node)
            
            # Build summary
            summary_parts = []
            summary_parts.append(f"Found {len(nodes)} interactive elements on this page:")
            
            # Prioritize important element types
            priority_order = ['button', 'textbox', 'link', 'combobox', 'checkbox', 'radio']
            
            for role in priority_order:
                if role in element_groups:
                    elements = element_groups[role]
                    names = [elem.get("name", f"unnamed {role}") for elem in elements[:3]]  # Top 3
                    if len(elements) > 3:
                        summary_parts.append(f"- {len(elements)} {role}s including: {', '.join(names)} and {len(elements)-3} more")
                    else:
                        summary_parts.append(f"- {len(elements)} {role}s: {', '.join(names)}")
            
            # Add other element types
            other_roles = set(element_groups.keys()) - set(priority_order)
            if other_roles:
                other_counts = [f"{len(element_groups[role])} {role}s" for role in other_roles]
                summary_parts.append(f"- Other elements: {', '.join(other_counts)}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error("Failed to generate AI summary", error=str(e))
            return f"Error generating page summary: {str(e)}"

# Global instance
accessibility_extractor = AccessibilityTreeExtractor()