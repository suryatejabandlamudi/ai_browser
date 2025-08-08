#!/usr/bin/env python3
"""
Intelligent Browsing System for AI Browser
Advanced AI-powered page understanding, smart search, and content analysis
"""

import asyncio
import json
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import structlog
from bs4 import BeautifulSoup
import urllib.parse

logger = structlog.get_logger(__name__)

@dataclass
class PageInsight:
    """Structured insights about a webpage"""
    url: str
    title: str
    content_type: str  # "article", "product", "form", "search", "social", "news"
    summary: str
    key_entities: List[str]
    actionable_elements: List[Dict[str, Any]]
    sentiment: str  # "positive", "negative", "neutral"
    reading_time: int  # minutes
    complexity_score: float  # 0-1
    trustworthiness: float  # 0-1
    privacy_score: float  # 0-1
    extracted_data: Dict[str, Any]
    ai_recommendations: List[str]
    timestamp: str

@dataclass
class SearchContext:
    """Context for intelligent search"""
    query: str
    intent: str  # "information", "navigation", "transaction", "local"
    entities: List[str]
    related_topics: List[str]
    suggested_refinements: List[str]
    expected_result_types: List[str]

class IntelligentBrowsingSystem:
    """Advanced AI-powered browsing intelligence"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.page_cache = {}
        self.search_history = []
        self.user_interests = set()
        self.content_patterns = {}
        
        # Initialize content understanding patterns
        self._load_content_patterns()
        
    def _load_content_patterns(self):
        """Load patterns for content type detection"""
        self.content_patterns = {
            "ecommerce": [
                r"add to cart", r"buy now", r"price", r"\$\d+", r"checkout",
                r"product", r"shipping", r"reviews?", r"rating"
            ],
            "article": [
                r"<article", r"byline", r"published", r"author", r"read time",
                r"paragraph", r"heading", r"<h[1-6]"
            ],
            "form": [
                r"<form", r"<input", r"submit", r"required", r"email",
                r"password", r"login", r"register"
            ],
            "social": [
                r"share", r"like", r"follow", r"tweet", r"post", r"comment",
                r"social", r"facebook", r"twitter", r"linkedin"
            ],
            "news": [
                r"breaking", r"updated", r"reporter", r"news", r"story",
                r"headline", r"developing", r"latest"
            ]
        }
    
    async def analyze_page(self, url: str, html: str, user_context: Dict[str, Any] = None) -> PageInsight:
        """Perform comprehensive AI-powered page analysis"""
        try:
            logger.info("Starting intelligent page analysis", url=url)
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic metadata
            title = self._extract_title(soup)
            content_type = await self._classify_content_type(soup, html)
            
            # Extract and clean main content
            main_content = self._extract_main_content(soup)
            
            # AI-powered analysis
            ai_analysis = await self._ai_analyze_content(url, title, main_content, user_context)
            
            # Extract structured data
            structured_data = self._extract_structured_data(soup)
            
            # Calculate metrics
            reading_time = self._calculate_reading_time(main_content)
            complexity_score = await self._calculate_complexity(main_content)
            trustworthiness = await self._assess_trustworthiness(url, soup, ai_analysis)
            privacy_score = await self._assess_privacy(soup)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(url, ai_analysis, user_context)
            
            # Create comprehensive insight
            insight = PageInsight(
                url=url,
                title=title,
                content_type=content_type,
                summary=ai_analysis.get("summary", ""),
                key_entities=ai_analysis.get("entities", []),
                actionable_elements=self._find_actionable_elements(soup),
                sentiment=ai_analysis.get("sentiment", "neutral"),
                reading_time=reading_time,
                complexity_score=complexity_score,
                trustworthiness=trustworthiness,
                privacy_score=privacy_score,
                extracted_data=structured_data,
                ai_recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            # Cache the insight
            self.page_cache[url] = insight
            
            # Update user interests
            self._update_user_interests(ai_analysis.get("entities", []))
            
            logger.info("Page analysis completed", 
                       url=url, 
                       content_type=content_type,
                       entities=len(ai_analysis.get("entities", [])))
            
            return insight
            
        except Exception as e:
            logger.error("Page analysis failed", url=url, error=str(e))
            # Return basic insight on failure
            return PageInsight(
                url=url,
                title=self._extract_title(BeautifulSoup(html, 'html.parser')),
                content_type="unknown",
                summary="Analysis failed",
                key_entities=[],
                actionable_elements=[],
                sentiment="neutral",
                reading_time=0,
                complexity_score=0.5,
                trustworthiness=0.5,
                privacy_score=0.5,
                extracted_data={},
                ai_recommendations=[],
                timestamp=datetime.now().isoformat()
            )
    
    async def smart_search_understanding(self, query: str, context: Dict[str, Any] = None) -> SearchContext:
        """Understand search intent and provide intelligent context"""
        try:
            logger.info("Analyzing search query", query=query)
            
            if not self.ai_client:
                return self._basic_search_analysis(query)
            
            # AI-powered query analysis
            analysis_prompt = f"""Analyze this search query and provide structured insights:

