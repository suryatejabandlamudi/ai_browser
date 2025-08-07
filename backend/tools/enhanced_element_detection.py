#!/usr/bin/env python3
"""
Enhanced Element Detection System
Inspired by GPT-OSS browser tools with stateful context management
and intelligent element finding strategies
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import hashlib
from pydantic import Field

from .base_tool import BaseTool, ToolSchema, ToolResult

class ElementDetectionStrategy(str, Enum):
    """Different strategies for finding elements"""
    ACCESSIBILITY = "accessibility"  # Use accessibility tree
    VISUAL = "visual"               # Use visual properties
    SEMANTIC = "semantic"           # Use semantic understanding
    HYBRID = "hybrid"               # Combine multiple strategies
    DESCRIPTION = "description"     # Natural language description

class ElementConfidence(str, Enum):
    """Confidence levels for element detection"""
    HIGH = "high"         # >90% confidence
    MEDIUM = "medium"     # 70-90% confidence 
    LOW = "low"           # 50-70% confidence
    UNCERTAIN = "uncertain"  # <50% confidence

@dataclass
class ElementCandidate:
    """A potential element match with confidence scoring"""
    selector: str
    confidence: float
    strategy: ElementDetectionStrategy
    bounds: Dict[str, int]
    text: str
    role: Optional[str] = None
    attributes: Dict[str, str] = None
    reasoning: str = ""

class StatefulBrowserContext:
    """Stateful context manager inspired by GPT-OSS browser tool design"""
    
    def __init__(self, cache_duration: int = 30):
        self.cache_duration = cache_duration
        self.page_cache: Dict[str, Dict] = {}
        self.element_cache: Dict[str, List[ElementCandidate]] = {}
        self.interaction_history: List[Dict] = []
        self.current_page_hash = None
        
    def get_page_key(self, url: str, content_sample: str = "") -> str:
        """Generate cache key for page state"""
        content_hash = hashlib.md5((url + content_sample[:1000]).encode()).hexdigest()[:8]
        return f"{url}_{content_hash}"
    
    def is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry.get('timestamp', 0) < self.cache_duration
    
    def cache_page_state(self, url: str, page_data: Dict):
        """Cache page state for reuse"""
        page_key = self.get_page_key(url, page_data.get('content', '')[:1000])
        self.page_cache[page_key] = {
            'data': page_data,
            'timestamp': time.time()
        }
        self.current_page_hash = page_key
    
    def get_cached_page_state(self, url: str, content_sample: str = "") -> Optional[Dict]:
        """Get cached page state if valid"""
        page_key = self.get_page_key(url, content_sample)
        if page_key in self.page_cache and self.is_cache_valid(self.page_cache[page_key]):
            return self.page_cache[page_key]['data']
        return None
    
    def record_interaction(self, interaction_type: str, target: str, success: bool, **kwargs):
        """Record interaction for learning and context"""
        self.interaction_history.append({
            'type': interaction_type,
            'target': target,
            'success': success,
            'timestamp': time.time(),
            'page_hash': self.current_page_hash,
            **kwargs
        })
        
        # Keep only last 50 interactions
        if len(self.interaction_history) > 50:
            self.interaction_history = self.interaction_history[-50:]

class IntelligentElementFinder:
    """Enhanced element finder using multiple strategies"""
    
    def __init__(self, context: StatefulBrowserContext):
        self.context = context
        
    def find_elements_by_description(self, description: str, page_data: Dict) -> List[ElementCandidate]:
        """Find elements using natural language description with multiple strategies"""
        candidates = []
        
        # Strategy 1: Accessibility-based search
        accessibility_candidates = self._find_by_accessibility(description, page_data)
        candidates.extend(accessibility_candidates)
        
        # Strategy 2: Visual property search
        visual_candidates = self._find_by_visual_properties(description, page_data)
        candidates.extend(visual_candidates)
        
        # Strategy 3: Semantic content search
        semantic_candidates = self._find_by_semantic_content(description, page_data)
        candidates.extend(semantic_candidates)
        
        # Strategy 4: Learning from interaction history
        historical_candidates = self._find_by_interaction_history(description, page_data)
        candidates.extend(historical_candidates)
        
        # Deduplicate and rank by confidence
        unique_candidates = self._deduplicate_candidates(candidates)
        ranked_candidates = self._rank_candidates(unique_candidates, description)
        
        return ranked_candidates[:10]  # Return top 10 candidates
    
    def _find_by_accessibility(self, description: str, page_data: Dict) -> List[ElementCandidate]:
        """Find elements using accessibility properties"""
        candidates = []
        interactive_elements = page_data.get('content', {}).get('interactive', [])
        
        description_lower = description.lower()
        
        for element in interactive_elements:
            confidence = 0.0
            reasoning_parts = []
            
            # Check aria-label
            if element.get('ariaLabel') and description_lower in element['ariaLabel'].lower():
                confidence += 0.4
                reasoning_parts.append(f"aria-label matches '{description}'")
            
            # Check element text
            if element.get('text') and description_lower in element['text'].lower():
                confidence += 0.3
                reasoning_parts.append(f"text content matches '{description}'")
            
            # Check placeholder
            if element.get('placeholder') and description_lower in element['placeholder'].lower():
                confidence += 0.2
                reasoning_parts.append(f"placeholder matches '{description}'")
            
            # Check element type/role relevance
            if self._is_relevant_element_type(description, element.get('tag'), element.get('type')):
                confidence += 0.1
                reasoning_parts.append("element type is relevant")
            
            if confidence > 0.1:  # Minimum threshold
                candidates.append(ElementCandidate(
                    selector=element.get('selector', ''),
                    confidence=confidence,
                    strategy=ElementDetectionStrategy.ACCESSIBILITY,
                    bounds=element.get('position', {}),
                    text=element.get('text', ''),
                    role=element.get('type', ''),
                    attributes={
                        'id': element.get('id', ''),
                        'classes': element.get('classes', ''),
                        'ariaLabel': element.get('ariaLabel', '')
                    },
                    reasoning='; '.join(reasoning_parts)
                ))
        
        return candidates
    
    def _find_by_visual_properties(self, description: str, page_data: Dict) -> List[ElementCandidate]:
        """Find elements using visual properties and positioning"""
        candidates = []
        interactive_elements = page_data.get('content', {}).get('interactive', [])
        
        # Look for visual keywords in description
        visual_keywords = {
            'button': ['button'],
            'link': ['link', 'anchor'],
            'input': ['input', 'field', 'textbox'],
            'top': ['top', 'upper', 'header'],
            'bottom': ['bottom', 'lower', 'footer'],
            'right': ['right', 'side'],
            'left': ['left', 'side'],
            'center': ['center', 'middle']
        }
        
        description_lower = description.lower()
        
        for element in interactive_elements:
            confidence = 0.0
            reasoning_parts = []
            
            # Element type matching
            for element_type, keywords in visual_keywords.items():
                if any(keyword in description_lower for keyword in keywords):
                    if element.get('tag') == element_type or element.get('type') == element_type:
                        confidence += 0.3
                        reasoning_parts.append(f"element type '{element_type}' matches description")
            
            # Position-based matching
            position = element.get('position', {})
            if position:
                if 'top' in description_lower and position.get('y', 0) < 200:
                    confidence += 0.2
                    reasoning_parts.append("positioned in top area")
                elif 'bottom' in description_lower and position.get('y', 0) > 600:
                    confidence += 0.2
                    reasoning_parts.append("positioned in bottom area")
                
                if 'right' in description_lower and position.get('x', 0) > 800:
                    confidence += 0.1
                    reasoning_parts.append("positioned on right side")
                elif 'left' in description_lower and position.get('x', 0) < 200:
                    confidence += 0.1
                    reasoning_parts.append("positioned on left side")
            
            if confidence > 0.1:
                candidates.append(ElementCandidate(
                    selector=element.get('selector', ''),
                    confidence=confidence,
                    strategy=ElementDetectionStrategy.VISUAL,
                    bounds=position,
                    text=element.get('text', ''),
                    reasoning='; '.join(reasoning_parts)
                ))
        
        return candidates
    
    def _find_by_semantic_content(self, description: str, page_data: Dict) -> List[ElementCandidate]:
        """Find elements using semantic content analysis"""
        candidates = []
        interactive_elements = page_data.get('content', {}).get('interactive', [])
        
        # Extract key terms from description
        key_terms = self._extract_key_terms(description)
        
        for element in interactive_elements:
            confidence = 0.0
            reasoning_parts = []
            
            element_text = element.get('text', '').lower()
            element_aria = element.get('ariaLabel', '').lower()
            element_id = element.get('id', '').lower()
            element_classes = element.get('classes', '').lower()
            
            # Check semantic similarity with key terms
            for term in key_terms:
                term_lower = term.lower()
                
                if term_lower in element_text:
                    confidence += 0.3
                    reasoning_parts.append(f"text contains '{term}'")
                elif term_lower in element_aria:
                    confidence += 0.25
                    reasoning_parts.append(f"aria-label contains '{term}'")
                elif term_lower in element_id:
                    confidence += 0.2
                    reasoning_parts.append(f"id contains '{term}'")
                elif term_lower in element_classes:
                    confidence += 0.15
                    reasoning_parts.append(f"classes contain '{term}'")
            
            # Bonus for exact phrase matches
            if description.lower() in element_text:
                confidence += 0.4
                reasoning_parts.append("exact phrase match in text")
            
            if confidence > 0.1:
                candidates.append(ElementCandidate(
                    selector=element.get('selector', ''),
                    confidence=confidence,
                    strategy=ElementDetectionStrategy.SEMANTIC,
                    bounds=element.get('position', {}),
                    text=element.get('text', ''),
                    reasoning='; '.join(reasoning_parts)
                ))
        
        return candidates
    
    def _find_by_interaction_history(self, description: str, page_data: Dict) -> List[ElementCandidate]:
        """Learn from previous successful interactions"""
        candidates = []
        
        # Find similar successful interactions
        similar_interactions = [
            interaction for interaction in self.context.interaction_history
            if interaction['success'] and 
            self._are_descriptions_similar(description, interaction.get('description', ''))
        ]
        
        interactive_elements = page_data.get('content', {}).get('interactive', [])
        
        for interaction in similar_interactions:
            target_selector = interaction.get('target', '')
            
            # Find matching element in current page
            for element in interactive_elements:
                if element.get('selector') == target_selector or \
                   self._selectors_likely_same_element(element.get('selector', ''), target_selector):
                    
                    confidence = 0.6  # High confidence from successful history
                    reasoning = f"Previously successful interaction with similar description"
                    
                    candidates.append(ElementCandidate(
                        selector=element.get('selector', ''),
                        confidence=confidence,
                        strategy=ElementDetectionStrategy.HYBRID,
                        bounds=element.get('position', {}),
                        text=element.get('text', ''),
                        reasoning=reasoning
                    ))
        
        return candidates
    
    def _deduplicate_candidates(self, candidates: List[ElementCandidate]) -> List[ElementCandidate]:
        """Remove duplicate candidates, keeping the highest confidence one"""
        seen_selectors = {}
        
        for candidate in candidates:
            selector = candidate.selector
            if selector not in seen_selectors or candidate.confidence > seen_selectors[selector].confidence:
                seen_selectors[selector] = candidate
        
        return list(seen_selectors.values())
    
    def _rank_candidates(self, candidates: List[ElementCandidate], description: str) -> List[ElementCandidate]:
        """Rank candidates by confidence and relevance"""
        # Apply additional ranking factors
        for candidate in candidates:
            # Boost confidence for elements with better visibility
            if candidate.bounds.get('width', 0) > 0 and candidate.bounds.get('height', 0) > 0:
                candidate.confidence += 0.05
            
            # Boost confidence for elements with accessible names
            if candidate.text and len(candidate.text.strip()) > 0:
                candidate.confidence += 0.05
            
            # Apply confidence level classification
            if candidate.confidence >= 0.9:
                candidate.confidence = min(candidate.confidence, 0.99)  # Cap at 99%
        
        # Sort by confidence (highest first)
        return sorted(candidates, key=lambda x: x.confidence, reverse=True)
    
    # Helper methods
    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from description"""
        # Simple keyword extraction - could be enhanced with NLP
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = description.lower().split()
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _is_relevant_element_type(self, description: str, tag: str, element_type: str) -> bool:
        """Check if element type is relevant to description"""
        type_keywords = {
            'button': ['button', 'click', 'press', 'submit'],
            'input': ['type', 'enter', 'input', 'field'],
            'a': ['link', 'navigate', 'go to', 'visit'],
            'select': ['choose', 'select', 'dropdown']
        }
        
        description_lower = description.lower()
        
        if tag in type_keywords:
            return any(keyword in description_lower for keyword in type_keywords[tag])
        
        if element_type in type_keywords:
            return any(keyword in description_lower for keyword in type_keywords[element_type])
        
        return False
    
    def _are_descriptions_similar(self, desc1: str, desc2: str) -> bool:
        """Simple similarity check for descriptions"""
        if not desc1 or not desc2:
            return False
        
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity > 0.3  # 30% word overlap threshold
    
    def _selectors_likely_same_element(self, selector1: str, selector2: str) -> bool:
        """Check if two selectors likely point to the same element"""
        if selector1 == selector2:
            return True
        
        # Check for similar ID-based selectors
        if selector1.startswith('#') and selector2.startswith('#'):
            return selector1 == selector2
        
        # Check for similar class-based selectors
        if '.' in selector1 and '.' in selector2:
            classes1 = set(selector1.replace('.', ' ').split())
            classes2 = set(selector2.replace('.', ' ').split())
            overlap = len(classes1.intersection(classes2))
            return overlap > 0 and overlap / max(len(classes1), len(classes2)) > 0.7
        
        return False

