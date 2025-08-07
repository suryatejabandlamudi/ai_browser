"""
Minimal Content Extractor for AI Browser
Basic content extraction without external dependencies.
"""

import re
import asyncio
from typing import Dict, Optional

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

import structlog

logger = structlog.get_logger(__name__)

class ContentExtractor:
    def __init__(self):
        pass
    
    async def extract_main_content(self, html_content: str, page_url: str = "") -> str:
        """Extract main content from HTML"""
        try:
            if BS4_AVAILABLE:
                return await self._extract_with_bs4(html_content)
            else:
                return await self._extract_basic(html_content)
        except Exception as e:
            logger.error("Content extraction failed", error=str(e))
            return html_content[:1000]  # Return first 1000 chars as fallback
    
    async def _extract_with_bs4(self, html_content: str) -> str:
        """Extract using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def _extract_basic(self, html_content: str) -> str:
        """Basic extraction without BeautifulSoup"""
        # Remove script and style tags
        text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def get_page_title(self, html_content: str) -> str:
        """Extract page title"""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return "Untitled Page"