Query: "{query}"
Context: {json.dumps(context or {}, indent=2)}

Provide analysis in JSON format:
{{
    "intent": "information|navigation|transaction|local",
    "entities": ["entity1", "entity2"],
    "related_topics": ["topic1", "topic2"],
    "suggested_refinements": ["refined query 1", "refined query 2"],
    "expected_result_types": ["articles", "products", "videos", "images"],
    "confidence": 0.95,
    "complexity": "simple|medium|complex",
    "search_strategy": "detailed search strategy recommendation"
}}

Consider:
1. User intent behind the query
2. Named entities and key concepts
3. Related topics that might be relevant
4. How to refine the search for better results
5. What types of content would best answer this query
"""

            response = await self.ai_client.chat(analysis_prompt, max_tokens=500)
            
            try:
                content = response.get("content", "")
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    analysis = json.loads(content[json_start:json_end])
                else:
                    analysis = json.loads(content)
                
                search_context = SearchContext(
                    query=query,
                    intent=analysis.get("intent", "information"),
                    entities=analysis.get("entities", []),
                    related_topics=analysis.get("related_topics", []),
                    suggested_refinements=analysis.get("suggested_refinements", []),
                    expected_result_types=analysis.get("expected_result_types", ["articles"])
                )
                
                logger.info("Search analysis completed", 
                           intent=search_context.intent,
                           entities=len(search_context.entities))
                
                return search_context
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI search analysis, using basic")
                return self._basic_search_analysis(query)
                
        except Exception as e:
            logger.error("Search understanding failed", query=query, error=str(e))
            return self._basic_search_analysis(query)
    
    async def generate_search_suggestions(self, partial_query: str, history: List[str] = None) -> List[str]:
        """Generate intelligent search suggestions"""
        try:
            if not self.ai_client:
                return self._basic_suggestions(partial_query)
            
            # Include user's search history and interests
            user_context = {
                "recent_searches": history[-5:] if history else [],
                "user_interests": list(self.user_interests)[:10],
                "partial_query": partial_query
            }
            
            suggestion_prompt = f"""Generate intelligent search suggestions for the partial query.

Partial Query: "{partial_query}"
User Context: {json.dumps(user_context, indent=2)}

Generate 8-10 diverse, helpful search suggestions that:
1. Complete the partial query naturally
2. Consider the user's interests and search history
3. Cover different aspects/angles of the topic
4. Include specific and general variations
5. Are practical and likely to yield good results

Return as JSON array:
["suggestion 1", "suggestion 2", ...]

