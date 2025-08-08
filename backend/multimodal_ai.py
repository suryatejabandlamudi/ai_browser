#!/usr/bin/env python3
"""
Multi-Modal AI System for AI Browser
Image analysis, OCR, video understanding, and document processing with local AI
"""

import asyncio
import json
import base64
import io
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import structlog
from PIL import Image, ImageEnhance
import numpy as np

logger = structlog.get_logger(__name__)

@dataclass
class ImageAnalysis:
    """Result of image analysis"""
    url: str
    description: str
    objects_detected: List[str]
    text_content: str  # OCR result
    colors: List[str]
    style: str  # "photograph", "illustration", "screenshot", "diagram"
    quality: str  # "high", "medium", "low"
    accessibility_text: str
    actionable_elements: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float

@dataclass
class VideoAnalysis:
    """Result of video analysis"""
    url: str
    description: str
    duration: float
    key_frames: List[Dict[str, Any]]
    audio_transcript: str
    topics: List[str]
    video_type: str  # "educational", "entertainment", "news", "tutorial"
    accessibility_description: str
    confidence_score: float

@dataclass
class DocumentAnalysis:
    """Result of document analysis"""
    url: str
    document_type: str  # "pdf", "doc", "spreadsheet", "presentation"
    title: str
    summary: str
    key_points: List[str]
    structure: Dict[str, Any]
    text_content: str
    metadata: Dict[str, Any]