class SmartElementFindSchema(ToolSchema):
    """Schema for smart element finding"""
    description: str = Field(description="Natural language description of the element to find")
    strategy: Optional[ElementDetectionStrategy] = Field(default=ElementDetectionStrategy.HYBRID, 
                                                        description="Detection strategy to use")
    max_candidates: int = Field(default=5, description="Maximum number of candidates to return")
    confidence_threshold: float = Field(default=0.1, description="Minimum confidence threshold")

class SmartElementFindTool(BaseTool):
    """Enhanced element finding tool using multiple strategies and learning"""
    
    def __init__(self, context: Optional[StatefulBrowserContext] = None):
        super().__init__(
            name="smart_find_element",
            description="Find elements using intelligent multi-strategy detection with learning",
            schema=SmartElementFindSchema
        )
        self.context = context or StatefulBrowserContext()
        self.element_finder = IntelligentElementFinder(self.context)
    
    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        description = params["description"]
        strategy = params.get("strategy", ElementDetectionStrategy.HYBRID)
        max_candidates = params.get("max_candidates", 5)
        confidence_threshold = params.get("confidence_threshold", 0.1)
        
        # Get page data from context
        page_data = context.get("page_data", {})
        if not page_data:
            return ToolResult(
                success=False,
                error="No page data available for element detection"
            )
        
        # Cache current page state
        page_url = context.get("page_url", "")
        self.context.cache_page_state(page_url, page_data)
        
        try:
            # Find element candidates
            candidates = self.element_finder.find_elements_by_description(description, page_data)
            
            # Filter by confidence threshold
            qualified_candidates = [
                candidate for candidate in candidates 
                if candidate.confidence >= confidence_threshold
            ][:max_candidates]
            
            if not qualified_candidates:
                return ToolResult(
                    success=False,
                    message=f"No elements found matching '{description}' with confidence >= {confidence_threshold}",
                    data={
                        "candidates_found": len(candidates),
                        "qualified_candidates": 0,
                        "description": description
                    }
                )
            
            # Prepare results
            results = []
            for candidate in qualified_candidates:
                confidence_level = self._get_confidence_level(candidate.confidence)
                results.append({
                    "selector": candidate.selector,
                    "confidence": round(candidate.confidence, 3),
                    "confidence_level": confidence_level.value,
                    "strategy": candidate.strategy.value,
                    "text": candidate.text,
                    "bounds": candidate.bounds,
                    "role": candidate.role,
                    "reasoning": candidate.reasoning
                })
            
            best_candidate = qualified_candidates[0]
            
            return ToolResult(
                success=True,
                message=f"Found {len(results)} element candidates for '{description}'",
                data={
                    "action": "smart_find_element",
                    "description": description,
                    "best_match": {
                        "selector": best_candidate.selector,
                        "confidence": round(best_candidate.confidence, 3),
                        "strategy": best_candidate.strategy.value,
                        "reasoning": best_candidate.reasoning
                    },
                    "all_candidates": results,
                    "instructions": f"Best match: {best_candidate.selector} (confidence: {round(best_candidate.confidence, 3)})"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Element detection failed: {str(e)}",
                data={"description": description}
            )
    
    def _get_confidence_level(self, confidence: float) -> ElementConfidence:
        """Convert numeric confidence to confidence level enum"""
        if confidence >= 0.9:
            return ElementConfidence.HIGH
        elif confidence >= 0.7:
            return ElementConfidence.MEDIUM
        elif confidence >= 0.5:
            return ElementConfidence.LOW
        else:
            return ElementConfidence.UNCERTAIN

# Helper function to register enhanced element detection tools
def register_enhanced_element_detection_tools():
    """Register enhanced element detection tools"""
    from .base_tool import tool_registry, ToolType
    
    # Create shared context for learning across tool instances
    shared_context = StatefulBrowserContext(cache_duration=60)  # 60 second cache
    
    tool = SmartElementFindTool(context=shared_context)
    tool_registry.register(tool, ToolType.INTERACTION)