Focus on being helpful and comprehensive while staying relevant to the partial query.
"""

            response = await self.ai_client.chat(suggestion_prompt, max_tokens=300)
            
            try:
                content = response.get("content", "")
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    suggestions = json.loads(content[json_start:json_end])
                else:
                    suggestions = json.loads(content)
                
                # Filter and validate suggestions
                valid_suggestions = []
                for suggestion in suggestions[:10]:
                    if isinstance(suggestion, str) and len(suggestion) > len(partial_query):
                        valid_suggestions.append(suggestion)
                
                return valid_suggestions[:8]
                
            except json.JSONDecodeError:
                return self._basic_suggestions(partial_query)
                
        except Exception as e:
            logger.error("Search suggestion generation failed", error=str(e))
            return self._basic_suggestions(partial_query)
    
    async def extract_page_actions(self, url: str, html: str, user_goal: str) -> List[Dict[str, Any]]:
        """Extract possible actions user can take on the page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all interactive elements
            interactive_elements = []
            
            # Buttons
            for button in soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]']):
                text = self._get_element_text(button)
                if text:
                    interactive_elements.append({
                        "type": "button",
                        "text": text,
                        "element": str(button)[:200],
                        "action": "click"
                    })
            
            # Links
            for link in soup.find_all('a', href=True):
                text = self._get_element_text(link)
                href = link.get('href')
                if text and href:
                    interactive_elements.append({
                        "type": "link",
                        "text": text,
                        "url": urllib.parse.urljoin(url, href),
                        "action": "navigate"
                    })
            
            # Forms
            for form in soup.find_all('form'):
                inputs = form.find_all(['input', 'textarea', 'select'])
                if inputs:
                    interactive_elements.append({
                        "type": "form",
                        "fields": len(inputs),
                        "action": form.get('action', ''),
                        "method": form.get('method', 'get'),
                        "action": "fill_form"
                    })
            
            # AI-powered action relevance analysis
            if self.ai_client and user_goal:
                relevant_actions = await self._analyze_action_relevance(
                    interactive_elements, user_goal, url
                )
                return relevant_actions
            
            return interactive_elements[:20]  # Limit to top 20 actions
            
        except Exception as e:
            logger.error("Action extraction failed", url=url, error=str(e))
            return []
    
    async def _ai_analyze_content(self, url: str, title: str, content: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use AI to analyze page content comprehensively"""
        if not self.ai_client:
            return {"summary": "AI analysis unavailable", "entities": [], "sentiment": "neutral"}
        
        analysis_prompt = f"""Analyze this webpage content and provide comprehensive insights:

URL: {url}
Title: {title}
Content: {content[:3000]}...
User Context: {json.dumps(user_context or {}, indent=2)}

Provide detailed analysis in JSON format:
{{
    "summary": "2-3 sentence summary of the main content",
    "entities": ["person", "company", "product", "concept"],
    "sentiment": "positive|negative|neutral",
    "key_topics": ["topic1", "topic2"],
    "content_quality": "high|medium|low",
    "credibility_indicators": ["indicator1", "indicator2"],
    "user_value": "high|medium|low",
    "next_steps": ["suggested action 1", "suggested action 2"],
    "related_queries": ["related search 1", "related search 2"]
}}

Focus on:
1. What is this page about?
2. What are the key entities and concepts?
3. What value does it provide to users?
4. What actions might users want to take?
5. How credible and trustworthy is the content?
"""

        try:
            response = await self.ai_client.chat(analysis_prompt, max_tokens=600)
            content = response.get("content", "")
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                return json.loads(content[json_start:json_end])
            else:
                return json.loads(content)
                
        except Exception as e:
            logger.error("AI content analysis failed", error=str(e))
            return {"summary": "Analysis failed", "entities": [], "sentiment": "neutral"}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        return "Untitled Page"
    
    async def _classify_content_type(self, soup: BeautifulSoup, html: str) -> str:
        """Classify the type of content on the page"""
        html_lower = html.lower()
        
        # Score each content type
        scores = {}
        for content_type, patterns in self.content_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, html_lower))
            scores[content_type] = score
        
        # Return the highest scoring type
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "general"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from the page"""
        # Try to find main content areas
        content_selectors = [
            'main', 'article', '[role="main"]', 
            '.content', '#content', '.main-content',
            '.post', '.entry', '.article'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True, separator=' ')
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            # Remove script and style elements
            for script in body(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            return body.get_text(strip=True, separator=' ')
        
        return soup.get_text(strip=True, separator=' ')
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data from the page"""
        structured_data = {}
        
        # JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data['json_ld'] = data
                break
            except:
                continue
        
        # Meta tags
        meta_data = {}
        for meta in soup.find_all('meta'):
            if meta.get('property'):
                meta_data[meta['property']] = meta.get('content', '')
            elif meta.get('name'):
                meta_data[meta['name']] = meta.get('content', '')
        
        if meta_data:
            structured_data['meta'] = meta_data
        
        return structured_data
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        word_count = len(content.split())
        # Average reading speed: 200 words per minute
        return max(1, round(word_count / 200))
    
    async def _calculate_complexity(self, content: str) -> float:
        """Calculate content complexity score (0-1)"""
        if not content:
            return 0.0
        
        # Simple heuristics for complexity
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Complexity based on sentence length and vocabulary
        complexity = min(1.0, avg_sentence_length / 25)  # 25 words = high complexity
        
        return complexity
    
    async def _assess_trustworthiness(self, url: str, soup: BeautifulSoup, ai_analysis: Dict[str, Any]) -> float:
        """Assess trustworthiness of the content"""
        score = 0.5  # Start neutral
        
        # Check domain reputation (basic heuristics)
        domain = urllib.parse.urlparse(url).netloc.lower()
        
        # Known trustworthy domains
        trustworthy_domains = [
            'wikipedia.org', 'edu', 'gov', 'reuters.com', 'bbc.com',
            'nature.com', 'science.org', 'nih.gov'
        ]
        
        if any(trusted in domain for trusted in trustworthy_domains):
            score += 0.3
        
        # Check for author information
        if soup.find(class_=re.compile('author|byline', re.I)):
            score += 0.1
        
        # Check for publication date
        if soup.find('time') or soup.find(class_=re.compile('date|publish', re.I)):
            score += 0.1
        
        # Check AI analysis for credibility indicators
        credibility_indicators = ai_analysis.get('credibility_indicators', [])
        score += min(0.2, len(credibility_indicators) * 0.05)
        
        return min(1.0, score)
    
    async def _assess_privacy(self, soup: BeautifulSoup) -> float:
        """Assess privacy score of the page"""
        score = 1.0  # Start with perfect privacy
        
        # Check for tracking scripts
        tracking_patterns = [
            r'google-analytics', r'googletagmanager', r'facebook\.com/tr',
            r'doubleclick', r'scorecardresearch', r'quantserve'
        ]
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.get('src'):
                script_src = script['src'].lower()
                for pattern in tracking_patterns:
                    if re.search(pattern, script_src):
                        score -= 0.15
        
        # Check for third-party resources
        external_resources = 0
        for element in soup.find_all(['script', 'link', 'img']):
            src = element.get('src') or element.get('href')
            if src and src.startswith(('http://', 'https://')):
                external_resources += 1
        
        if external_resources > 10:
            score -= 0.2
        
        return max(0.0, score)
    
    async def _generate_recommendations(self, url: str, ai_analysis: Dict[str, Any], user_context: Dict[str, Any] = None) -> List[str]:
        """Generate AI-powered recommendations for the user"""
        if not self.ai_client:
            return ["Explore the main content", "Check related links"]
        
        try:
            rec_prompt = f"""Based on this webpage analysis, generate 3-5 helpful recommendations for the user:

URL: {url}
Analysis: {json.dumps(ai_analysis, indent=2)}
User Context: {json.dumps(user_context or {}, indent=2)}

Generate specific, actionable recommendations like:
- "Read the section about X for detailed information on Y"
- "Try the interactive tool to calculate Z"
- "Check out the related article about A"
- "Save this page for reference when working on B"

Focus on helping the user get maximum value from this page.
Return as JSON array: ["recommendation 1", "recommendation 2", ...]
"""

            response = await self.ai_client.chat(rec_prompt, max_tokens=300)
            content = response.get("content", "")
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                recommendations = json.loads(content[json_start:json_end])
            else:
                recommendations = json.loads(content)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception:
            return ["Explore the main content", "Look for actionable elements", "Check related information"]
    
    def _find_actionable_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find elements the user can interact with"""
        actionable = []
        
        # Buttons
        for button in soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]']):
            text = self._get_element_text(button)
            if text:
                actionable.append({
                    "type": "button",
                    "text": text,
                    "action": "click"
                })
        
        # Forms
        for form in soup.find_all('form'):
            inputs = form.find_all(['input', 'textarea', 'select'])
            if inputs:
                actionable.append({
                    "type": "form",
                    "fields": len(inputs),
                    "action": "fill_form"
                })
        
        # Important links
        for link in soup.find_all('a', href=True):
            text = self._get_element_text(link)
            if text and len(text) > 3 and len(text) < 100:
                actionable.append({
                    "type": "link",
                    "text": text,
                    "action": "navigate"
                })
        
        return actionable[:15]  # Limit to top 15 actionable elements
    
    def _get_element_text(self, element) -> str:
        """Get clean text from an element"""
        if element.get('value'):
            return element['value'].strip()
        return element.get_text(strip=True)
    
    def _update_user_interests(self, entities: List[str]):
        """Update user interests based on page entities"""
        for entity in entities:
            if len(entity) > 2:  # Only meaningful entities
                self.user_interests.add(entity.lower())
        
        # Keep only recent interests (limit to 100)
        if len(self.user_interests) > 100:
            # In a real implementation, you'd use a more sophisticated strategy
            # For now, just keep the set size manageable
            self.user_interests = set(list(self.user_interests)[-100:])
    
    def _basic_search_analysis(self, query: str) -> SearchContext:
        """Basic search analysis when AI is not available"""
        # Simple keyword extraction
        entities = [word for word in query.split() if len(word) > 3]
        
        # Basic intent classification
        intent = "information"
        if any(word in query.lower() for word in ["buy", "purchase", "order"]):
            intent = "transaction"
        elif any(word in query.lower() for word in ["near me", "location", "address"]):
            intent = "local"
        elif any(word in query.lower() for word in ["how to", "tutorial", "guide"]):
            intent = "information"
        
        return SearchContext(
            query=query,
            intent=intent,
            entities=entities,
            related_topics=[],
            suggested_refinements=[],
            expected_result_types=["articles"]
        )
    
    def _basic_suggestions(self, partial_query: str) -> List[str]:
        """Basic search suggestions when AI is not available"""
        # Simple completion suggestions
        suggestions = [
            f"{partial_query} tutorial",
            f"{partial_query} guide",
            f"{partial_query} examples",
            f"{partial_query} best practices",
            f"how to {partial_query}",
            f"{partial_query} tips",
        ]
        return [s for s in suggestions if len(s) > len(partial_query)]
    
    async def _analyze_action_relevance(self, actions: List[Dict[str, Any]], user_goal: str, url: str) -> List[Dict[str, Any]]:
        """Use AI to analyze which actions are most relevant to user's goal"""
        if not self.ai_client or not actions:
            return actions
        
        try:
            relevance_prompt = f"""Analyze which page actions are most relevant to the user's goal:

User Goal: "{user_goal}"
Page URL: {url}
Available Actions: {json.dumps(actions[:20], indent=2)}

Rank the actions by relevance to the user's goal and return the top 10 most relevant ones.
Add a relevance score (0-1) and brief explanation for each.

Return as JSON array:
[
    {{
        "type": "button",
        "text": "Submit Application",
        "action": "click",
        "relevance_score": 0.95,
        "explanation": "This directly achieves the user's goal"
    }}
]
"""

            response = await self.ai_client.chat(relevance_prompt, max_tokens=800)
            content = response.get("content", "")
            
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                relevant_actions = json.loads(content[json_start:json_end])
            else:
                relevant_actions = json.loads(content)
            
            return relevant_actions[:10]
            
        except Exception as e:
            logger.error("Action relevance analysis failed", error=str(e))
            return actions[:10]

# Factory function for easy integration
async def create_intelligent_browsing(ai_client):
    """Factory function to create intelligent browsing system"""
    return IntelligentBrowsingSystem(ai_client)