"""
Advanced Task Classification System for AI Browser
Analyzes user requests to determine complexity and appropriate execution strategy.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # Single action, clear intent
    MODERATE = "moderate"  # 2-3 actions, some planning needed
    COMPLEX = "complex"    # Multi-step workflow, requires planning
    AMBIGUOUS = "ambiguous" # Unclear intent, needs clarification

class TaskCategory(Enum):
    """Categories of browser tasks"""
    NAVIGATION = "navigation"
    FORM_FILLING = "form_filling"
    DATA_EXTRACTION = "data_extraction"
    SEARCH = "search"
    SHOPPING = "shopping"
    AUTHENTICATION = "authentication"
    CONTENT_INTERACTION = "content_interaction"
    WORKFLOW = "workflow"
    QUESTION_ANSWERING = "question_answering"
    PAGE_ANALYSIS = "page_analysis"

@dataclass
class TaskClassification:
    """Result of task classification"""
    complexity: TaskComplexity
    category: TaskCategory
    confidence: float
    intent_summary: str
    suggested_actions: List[Dict[str, Any]]
    requires_page_context: bool
    estimated_steps: int
    potential_challenges: List[str]
    success_criteria: List[str]

class IntelligentTaskClassifier:
    """Advanced task classifier that understands user intent and complexity"""
    
    def __init__(self):
        # Keyword patterns for different task categories
        self.category_patterns = {
            TaskCategory.NAVIGATION: {
                'keywords': ['go to', 'navigate to', 'visit', 'open', 'load'],
                'patterns': [
                    r'(?:go to|navigate to|visit|open)\s+([^\s]+\.com|[^\s]+\.org|[^\s]+\.net)',
                    r'take me to\s+(.+)',
                    r'open\s+(.+)\s+(?:website|page|site)'
                ],
                'weight': 0.8
            },
            TaskCategory.FORM_FILLING: {
                'keywords': ['fill', 'enter', 'type', 'input', 'form', 'submit', 'register', 'signup', 'sign up'],
                'patterns': [
                    r'fill (?:out|in)?\s*(?:the)?\s*form',
                    r'enter\s+(.+)\s+(?:in|into)\s+(.+)',
                    r'type\s+["\'](.+)["\']',
                    r'(?:sign up|register)\s+(?:for|with)'
                ],
                'weight': 0.9
            },
            TaskCategory.SEARCH: {
                'keywords': ['search', 'find', 'look for', 'lookup'],
                'patterns': [
                    r'search for\s+(.+)',
                    r'find\s+(.+)\s+(?:on|in)',
                    r'look (?:for|up)\s+(.+)'
                ],
                'weight': 0.8
            },
            TaskCategory.SHOPPING: {
                'keywords': ['buy', 'purchase', 'order', 'cart', 'checkout', 'add to cart'],
                'patterns': [
                    r'(?:buy|purchase|order)\s+(.+)',
                    r'add\s+(.+)\s+to\s+cart',
                    r'checkout|proceed to checkout'
                ],
                'weight': 0.9
            },
            TaskCategory.AUTHENTICATION: {
                'keywords': ['login', 'log in', 'sign in', 'signin', 'authenticate'],
                'patterns': [
                    r'(?:log|sign)\s+in',
                    r'login\s+(?:to|with)',
                    r'authenticate'
                ],
                'weight': 0.9
            },
            TaskCategory.DATA_EXTRACTION: {
                'keywords': ['extract', 'get', 'scrape', 'download', 'save', 'export'],
                'patterns': [
                    r'(?:extract|get|scrape)\s+(.+)\s+from',
                    r'download\s+(.+)',
                    r'save\s+(?:the)?\s*(.+)\s+(?:to|as)'
                ],
                'weight': 0.8
            },
            TaskCategory.QUESTION_ANSWERING: {
                'keywords': ['what', 'how', 'why', 'when', 'where', 'who', 'explain', 'tell me'],
                'patterns': [
                    r'^(?:what|how|why|when|where|who)\s+',
                    r'(?:explain|tell me)\s+(?:about|how)'
                ],
                'weight': 0.7
            }
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: {
                'max_actions': 1,
                'keywords': ['click', 'open', 'go to', 'what is'],
                'patterns': [r'^(?:click|open|go to)\s+']
            },
            TaskComplexity.MODERATE: {
                'max_actions': 3,
                'keywords': ['fill form', 'search and', 'login and'],
                'conjunctions': ['and', 'then']
            },
            TaskComplexity.COMPLEX: {
                'keywords': ['complete', 'workflow', 'process', 'setup', 'configure'],
                'conjunctions': ['and then', 'after that', 'next', 'finally'],
                'multi_step_indicators': ['step', 'first', 'second', 'third', 'last']
            }
        }
    
    async def classify_task(self, user_input: str, page_context: Dict[str, Any] = None) -> TaskClassification:
        """Classify a user task by complexity and category"""
        try:
            logger.info("Classifying user task", input_preview=user_input[:100])
            
            # Clean and normalize input
            normalized_input = self._normalize_input(user_input)
            
            # Determine task category
            category, category_confidence = self._classify_category(normalized_input)
            
            # Determine complexity
            complexity, complexity_confidence = self._classify_complexity(normalized_input, page_context)
            
            # Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(
                normalized_input, category, complexity, page_context
            )
            
            # Estimate steps and challenges
            estimated_steps = self._estimate_steps(complexity, suggested_actions)
            potential_challenges = self._identify_challenges(category, complexity, page_context)
            success_criteria = self._define_success_criteria(category, normalized_input)
            
            # Overall confidence
            overall_confidence = (category_confidence + complexity_confidence) / 2
            
            classification = TaskClassification(
                complexity=complexity,
                category=category,
                confidence=overall_confidence,
                intent_summary=self._summarize_intent(normalized_input, category),
                suggested_actions=suggested_actions,
                requires_page_context=self._requires_page_context(category),
                estimated_steps=estimated_steps,
                potential_challenges=potential_challenges,
                success_criteria=success_criteria
            )
            
            logger.info("Task classification completed", 
                       category=category.value,
                       complexity=complexity.value,
                       confidence=overall_confidence)
            
            return classification
            
        except Exception as e:
            logger.error("Task classification failed", error=str(e))
            # Return safe fallback
            return TaskClassification(
                complexity=TaskComplexity.AMBIGUOUS,
                category=TaskCategory.QUESTION_ANSWERING,
                confidence=0.5,
                intent_summary="Unable to classify task clearly",
                suggested_actions=[],
                requires_page_context=True,
                estimated_steps=1,
                potential_challenges=["Task intent unclear"],
                success_criteria=["User satisfaction"]
            )
    
    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for better analysis"""
        # Convert to lowercase
        normalized = user_input.lower().strip()
        
        # Remove common filler words that don't affect intent
        filler_words = ['please', 'can you', 'could you', 'would you', 'i want to', 'i need to', 'help me']
        for filler in filler_words:
            normalized = normalized.replace(filler, '').strip()
        
        # Normalize common variations
        replacements = {
            'log in': 'login',
            'sign in': 'signin',
            'sign up': 'signup',
            'check out': 'checkout',
            'look up': 'lookup'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _classify_category(self, normalized_input: str) -> Tuple[TaskCategory, float]:
        """Classify the task category"""
        category_scores = {}
        
        for category, info in self.category_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in info['keywords']:
                if keyword in normalized_input:
                    score += info['weight']
            
            # Check patterns
            for pattern in info['patterns']:
                if re.search(pattern, normalized_input, re.IGNORECASE):
                    score += info['weight'] * 1.2  # Patterns are more specific
            
            category_scores[category] = score
        
        # Get the category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            best_score = category_scores[best_category]
            
            # Normalize confidence (0-1)
            confidence = min(best_score / 2.0, 1.0)  # Assuming max reasonable score is 2
            
            if confidence > 0.3:
                return best_category, confidence
        
        # Fallback to question answering if no clear category
        return TaskCategory.QUESTION_ANSWERING, 0.5
    
    def _classify_complexity(self, normalized_input: str, page_context: Dict[str, Any] = None) -> Tuple[TaskComplexity, float]:
        """Classify task complexity"""
        
        # Count conjunctions and multi-step indicators
        conjunctions = len(re.findall(r'\b(?:and|then|after|next|finally)\b', normalized_input))
        multi_step_words = len(re.findall(r'\b(?:first|second|third|step|process|workflow)\b', normalized_input))
        
        # Check for complex keywords
        complex_keywords = ['complete', 'setup', 'configure', 'process', 'workflow', 'entire', 'full']
        complex_count = sum(1 for kw in complex_keywords if kw in normalized_input)
        
        # Sentence complexity
        sentences = len(normalized_input.split('.'))
        words = len(normalized_input.split())
        
        # Scoring
        complexity_score = 0
        
        if conjunctions >= 2:
            complexity_score += 2
        elif conjunctions == 1:
            complexity_score += 1
            
        if multi_step_words > 0:
            complexity_score += 2
            
        if complex_count > 0:
            complexity_score += 1
            
        if words > 20:
            complexity_score += 1
            
        if sentences > 2:
            complexity_score += 1
        
        # Classify based on score
        if complexity_score >= 4:
            return TaskComplexity.COMPLEX, 0.8
        elif complexity_score >= 2:
            return TaskComplexity.MODERATE, 0.7
        elif complexity_score >= 1:
            return TaskComplexity.MODERATE, 0.6
        else:
            return TaskComplexity.SIMPLE, 0.8
    
    async def _generate_suggested_actions(self, 
                                        normalized_input: str,
                                        category: TaskCategory,
                                        complexity: TaskComplexity,
                                        page_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate suggested actions based on classification"""
        actions = []
        
        if category == TaskCategory.NAVIGATION:
            # Extract URL if mentioned
            url_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})', normalized_input)
            if url_match:
                actions.append({
                    'type': 'navigate',
                    'parameters': {'url': url_match.group(0)},
                    'description': f"Navigate to {url_match.group(0)}"
                })
        
        elif category == TaskCategory.FORM_FILLING:
            actions.append({
                'type': 'find',
                'parameters': {'query': 'form'},
                'description': "Locate form on page"
            })
            actions.append({
                'type': 'extract',
                'parameters': {'target': 'form_fields'},
                'description': "Analyze form fields"
            })
        
        elif category == TaskCategory.SEARCH:
            search_query = re.search(r'search (?:for\s+)?(.+)', normalized_input)
            if search_query:
                actions.append({
                    'type': 'find',
                    'parameters': {'query': 'search box'},
                    'description': "Find search input field"
                })
                actions.append({
                    'type': 'type',
                    'parameters': {'text': search_query.group(1)},
                    'description': f"Enter search term: {search_query.group(1)}"
                })
        
        elif category == TaskCategory.SHOPPING:
            if 'add to cart' in normalized_input:
                actions.append({
                    'type': 'find',
                    'parameters': {'query': 'add to cart button'},
                    'description': "Find 'Add to Cart' button"
                })
                actions.append({
                    'type': 'click',
                    'parameters': {'target': 'add to cart'},
                    'description': "Click 'Add to Cart'"
                })
        
        elif category == TaskCategory.AUTHENTICATION:
            actions.append({
                'type': 'find',
                'parameters': {'query': 'login form'},
                'description': "Locate login form"
            })
            actions.append({
                'type': 'find',
                'parameters': {'query': 'username field'},
                'description': "Find username/email field"
            })
            actions.append({
                'type': 'find',
                'parameters': {'query': 'password field'},
                'description': "Find password field"
            })
        
        return actions
    
    def _estimate_steps(self, complexity: TaskComplexity, suggested_actions: List[Dict[str, Any]]) -> int:
        """Estimate number of steps for task completion"""
        base_steps = len(suggested_actions)
        
        if complexity == TaskComplexity.SIMPLE:
            return max(base_steps, 1)
        elif complexity == TaskComplexity.MODERATE:
            return max(base_steps, 3)
        elif complexity == TaskComplexity.COMPLEX:
            return max(base_steps, 5)
        else:
            return 2  # AMBIGUOUS
    
    def _identify_challenges(self, 
                           category: TaskCategory, 
                           complexity: TaskComplexity,
                           page_context: Dict[str, Any] = None) -> List[str]:
        """Identify potential challenges for task completion"""
        challenges = []
        
        # Category-specific challenges
        if category == TaskCategory.FORM_FILLING:
            challenges.extend([
                "Form fields may be dynamically loaded",
                "Required field validation",
                "CAPTCHA verification might be needed"
            ])
        
        elif category == TaskCategory.SHOPPING:
            challenges.extend([
                "Product may be out of stock",
                "Login required for checkout",
                "Payment method selection"
            ])
        
        elif category == TaskCategory.AUTHENTICATION:
            challenges.extend([
                "Two-factor authentication",
                "Password requirements",
                "Account lockout after failed attempts"
            ])
        
        # Complexity-specific challenges
        if complexity == TaskComplexity.COMPLEX:
            challenges.extend([
                "Multi-step workflow coordination",
                "State management across pages",
                "Error recovery and retry logic"
            ])
        
        # Page context challenges
        if page_context and page_context.get('url'):
            if 'login' in page_context['url']:
                challenges.append("Authentication required")
            if 'checkout' in page_context['url']:
                challenges.append("Payment processing required")
        
        return challenges
    
    def _define_success_criteria(self, category: TaskCategory, normalized_input: str) -> List[str]:
        """Define success criteria for task completion"""
        criteria = ["Task completed without errors"]
        
        if category == TaskCategory.NAVIGATION:
            criteria.append("Successfully loaded target page")
            criteria.append("Page content is accessible")
        
        elif category == TaskCategory.FORM_FILLING:
            criteria.extend([
                "All required fields filled correctly",
                "Form submitted successfully",
                "Confirmation message displayed"
            ])
        
        elif category == TaskCategory.SEARCH:
            criteria.extend([
                "Search query executed",
                "Results displayed",
                "Relevant results found"
            ])
        
        elif category == TaskCategory.SHOPPING:
            criteria.extend([
                "Product added to cart",
                "Cart updated correctly",
                "Checkout process available"
            ])
        
        elif category == TaskCategory.AUTHENTICATION:
            criteria.extend([
                "Login credentials accepted",
                "User successfully authenticated",
                "Access to protected content granted"
            ])
        
        return criteria
    
    def _summarize_intent(self, normalized_input: str, category: TaskCategory) -> str:
        """Generate a concise summary of user intent"""
        if category == TaskCategory.NAVIGATION:
            return f"Navigate to specified website or page"
        elif category == TaskCategory.FORM_FILLING:
            return f"Fill out and submit form with provided information"
        elif category == TaskCategory.SEARCH:
            return f"Search for specified content or information"
        elif category == TaskCategory.SHOPPING:
            return f"Complete shopping task (browse, add to cart, checkout)"
        elif category == TaskCategory.AUTHENTICATION:
            return f"Log into account or authenticate user"
        elif category == TaskCategory.DATA_EXTRACTION:
            return f"Extract and retrieve specific data from page"
        else:
            return f"Answer question or provide information about page content"
    
    def _requires_page_context(self, category: TaskCategory) -> bool:
        """Determine if task requires current page context"""
        context_required = [
            TaskCategory.FORM_FILLING,
            TaskCategory.DATA_EXTRACTION,
            TaskCategory.CONTENT_INTERACTION,
            TaskCategory.PAGE_ANALYSIS,
            TaskCategory.QUESTION_ANSWERING
        ]
        return category in context_required

# Global instance
task_classifier = IntelligentTaskClassifier()