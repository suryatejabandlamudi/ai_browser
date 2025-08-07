"""
Content Extractor for AI Browser
Extracts clean, readable content from web pages using various techniques.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import aiohttp
import structlog
from bs4 import BeautifulSoup, NavigableString
from readability import Document

logger = structlog.get_logger(__name__)

class ContentExtractor:
    def __init__(self):
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_page_content(self, url: str) -> str:
        """Fetch raw HTML content from a URL"""
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    logger.debug("Fetched page content", url=url, size=len(html))
                    return html
                else:
                    logger.error("Failed to fetch page", url=url, status=response.status)
                    raise Exception(f"HTTP {response.status} when fetching {url}")
                    
        except Exception as e:
            logger.error("Error fetching page", url=url, error=str(e))
            raise
    
    async def extract_main_content(self, html: str, url: str) -> str:
        """Extract main content from HTML using Readability"""
        try:
            # Use Readability to extract the main content
            doc = Document(html)
            clean_html = doc.summary()
            
            # Convert to plain text while preserving structure
            soup = BeautifulSoup(clean_html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
                
            # Extract text with some structure preservation
            content = self._extract_structured_text(soup)
            
            # Clean up the text
            content = self._clean_text(content)
            
            logger.debug("Extracted main content", 
                        url=url, 
                        original_size=len(html), 
                        extracted_size=len(content))
            
            return content
            
        except Exception as e:
            logger.error("Content extraction failed", url=url, error=str(e))
            # Fallback to basic text extraction
            return self._fallback_text_extraction(html)
    
    def _extract_structured_text(self, soup: BeautifulSoup) -> str:
        """Extract text while preserving some structure"""
        content_parts = []
        
        # Process different elements with appropriate formatting
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'article', 'section']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Headers
                text = element.get_text(strip=True)
                if text:
                    content_parts.append(f"\n## {text}\n")
            elif element.name in ['p']:
                # Paragraphs
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short paragraphs
                    content_parts.append(f"{text}\n")
            elif element.name in ['div', 'article', 'section']:
                # Containers - only if they don't have child block elements
                if not element.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'article', 'section']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:
                        content_parts.append(f"{text}\n")
        
        # If no structured content found, fallback to all text
        if not content_parts:
            content_parts = [soup.get_text()]
            
        return "".join(content_parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Remove common boilerplate text patterns
        boilerplate_patterns = [
            r'Cookie\s+(?:Policy|Notice|Settings|Preferences).*?(?:\n|$)',
            r'We use cookies.*?(?:\n|$)',
            r'This website uses cookies.*?(?:\n|$)',
            r'By continuing.*?(?:cookies|site).*?(?:\n|$)',
            r'Accept\s+(?:All\s+)?Cookies.*?(?:\n|$)',
            r'Privacy\s+Policy.*?(?:\n|$)',
            r'Terms\s+(?:of\s+)?(?:Service|Use).*?(?:\n|$)',
            r'Subscribe\s+to.*?(?:newsletter|updates).*?(?:\n|$)',
            r'Sign\s+up\s+for.*?(?:\n|$)',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Trim and normalize
        text = text.strip()
        
        return text
    
    def _fallback_text_extraction(self, html: str) -> str:
        """Fallback method for text extraction"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                element.decompose()
            
            # Get text
            text = soup.get_text()
            return self._clean_text(text)
            
        except Exception:
            # Ultimate fallback - just strip HTML tags
            text = re.sub(r'<[^>]+>', '', html)
            return self._clean_text(text)
    
    def extract_page_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """Extract metadata from the page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            metadata = {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'published_date': '',
                'image': '',
                'type': 'webpage'
            }
            
            # Title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
            
            # Meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                property_name = meta.get('property', '').lower()
                content = meta.get('content', '')
                
                if name == 'description' or property_name == 'og:description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif property_name == 'og:image':
                    metadata['image'] = urljoin(url, content)
                elif property_name == 'og:type':
                    metadata['type'] = content
                elif name in ['date', 'pubdate', 'published_time'] or property_name == 'article:published_time':
                    metadata['published_date'] = content
            
            return metadata
            
        except Exception as e:
            logger.error("Metadata extraction failed", url=url, error=str(e))
            return {'url': url, 'domain': urlparse(url).netloc}
    
    def find_interactive_elements(self, html: str) -> List[Dict[str, Any]]:
        """Find interactive elements on the page for automation"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = []
            
            # Buttons
            for button in soup.find_all(['button', 'input']):
                if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
                    continue
                    
                element_info = {
                    'type': 'button',
                    'tag': button.name,
                    'text': button.get_text(strip=True) or button.get('value', ''),
                    'id': button.get('id', ''),
                    'class': ' '.join(button.get('class', [])),
                    'name': button.get('name', ''),
                }
                if element_info['text'] or element_info['id']:
                    elements.append(element_info)
            
            # Links
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                if text:
                    elements.append({
                        'type': 'link',
                        'tag': 'a',
                        'text': text,
                        'href': link['href'],
                        'id': link.get('id', ''),
                        'class': ' '.join(link.get('class', [])),
                    })
            
            # Form inputs
            for input_elem in soup.find_all('input'):
                input_type = input_elem.get('type', 'text').lower()
                if input_type in ['text', 'email', 'password', 'search', 'tel', 'url']:
                    elements.append({
                        'type': 'input',
                        'tag': 'input',
                        'input_type': input_type,
                        'placeholder': input_elem.get('placeholder', ''),
                        'id': input_elem.get('id', ''),
                        'name': input_elem.get('name', ''),
                        'class': ' '.join(input_elem.get('class', [])),
                    })
            
            # Textareas
            for textarea in soup.find_all('textarea'):
                elements.append({
                    'type': 'textarea',
                    'tag': 'textarea',
                    'placeholder': textarea.get('placeholder', ''),
                    'id': textarea.get('id', ''),
                    'name': textarea.get('name', ''),
                    'class': ' '.join(textarea.get('class', [])),
                })
            
            return elements
            
        except Exception as e:
            logger.error("Element extraction failed", error=str(e))
            return []
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()