"""
AI Client for GPT-OSS 20B via Ollama
Handles all interactions with the local language model.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncIterator

import aiohttp
import structlog

logger = structlog.get_logger(__name__)

class AIClient:
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "gpt-oss:20b",
                 timeout: int = 60):  # Increased timeout for better stability
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.session = None
        
        # Simple conversation caching for repeated queries
        self._conversation_cache = {}  
        self.cache_size = 50  # Keep it reasonable
        
        # Model settings
        self.primary_model = model
        self.fallback_model = model
        self.model_warmup_enabled = True
        self.local_models = ["gpt-oss:20b"]
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with optimized settings"""
        if not self.session or self.session.closed:
            # Optimized connection settings for better performance
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool size
                limit_per_host=30,  # Per-host connection limit
                keepalive_timeout=60,  # Keep connections alive longer
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "AI-Browser/1.0"}
            )
        return self.session
    
    def _cache_key(self, message: str, context: Dict[str, Any] = None) -> str:
        """Generate cache key for conversation caching"""
        import hashlib
        context_str = str(context) if context else ""
        return hashlib.md5(f"{message}{context_str}".encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        return self._conversation_cache.get(cache_key)
    
    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache response with size limit"""
        if len(self._conversation_cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._conversation_cache))
            del self._conversation_cache[oldest_key]
        
        self._conversation_cache[cache_key] = {
            **response,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def select_optimal_local_model(self, task_complexity: str = "medium") -> str:
        """Select optimal LOCAL model based on task complexity - privacy-first approach"""
        # Always use local models only - this is our core value proposition
        if task_complexity == "simple" and self._is_local_model_available("llama2:7b"):
            return "llama2:7b"  # Faster for simple tasks
        else:
            return self.primary_model  # GPT-OSS 20B for everything else
    
    def _is_local_model_available(self, model_name: str) -> bool:
        """Check if local model is available via Ollama"""
        return model_name in self.local_models
    
    async def warm_up_model(self, model_name: str = None) -> bool:
        """Pre-load model to reduce first-request latency"""
        if not self.model_warmup_enabled:
            return True
            
        target_model = model_name or self.primary_model
        
        try:
            # Send a minimal request to ensure model is loaded
            session = await self._get_session()
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": target_model,
                "prompt": "Hi",
                "options": {
                    "num_predict": 1,
                    "temperature": 0.1
                }
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Model {target_model} warmed up successfully")
                    return True
                else:
                    logger.warning(f"Model warmup failed for {target_model}")
                    return False
                    
        except Exception as e:
            logger.error(f"Model warmup error for {target_model}: {str(e)}")
            return False
        
    async def test_connection(self) -> bool:
        """Test connection to Ollama and GPT-OSS model"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/chat/completions"
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test connection"}],
                "max_tokens": 10
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("AI model connection test successful", 
                               model=self.model,
                               response_preview=data.get("choices", [{}])[0].get("message", {}).get("content", "")[:50])
                    return True
                else:
                    logger.error("AI model connection test failed", 
                               status=response.status,
                               response=await response.text())
                    return False
                    
        except Exception as e:
            logger.error("AI model connection test error", error=str(e))
            return False
    
    async def chat_stream(self,
                         message: str,
                         context: Optional[Dict[str, Any]] = None,
                         max_tokens: int = 1000) -> AsyncIterator[str]:
        """Stream chat response from AI model"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/chat/completions"
            
            # Build system prompt based on context
            system_prompt = self._build_system_prompt(context)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": True  # Enable streaming
            }
            
            logger.debug("Starting streaming chat request", message_preview=message[:100])
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    async for line in response.content:
                        line_text = line.decode('utf-8').strip()
                        
                        if line_text.startswith('data: '):
                            json_text = line_text[6:]  # Remove 'data: ' prefix
                            
                            if json_text == '[DONE]':
                                break
                                
                            try:
                                chunk = json.loads(json_text)
                                delta_content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                
                                if delta_content:
                                    yield delta_content
                                    
                            except json.JSONDecodeError:
                                continue  # Skip malformed JSON
                else:
                    error_text = await response.text()
                    logger.error("Streaming chat request failed", 
                               status=response.status, 
                               error=error_text)
                    yield f"Error: Request failed with status {response.status}"
                    
        except Exception as e:
            logger.error("Streaming chat error", error=str(e))
            yield f"Error: {str(e)}"

    async def chat(self, 
                   message: str, 
                   context: Optional[Dict[str, Any]] = None,
                   max_tokens: int = 1000) -> Dict[str, Any]:
        """Send chat message to GPT-OSS 20B - our privacy-first local AI"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/chat/completions"
            
            # Build system prompt based on context
            system_prompt = self._build_system_prompt(context)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": self.model,  # Always GPT-OSS 20B
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            logger.debug("Sending chat request to GPT-OSS 20B", message_preview=message[:100])
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    choice = data.get("choices", [{}])[0]
                    
                    return {
                        "content": choice.get("message", {}).get("content", ""),
                        "raw_response": choice.get("message", {}).get("content", ""),
                        "usage": data.get("usage", {}),
                        "model": self.model,
                        "privacy": "100% Local"  # Our key advantage!
                    }
                else:
                    error_text = await response.text()
                    logger.error("GPT-OSS 20B request failed", 
                               status=response.status, 
                               error=error_text)
                    raise Exception(f"GPT-OSS API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("GPT-OSS chat request failed", error=str(e))
            raise
    
    async def stream_chat(self, 
                         message: str, 
                         context: Optional[Dict[str, Any]] = None,
                         max_tokens: int = 1000) -> AsyncIterator[str]:
        """Stream chat response from AI model"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/v1/chat/completions"
            
            system_prompt = self._build_system_prompt(context)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": True
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data: ") and not line_str.endswith("[DONE]"):
                            try:
                                data = json.loads(line_str[6:])  # Remove "data: " prefix
                                choice = data.get("choices", [{}])[0]
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    logger.error("AI stream request failed", 
                               status=response.status, 
                               error=error_text)
                    raise Exception(f"AI streaming error: {response.status}")
                    
        except Exception as e:
            logger.error("Stream chat failed", error=str(e))
            raise
    
    async def summarize(self, 
                       content: str, 
                       url: str,
                       max_tokens: int = 500) -> Dict[str, Any]:
        """Summarize web page content"""
        
        # Truncate content if too long (rough token estimation)
        if len(content) > 8000:  # Rough character limit for context
            content = content[:8000] + "..."
            
        prompt = f"""Please summarize this web page content in a clear, concise way:

URL: {url}
Content:
{content}

Provide:
1. A 2-3 sentence summary
2. Key points as a bulleted list
3. Main topic/purpose of the page

Format your response as JSON with fields: summary, key_points (array), topic"""
        
        response = await self.chat(prompt, max_tokens=max_tokens)
        
        try:
            # Try to parse JSON response
            content_text = response["content"]
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                json_text = content_text[json_start:json_end].strip()
            else:
                json_text = content_text
                
            parsed = json.loads(json_text)
            return {
                "summary": parsed.get("summary", content_text),
                "key_points": parsed.get("key_points", []),
                "topic": parsed.get("topic", "Web Page"),
                "raw_response": content_text
            }
        except json.JSONDecodeError:
            # Fallback to plain text response
            return {
                "summary": response["content"],
                "key_points": [],
                "topic": "Web Page",
                "raw_response": response["content"]
            }
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt based on context"""
        base_prompt = """You are an AI assistant integrated into a web browser. You help users understand web pages, answer questions about content, and suggest browser actions when appropriate.

Key capabilities:
- Summarize and explain web page content
- Answer questions about pages 
- Suggest browser actions (click, type, navigate)
- Help with web tasks and workflows

Guidelines:
- Be concise and helpful
- Use information from the current page when available
- For actions, be specific about elements (e.g., "click the 'Sign In' button")
- Always prioritize user privacy and security"""

        if not context:
            return base_prompt
            
        context_info = []
        
        if context.get("has_page_context"):
            context_info.append(f"Current page: {context.get('page_url', 'Unknown')}")
            if context.get("page_content"):
                content_preview = context["page_content"][:500] + "..." if len(context["page_content"]) > 500 else context["page_content"]
                context_info.append(f"Page content:\n{content_preview}")
        
        if context_info:
            return f"{base_prompt}\n\nCurrent Context:\n" + "\n".join(context_info)
        
        return base_prompt
        
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()