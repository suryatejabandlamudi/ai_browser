"""
Extraction Tools for AI Browser
Advanced content analysis, data mining, and information extraction.
Designed to compete with Perplexity Comet's content understanding capabilities.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union, Literal
import asyncio
import structlog
import json
import re
from datetime import datetime
import hashlib

from .base import AIBrowserTool, ToolCategory, ToolResult, BrowserContext

logger = structlog.get_logger(__name__)

# Input Schemas

class ExtractContentInput(BaseModel):
    """Input for content extraction"""
    extraction_type: Literal["summary", "key_points", "full_text", "structured", "metadata"] = Field(description="Type of extraction to perform")
    target_selector: Optional[str] = Field(None, description="CSS selector for specific content area")
    max_length: int = Field(default=5000, description="Maximum length of extracted content")
    include_links: bool = Field(default=True, description="Include links in extraction")
    include_images: bool = Field(default=False, description="Include image information")
    filter_noise: bool = Field(default=True, description="Remove navigation, ads, and boilerplate content")

class AnalyzePageInput(BaseModel):
    """Input for comprehensive page analysis"""
    analysis_depth: Literal["basic", "detailed", "comprehensive"] = Field(description="Depth of analysis")
    focus_areas: List[str] = Field(default=[], description="Specific areas to focus analysis on")
    extract_contact_info: bool = Field(default=False, description="Extract contact information")
    extract_pricing: bool = Field(default=False, description="Extract pricing information")
    analyze_sentiment: bool = Field(default=False, description="Analyze content sentiment")
    detect_language: bool = Field(default=True, description="Detect content language")

class FindElementsInput(BaseModel):
    """Input for intelligent element finding"""
    description: str = Field(description="Natural language description of elements to find")
    element_types: List[str] = Field(default=[], description="Specific element types to look for (button, link, input, etc.)")
    max_results: int = Field(default=10, description="Maximum number of elements to return")
    confidence_threshold: float = Field(default=0.6, description="Minimum confidence for element matches")
    include_hidden: bool = Field(default=False, description="Include hidden elements")

class ExtractDataInput(BaseModel):
    """Input for structured data extraction"""
    data_type: Literal["table", "list", "form", "article", "product", "contact", "event"] = Field(description="Type of data to extract")
    schema_hint: Optional[Dict[str, str]] = Field(None, description="Expected data schema")
    target_area: Optional[str] = Field(None, description="CSS selector for target area")
    format_output: Literal["json", "csv", "markdown", "plain"] = Field(default="json", description="Output format")

class MonitorChangesInput(BaseModel):
    """Input for page change monitoring"""
    watch_selector: Optional[str] = Field(None, description="Specific element to watch")
    watch_type: Literal["content", "attributes", "structure", "all"] = Field(default="content", description="Type of changes to monitor")
    comparison_baseline: Optional[str] = Field(None, description="Baseline content for comparison")
    sensitivity: Literal["low", "medium", "high"] = Field(default="medium", description="Change detection sensitivity")

# Tool Implementations

class ExtractContentTool(AIBrowserTool[ExtractContentInput]):
    """
    Advanced content extraction tool.
    Superior to basic scraping - AI-powered content understanding.
    """
    
    def __init__(self):
        super().__init__(
            name="extract_content",
            description="Extract and analyze page content with AI-powered understanding",
            category=ToolCategory.EXTRACTION,
            input_schema=ExtractContentInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: ExtractContentInput, context: BrowserContext) -> ToolResult:
        """Execute intelligent content extraction"""
        
        try:
            if not context.page_content:
                return ToolResult(
                    success=False,
                    message="No page content available for extraction",
                    error="Browser context missing page content"
                )
            
            # Process content based on extraction type
            if params.extraction_type == "summary":
                extracted_content = await self._extract_summary(params, context)
            elif params.extraction_type == "key_points":
                extracted_content = await self._extract_key_points(params, context)
            elif params.extraction_type == "structured":
                extracted_content = await self._extract_structured(params, context)
            elif params.extraction_type == "metadata":
                extracted_content = await self._extract_metadata(params, context)
            else:  # full_text
                extracted_content = await self._extract_full_text(params, context)
            
            # Apply content filtering and processing
            if params.filter_noise:
                extracted_content = self._filter_noise(extracted_content)
            
            # Truncate if needed
            if len(str(extracted_content)) > params.max_length:
                if isinstance(extracted_content, dict):
                    extracted_content["_truncated"] = True
                    extracted_content["_original_length"] = len(str(extracted_content))
                else:
                    extracted_content = str(extracted_content)[:params.max_length] + "..."
            
            return ToolResult(
                success=True,
                message=f"Successfully extracted {params.extraction_type} content ({len(str(extracted_content))} chars)",
                data={
                    "extraction_type": params.extraction_type,
                    "content": extracted_content,
                    "content_length": len(str(extracted_content)),
                    "page_url": context.current_url,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "filtered": params.filter_noise
                }
            )
            
        except Exception as e:
            logger.error(f"Content extraction failed", error=str(e))
            return ToolResult(
                success=False,
                message="Content extraction failed",
                error=str(e)
            )
    
    async def _extract_summary(self, params: ExtractContentInput, context: BrowserContext) -> str:
        """Extract intelligent summary of page content"""
        # In real implementation, would use AI to generate summary
        content = context.page_content
        
        # Mock AI summarization
        await asyncio.sleep(0.5)  # Simulate AI processing
        
        # Extract first few paragraphs as mock summary
        sentences = content.split('. ')[:5]
        summary = '. '.join(sentences) + '.'
        
        return f"AI Summary: {summary}"
    
    async def _extract_key_points(self, params: ExtractContentInput, context: BrowserContext) -> List[str]:
        """Extract key points from content"""
        await asyncio.sleep(0.3)  # Simulate AI processing
        
        # Mock key point extraction
        content = context.page_content.lower()
        key_points = []
        
        # Look for list items and headings
        if "important" in content:
            key_points.append("Contains important information")
        if "price" in content or "$" in content:
            key_points.append("Includes pricing information")
        if "contact" in content or "email" in content:
            key_points.append("Contains contact details")
        if "form" in content:
            key_points.append("Has interactive forms")
        
        if not key_points:
            key_points.append("General informational content")
        
        return key_points
    
    async def _extract_structured(self, params: ExtractContentInput, context: BrowserContext) -> Dict[str, Any]:
        """Extract structured data from content"""
        await asyncio.sleep(0.4)  # Simulate processing
        
        structured_data = {
            "title": context.page_title or "Untitled",
            "url": context.current_url,
            "content_type": self._detect_content_type(context.page_content),
            "main_content": context.page_content[:1000] if context.page_content else "",
            "word_count": len(context.page_content.split()) if context.page_content else 0,
            "extracted_at": datetime.now().isoformat()
        }
        
        # Add interactive elements if available
        if context.interactive_elements:
            structured_data["interactive_elements"] = {
                "total": len(context.interactive_elements),
                "types": list(set(elem.get("tag", "") for elem in context.interactive_elements))
            }
        
        return structured_data
    
    async def _extract_metadata(self, params: ExtractContentInput, context: BrowserContext) -> Dict[str, Any]:
        """Extract page metadata"""
        return {
            "page_title": context.page_title,
            "page_url": context.current_url,
            "content_hash": hashlib.md5(context.page_content.encode()).hexdigest() if context.page_content else None,
            "content_length": len(context.page_content) if context.page_content else 0,
            "interactive_element_count": len(context.interactive_elements) if context.interactive_elements else 0,
            "has_accessibility_tree": context.accessibility_tree is not None,
            "extraction_timestamp": datetime.now().isoformat()
        }
    
    async def _extract_full_text(self, params: ExtractContentInput, context: BrowserContext) -> str:
        """Extract clean full text content"""
        if not context.page_content:
            return ""
        
        # Basic text cleaning
        text = context.page_content
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _detect_content_type(self, content: str) -> str:
        """Detect type of content on page"""
        if not content:
            return "unknown"
        
        content_lower = content.lower()
        
        if "article" in content_lower or "blog" in content_lower:
            return "article"
        elif "product" in content_lower and ("price" in content_lower or "$" in content_lower):
            return "product"
        elif "form" in content_lower or "submit" in content_lower:
            return "form"
        elif "login" in content_lower or "sign in" in content_lower:
            return "authentication"
        elif "about" in content_lower or "company" in content_lower:
            return "about"
        else:
            return "general"
    
    def _filter_noise(self, content) -> Any:
        """Filter out noise and boilerplate content"""
        if isinstance(content, str):
            # Remove common boilerplate patterns
            noise_patterns = [
                r"cookie\s+policy",
                r"privacy\s+policy",
                r"terms\s+of\s+service",
                r"subscribe\s+to\s+newsletter",
                r"follow\s+us\s+on",
                r"advertisement",
                r"sponsored\s+content"
            ]
            
            for pattern in noise_patterns:
                content = re.sub(pattern, "", content, flags=re.IGNORECASE)
            
            # Clean up extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
        
        return content

class AnalyzePageTool(AIBrowserTool[AnalyzePageInput]):
    """
    Comprehensive page analysis tool.
    Competes with Perplexity Comet's deep page understanding.
    """
    
    def __init__(self):
        super().__init__(
            name="analyze_page",
            description="Perform comprehensive analysis of web page content and structure",
            category=ToolCategory.EXTRACTION,
            input_schema=AnalyzePageInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: AnalyzePageInput, context: BrowserContext) -> ToolResult:
        """Execute comprehensive page analysis"""
        
        try:
            analysis_results = {
                "page_info": {
                    "title": context.page_title,
                    "url": context.current_url,
                    "analysis_timestamp": datetime.now().isoformat()
                },
                "content_analysis": {},
                "structure_analysis": {},
                "interaction_analysis": {}
            }
            
            # Content analysis
            if context.page_content:
                analysis_results["content_analysis"] = await self._analyze_content(params, context)
            
            # Structure analysis
            if context.accessibility_tree:
                analysis_results["structure_analysis"] = await self._analyze_structure(params, context)
            
            # Interaction analysis
            if context.interactive_elements:
                analysis_results["interaction_analysis"] = await self._analyze_interactions(params, context)
            
            # Focused analysis areas
            if params.focus_areas:
                analysis_results["focused_analysis"] = await self._analyze_focus_areas(params, context)
            
            # Optional extractions
            if params.extract_contact_info:
                analysis_results["contact_info"] = await self._extract_contact_info(context)
            
            if params.extract_pricing:
                analysis_results["pricing_info"] = await self._extract_pricing_info(context)
            
            return ToolResult(
                success=True,
                message=f"Completed {params.analysis_depth} page analysis",
                data=analysis_results
            )
            
        except Exception as e:
            logger.error(f"Page analysis failed", error=str(e))
            return ToolResult(
                success=False,
                message="Page analysis failed",
                error=str(e)
            )
    
    async def _analyze_content(self, params: AnalyzePageInput, context: BrowserContext) -> Dict[str, Any]:
        """Analyze page content characteristics"""
        await asyncio.sleep(0.3)  # Simulate analysis time
        
        content = context.page_content
        
        analysis = {
            "word_count": len(content.split()) if content else 0,
            "character_count": len(content) if content else 0,
            "estimated_reading_time": len(content.split()) // 200 if content else 0,  # ~200 WPM
            "content_type": self._detect_content_type(content),
            "language": "en",  # Mock language detection
            "complexity": "medium"  # Mock complexity assessment
        }
        
        # Content themes (mock AI analysis)
        themes = []
        if content:
            content_lower = content.lower()
            if "business" in content_lower or "company" in content_lower:
                themes.append("business")
            if "technology" in content_lower or "software" in content_lower:
                themes.append("technology")
            if "product" in content_lower or "service" in content_lower:
                themes.append("commerce")
            if "article" in content_lower or "news" in content_lower:
                themes.append("editorial")
        
        analysis["themes"] = themes or ["general"]
        
        return analysis
    
    async def _analyze_structure(self, params: AnalyzePageInput, context: BrowserContext) -> Dict[str, Any]:
        """Analyze page structure"""
        tree = context.accessibility_tree
        
        return {
            "total_nodes": len(tree.get("nodes", [])) if tree else 0,
            "interactive_nodes": len([n for n in tree.get("nodes", []) if n.get("role") in ["button", "link", "textbox"]]) if tree else 0,
            "heading_structure": self._analyze_headings(tree) if tree else {},
            "form_count": len([n for n in tree.get("nodes", []) if n.get("role") == "form"]) if tree else 0,
            "accessibility_score": self._calculate_accessibility_score(tree) if tree else 0
        }
    
    async def _analyze_interactions(self, params: AnalyzePageInput, context: BrowserContext) -> Dict[str, Any]:
        """Analyze interactive elements"""
        elements = context.interactive_elements or []
        
        element_types = {}
        for elem in elements:
            elem_type = elem.get("tag", "unknown")
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        return {
            "total_interactive": len(elements),
            "element_types": element_types,
            "has_forms": any(elem.get("tag") == "form" for elem in elements),
            "has_buttons": any(elem.get("tag") == "button" for elem in elements),
            "interaction_density": len(elements) / max(len(context.page_content.split()) // 100, 1) if context.page_content else 0
        }
    
    def _detect_content_type(self, content: str) -> str:
        """Detect content type from text analysis"""
        # Same as in ExtractContentTool for consistency
        if not content:
            return "unknown"
        
        content_lower = content.lower()
        
        if "article" in content_lower:
            return "article"
        elif "product" in content_lower and "$" in content_lower:
            return "product"
        elif "form" in content_lower:
            return "form"
        else:
            return "general"

class FindElementsTool(AIBrowserTool[FindElementsInput]):
    """
    AI-powered element finding tool.
    Key advantage over competitors - natural language element detection.
    """
    
    def __init__(self):
        super().__init__(
            name="find_elements",
            description="Find page elements using natural language descriptions and AI matching",
            category=ToolCategory.EXTRACTION,
            input_schema=FindElementsInput,
            requires_browser_context=True,
            can_modify_browser_state=False
        )
    
    async def execute(self, params: FindElementsInput, context: BrowserContext) -> ToolResult:
        """Find elements using AI-powered matching"""
        
        try:
            if not context.accessibility_tree:
                return ToolResult(
                    success=False,
                    message="No accessibility tree available for element finding",
                    error="Browser context missing accessibility data"
                )
            
            # AI-powered element matching
            await asyncio.sleep(0.4)  # Simulate AI processing
            
            matches = await self._find_matching_elements(params, context)
            
            # Filter by confidence threshold
            high_confidence_matches = [
                match for match in matches 
                if match["confidence"] >= params.confidence_threshold
            ]
            
            # Limit results
            final_matches = high_confidence_matches[:params.max_results]
            
            return ToolResult(
                success=len(final_matches) > 0,
                message=f"Found {len(final_matches)} elements matching '{params.description}'",
                data={
                    "description": params.description,
                    "matches": final_matches,
                    "total_candidates": len(matches),
                    "high_confidence_matches": len(high_confidence_matches),
                    "confidence_threshold": params.confidence_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Element finding failed", error=str(e))
            return ToolResult(
                success=False,
                message="Element finding failed",
                error=str(e)
            )
    
    async def _find_matching_elements(self, params: FindElementsInput, context: BrowserContext) -> List[Dict[str, Any]]:
        """Use AI to match elements to description"""
        tree = context.accessibility_tree
        nodes = tree.get("nodes", [])
        
        matches = []
        description_lower = params.description.lower()
        
        for node in nodes:
            confidence = 0.0
            reasons = []
            
            # Text content matching
            node_text = node.get("name", "").lower()
            if node_text and any(word in node_text for word in description_lower.split()):
                confidence += 0.4
                reasons.append("text content match")
            
            # Role matching
            node_role = node.get("role", "")
            if params.element_types and node_role in params.element_types:
                confidence += 0.3
                reasons.append("element type match")
            
            # Semantic matching (mock AI analysis)
            if self._semantic_match(description_lower, node):
                confidence += 0.5
                reasons.append("semantic similarity")
            
            # Priority boost for interactive elements
            if node_role in ["button", "link", "textbox"]:
                confidence += 0.1
                reasons.append("interactive element")
            
            if confidence > 0:
                matches.append({
                    "node": node,
                    "confidence": min(confidence, 1.0),
                    "reasons": reasons,
                    "selectors": node.get("selectors", []),
                    "element_info": {
                        "role": node_role,
                        "name": node.get("name", ""),
                        "description": node.get("description", "")
                    }
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches
    
    def _semantic_match(self, description: str, node: Dict[str, Any]) -> bool:
        """Mock semantic matching between description and node"""
        # In real implementation, would use AI embeddings or semantic analysis
        
        # Simple keyword matching for demo
        description_keywords = set(description.split())
        node_text = (node.get("name", "") + " " + node.get("description", "")).lower()
        node_keywords = set(node_text.split())
        
        overlap = len(description_keywords & node_keywords)
        return overlap > 0

# Register all extraction tools
def register_extraction_tools():
    """Register all extraction tools in the global registry"""
    from .base import tool_registry
    
    tools = [
        ExtractContentTool(),
        AnalyzePageTool(),
        FindElementsTool()
    ]
    
    for tool in tools:
        tool_registry.register(tool)