class MultiModalAI:
    """Multi-modal AI system for comprehensive media understanding"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.ocr_engines = {}
        self.image_cache = {}
        self.video_cache = {}
        
        # Initialize OCR engines
        self._init_ocr_engines()
        
        logger.info("Multi-modal AI system initialized")
    
    def _init_ocr_engines(self):
        """Initialize available OCR engines"""
        # Try to import OCR libraries
        ocr_engines = {}
        
        # Tesseract OCR
        try:
            import pytesseract
            ocr_engines['tesseract'] = pytesseract
            logger.info("Tesseract OCR available")
        except ImportError:
            logger.warning("Tesseract OCR not available - install pytesseract")
        
        # EasyOCR
        try:
            import easyocr
            ocr_engines['easyocr'] = easyocr.Reader(['en'])
            logger.info("EasyOCR available")
        except ImportError:
            logger.warning("EasyOCR not available - install easyocr")
        
        # PaddleOCR
        try:
            from paddleocr import PaddleOCR
            ocr_engines['paddleocr'] = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR available")
        except ImportError:
            logger.warning("PaddleOCR not available - install paddlepaddle paddleocr")
        
        self.ocr_engines = ocr_engines
        
        if not ocr_engines:
            logger.warning("No OCR engines available - text extraction will be limited")
    
    async def analyze_image(self, image_url: str, image_data: bytes = None, 
                           user_context: Dict[str, Any] = None) -> ImageAnalysis:
        """Comprehensive image analysis with AI and OCR"""
        start_time = datetime.now()
        
        try:
            logger.info("Starting image analysis", url=image_url)
            
            # Load and preprocess image
            if image_data:
                image = Image.open(io.BytesIO(image_data))
            else:
                # In a real implementation, you'd fetch the image from URL
                logger.warning("Image data not provided, analysis limited")
                return self._create_empty_image_analysis(image_url, start_time)
            
            # Basic image properties
            width, height = image.size
            format_info = image.format or "unknown"
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract dominant colors
            colors = self._extract_dominant_colors(image)
            
            # Perform OCR
            text_content = await self._extract_text_from_image(image)
            
            # Classify image style and quality
            style = self._classify_image_style(image)
            quality = self._assess_image_quality(image)
            
            # AI-powered image description
            ai_description = await self._ai_describe_image(image, image_url, user_context)
            
            # Detect actionable elements (buttons, links in screenshots)
            actionable_elements = await self._detect_actionable_elements(image, text_content)
            
            # Generate accessibility description
            accessibility_text = await self._generate_accessibility_description(
                ai_description, text_content, actionable_elements
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            analysis = ImageAnalysis(
                url=image_url,
                description=ai_description.get("description", "Image analysis unavailable"),
                objects_detected=ai_description.get("objects", []),
                text_content=text_content,
                colors=colors,
                style=style,
                quality=quality,
                accessibility_text=accessibility_text,
                actionable_elements=actionable_elements,
                confidence_score=ai_description.get("confidence", 0.7),
                processing_time=processing_time
            )
            
            # Cache result
            self.image_cache[image_url] = analysis
            
            logger.info("Image analysis completed", 
                       url=image_url, 
                       processing_time=processing_time,
                       text_length=len(text_content))
            
            return analysis
            
        except Exception as e:
            logger.error("Image analysis failed", url=image_url, error=str(e))
            return self._create_empty_image_analysis(image_url, start_time)
    
    async def analyze_video(self, video_url: str, video_data: bytes = None) -> VideoAnalysis:
        """Analyze video content (requires additional video processing libraries)"""
        try:
            logger.info("Starting video analysis", url=video_url)
            
            # Basic video analysis - in production you'd use opencv-python, moviepy, etc.
            analysis = VideoAnalysis(
                url=video_url,
                description="Video analysis requires additional setup",
                duration=0.0,
                key_frames=[],
                audio_transcript="",
                topics=[],
                video_type="unknown",
                accessibility_description="Video analysis unavailable",
                confidence_score=0.0
            )
            
            logger.info("Video analysis completed (basic)", url=video_url)
            return analysis
            
        except Exception as e:
            logger.error("Video analysis failed", url=video_url, error=str(e))
            return VideoAnalysis(
                url=video_url,
                description="Video analysis failed",
                duration=0.0,
                key_frames=[],
                audio_transcript="",
                topics=[],
                video_type="error",
                accessibility_description="Video analysis failed",
                confidence_score=0.0
            )
    
    async def analyze_document(self, doc_url: str, doc_data: bytes = None) -> DocumentAnalysis:
        """Analyze document content (PDF, DOC, etc.)"""
        try:
            logger.info("Starting document analysis", url=doc_url)
            
            # Basic document analysis - in production you'd use PyPDF2, python-docx, etc.
            analysis = DocumentAnalysis(
                url=doc_url,
                document_type="unknown",
                title="Document analysis requires additional setup",
                summary="",
                key_points=[],
                structure={},
                text_content="",
                metadata={}
            )
            
            logger.info("Document analysis completed (basic)", url=doc_url)
            return analysis
            
        except Exception as e:
            logger.error("Document analysis failed", url=doc_url, error=str(e))
            return DocumentAnalysis(
                url=doc_url,
                document_type="error",
                title="Document analysis failed",
                summary="",
                key_points=[],
                structure={},
                text_content="",
                metadata={}
            )
    
    async def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using available OCR engines"""
        if not self.ocr_engines:
            return ""
        
        text_results = []
        
        # Try Tesseract first (usually most accurate for clean text)
        if 'tesseract' in self.ocr_engines:
            try:
                import pytesseract
                # Enhance image for better OCR
                enhanced_image = ImageEnhance.Contrast(image).enhance(2.0)
                enhanced_image = ImageEnhance.Sharpness(enhanced_image).enhance(2.0)
                
                text = pytesseract.image_to_string(enhanced_image, lang='eng')
                if text.strip():
                    text_results.append(text.strip())
            except Exception as e:
                logger.warning("Tesseract OCR failed", error=str(e))
        
        # Try EasyOCR
        if 'easyocr' in self.ocr_engines and not text_results:
            try:
                reader = self.ocr_engines['easyocr']
                # Convert PIL image to numpy array
                img_array = np.array(image)
                results = reader.readtext(img_array)
                
                extracted_text = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Only include confident results
                        extracted_text.append(text)
                
                if extracted_text:
                    text_results.append(' '.join(extracted_text))
            except Exception as e:
                logger.warning("EasyOCR failed", error=str(e))
        
        # Try PaddleOCR
        if 'paddleocr' in self.ocr_engines and not text_results:
            try:
                ocr = self.ocr_engines['paddleocr']
                img_array = np.array(image)
                results = ocr.ocr(img_array, cls=True)
                
                extracted_text = []
                for line in results:
                    if line:
                        for word_info in line:
                            text = word_info[1][0]
                            confidence = word_info[1][1]
                            if confidence > 0.5:
                                extracted_text.append(text)
                
                if extracted_text:
                    text_results.append(' '.join(extracted_text))
            except Exception as e:
                logger.warning("PaddleOCR failed", error=str(e))
        
        # Return the best result
        if text_results:
            # Choose the longest text (usually most complete)
            return max(text_results, key=len)
        
        return ""
    
    def _extract_dominant_colors(self, image: Image.Image) -> List[str]:
        """Extract dominant colors from image"""
        try:
            # Resize image for faster processing
            small_image = image.resize((50, 50))
            
            # Get color palette
            colors = small_image.getcolors(maxcolors=256)
            if not colors:
                return []
            
            # Sort by frequency and get top colors
            colors.sort(key=lambda x: x[0], reverse=True)
            
            dominant_colors = []
            for count, color in colors[:5]:  # Top 5 colors
                if isinstance(color, tuple) and len(color) >= 3:
                    # Convert RGB to hex
                    hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
                    dominant_colors.append(hex_color)
            
            return dominant_colors
            
        except Exception as e:
            logger.warning("Color extraction failed", error=str(e))
            return []
    
    def _classify_image_style(self, image: Image.Image) -> str:
        """Classify image style using basic heuristics"""
        try:
            width, height = image.size
            
            # Very simple heuristics - in production use ML model
            aspect_ratio = width / height
            
            # Screenshot-like (wide aspect ratio, likely UI elements)
            if aspect_ratio > 2.0:
                return "screenshot"
            
            # Square or near-square (likely social media, icons)
            elif 0.8 <= aspect_ratio <= 1.2:
                return "social"
            
            # Standard photo ratios
            elif 1.3 <= aspect_ratio <= 1.8:
                return "photograph"
            
            return "illustration"
            
        except Exception:
            return "unknown"
    
    def _assess_image_quality(self, image: Image.Image) -> str:
        """Assess image quality using basic metrics"""
        try:
            width, height = image.size
            total_pixels = width * height
            
            # Simple quality assessment based on resolution
            if total_pixels > 2_000_000:  # > 2MP
                return "high"
            elif total_pixels > 500_000:  # > 0.5MP
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "unknown"
    
    async def _ai_describe_image(self, image: Image.Image, image_url: str, 
                                user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use AI to describe image content"""
        if not self.ai_client:
            return {"description": "AI description unavailable", "objects": [], "confidence": 0.5}
        
        try:
            # Convert image to base64 for AI analysis
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Simple text-based analysis (in production, use vision models)
            analysis_prompt = f"""Analyze this image and provide detailed description:

Image URL: {image_url}
Image Size: {image.size[0]}x{image.size[1]}
User Context: {json.dumps(user_context or {}, indent=2)}

Provide analysis in JSON format:
{{
    "description": "Detailed description of what's in the image",
    "objects": ["object1", "object2", "object3"],
    "scene_type": "indoor|outdoor|interface|document|artwork",
    "mood": "professional|casual|artistic|technical",
    "purpose": "informational|decorative|functional|marketing",
    "confidence": 0.85,
    "accessibility_notes": "Important details for screen readers"
}}

Focus on:
1. What are the main subjects/objects?
2. What is the overall scene or context?
3. Any text or UI elements visible?
4. What would be useful for accessibility?
"""

            response = await self.ai_client.chat(analysis_prompt, max_tokens=500)
            
            content = response.get("content", "")
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                return json.loads(content[json_start:json_end])
            else:
                return json.loads(content)
                
        except Exception as e:
            logger.error("AI image description failed", error=str(e))
            return {
                "description": f"Image at {image_url}",
                "objects": [],
                "confidence": 0.3
            }
    
    async def _detect_actionable_elements(self, image: Image.Image, text_content: str) -> List[Dict[str, Any]]:
        """Detect buttons, links, and other actionable elements in screenshots"""
        actionable_elements = []
        
        # Look for UI-related text in OCR results
        ui_keywords = [
            "click", "button", "submit", "cancel", "ok", "yes", "no",
            "login", "register", "sign up", "download", "upload",
            "next", "previous", "back", "home", "menu", "search"
        ]
        
        if text_content:
            text_lower = text_content.lower()
            for keyword in ui_keywords:
                if keyword in text_lower:
                    actionable_elements.append({
                        "type": "button",
                        "text": keyword,
                        "confidence": 0.7,
                        "detected_method": "ocr"
                    })
        
        # In production, use computer vision to detect actual UI elements
        # This would involve training models or using existing UI detection APIs
        
        return actionable_elements
    
    async def _generate_accessibility_description(self, ai_description: Dict[str, Any], 
                                                text_content: str, 
                                                actionable_elements: List[Dict[str, Any]]) -> str:
        """Generate comprehensive accessibility description"""
        parts = []
        
        # Main description
        main_desc = ai_description.get("description", "")
        if main_desc:
            parts.append(main_desc)
        
        # Text content
        if text_content:
            parts.append(f"Text content: {text_content[:200]}")
        
        # Actionable elements
        if actionable_elements:
            element_texts = [elem.get("text", "") for elem in actionable_elements]
            if element_texts:
                parts.append(f"Interactive elements: {', '.join(element_texts)}")
        
        return ". ".join(parts) if parts else "Image content not accessible"
    
    def _create_empty_image_analysis(self, image_url: str, start_time: datetime) -> ImageAnalysis:
        """Create empty analysis result for failed cases"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ImageAnalysis(
            url=image_url,
            description="Image analysis failed",
            objects_detected=[],
            text_content="",
            colors=[],
            style="unknown",
            quality="unknown",
            accessibility_text="Image not accessible",
            actionable_elements=[],
            confidence_score=0.0,
            processing_time=processing_time
        )
    
    async def analyze_page_media(self, url: str, html_content: str) -> Dict[str, Any]:
        """Analyze all media content on a page"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            media_analysis = {
                "images": [],
                "videos": [],
                "audio": [],
                "documents": [],
                "total_media_elements": 0
            }
            
            # Find all images
            images = soup.find_all('img', src=True)
            for img in images[:10]:  # Limit to first 10 images
                img_src = img.get('src')
                if img_src:
                    # In production, fetch and analyze each image
                    analysis = ImageAnalysis(
                        url=img_src,
                        description=img.get('alt', 'Image without alt text'),
                        objects_detected=[],
                        text_content="",
                        colors=[],
                        style="unknown",
                        quality="unknown",
                        accessibility_text=img.get('alt', 'No alt text provided'),
                        actionable_elements=[],
                        confidence_score=0.5,
                        processing_time=0.0
                    )
                    media_analysis["images"].append(analysis)
            
            # Find all videos
            videos = soup.find_all(['video', 'iframe'])
            for video in videos:
                video_src = video.get('src') or video.get('data-src')
                if video_src:
                    media_analysis["videos"].append({
                        "url": video_src,
                        "type": video.name
                    })
            
            # Find all audio
            audio_elements = soup.find_all('audio', src=True)
            for audio in audio_elements:
                media_analysis["audio"].append({
                    "url": audio.get('src'),
                    "type": "audio"
                })
            
            # Find document links
            doc_links = soup.find_all('a', href=True)
            doc_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']
            for link in doc_links:
                href = link.get('href', '').lower()
                if any(ext in href for ext in doc_extensions):
                    media_analysis["documents"].append({
                        "url": link.get('href'),
                        "text": link.get_text(strip=True),
                        "type": "document"
                    })
            
            media_analysis["total_media_elements"] = (
                len(media_analysis["images"]) + 
                len(media_analysis["videos"]) + 
                len(media_analysis["audio"]) + 
                len(media_analysis["documents"])
            )
            
            logger.info("Page media analysis completed", 
                       url=url, 
                       total_elements=media_analysis["total_media_elements"])
            
            return media_analysis
            
        except Exception as e:
            logger.error("Page media analysis failed", url=url, error=str(e))
            return {
                "images": [],
                "videos": [],
                "audio": [],
                "documents": [],
                "total_media_elements": 0,
                "error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get available multi-modal capabilities"""
        return {
            "image_analysis": True,
            "ocr_tesseract": 'tesseract' in self.ocr_engines,
            "ocr_easyocr": 'easyocr' in self.ocr_engines,
            "ocr_paddleocr": 'paddleocr' in self.ocr_engines,
            "video_analysis": False,  # Requires additional setup
            "audio_analysis": False,  # Requires additional setup
            "document_analysis": False,  # Requires additional setup
            "ai_description": self.ai_client is not None
        }

# Factory function for easy integration
async def create_multimodal_ai(ai_client=None):
    """Factory function to create multi-modal AI system"""
    return MultiModalAI(ai_client)