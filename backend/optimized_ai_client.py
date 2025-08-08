"""
Optimized AI Client for High Performance Local LLM
Addresses critical 10-15s response time → 1-3s target
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import httpx
import logging
from collections import deque
import hashlib
import pickle
import sqlite3
from pathlib import Path

@dataclass
class CachedResponse:
    response: str
    timestamp: float
    context_hash: str
    usage_count: int = 0

class ModelPool:
    """Pool of pre-loaded model instances for parallel processing"""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.available_models = deque()
        self.busy_models = set()
        self.lock = threading.Lock()
        self.initialized = False
    
    async def initialize_pool(self):
        """Pre-load model instances"""
        if self.initialized:
            return
            
        logging.info(f"Initializing model pool with {self.pool_size} instances")
        
        # Initialize multiple Ollama connections
        for i in range(self.pool_size):
            model_instance = {
                'id': i,
                'client': httpx.AsyncClient(
                    base_url="http://localhost:11434",
                    timeout=httpx.Timeout(30.0)
                ),
                'warm': False
            }
            self.available_models.append(model_instance)
        
        # Warm up models in parallel
        await self._warm_up_models()
        self.initialized = True
    
    async def _warm_up_models(self):
        """Pre-warm all model instances"""
        warm_up_tasks = []
        for model in list(self.available_models):
            warm_up_tasks.append(self._warm_up_single_model(model))
        
        await asyncio.gather(*warm_up_tasks, return_exceptions=True)
    
    async def _warm_up_single_model(self, model):
        """Warm up a single model instance"""
        try:
            warm_up_request = {
                "model": "gpt-oss:20b",
                "prompt": "Hello",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 5
                }
            }
            
            start_time = time.time()
            response = await model['client'].post(
                "/api/generate",
                json=warm_up_request
            )
            
            if response.status_code == 200:
                model['warm'] = True
                warm_time = time.time() - start_time
                logging.info(f"Model {model['id']} warmed up in {warm_time:.2f}s")
            
        except Exception as e:
            logging.error(f"Failed to warm up model {model['id']}: {e}")
    
    async def get_model(self):
        """Get an available model instance"""
        with self.lock:
            if not self.available_models:
                return None
            
            model = self.available_models.popleft()
            self.busy_models.add(model['id'])
            return model
    
    def return_model(self, model):
        """Return model to pool"""
        with self.lock:
            if model['id'] in self.busy_models:
                self.busy_models.remove(model['id'])
                self.available_models.append(model)

class IntelligentCache:
    """Smart caching system for AI responses"""
    
    def __init__(self, cache_file: str = "ai_cache.db", max_size: int = 1000):
        self.cache_file = cache_file
        self.max_size = max_size
        self.memory_cache: Dict[str, CachedResponse] = {}
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    context_hash TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON response_cache(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage ON response_cache(usage_count)
            """)
    
    def _generate_cache_key(self, prompt: str, context: dict = None) -> str:
        """Generate cache key from prompt and context"""
        context_str = json.dumps(context or {}, sort_keys=True)
        combined = f"{prompt}:{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, prompt: str, context: dict = None, max_age: float = 300) -> Optional[str]:
        """Get cached response if available and fresh"""
        cache_key = self._generate_cache_key(prompt, context)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if time.time() - cached.timestamp < max_age:
                cached.usage_count += 1
                return cached.response
        
        # Check database cache
        try:
            with sqlite3.connect(self.cache_file) as conn:
                cursor = conn.execute(
                    "SELECT response, timestamp, usage_count FROM response_cache WHERE cache_key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    response, timestamp, usage_count = row
                    if time.time() - timestamp < max_age:
                        # Update usage count and load into memory
                        conn.execute(
                            "UPDATE response_cache SET usage_count = usage_count + 1 WHERE cache_key = ?",
                            (cache_key,)
                        )
                        
                        self.memory_cache[cache_key] = CachedResponse(
                            response=response,
                            timestamp=timestamp,
                            context_hash=cache_key,
                            usage_count=usage_count + 1
                        )
                        return response
        except Exception as e:
            logging.error(f"Cache retrieval error: {e}")
        
        return None
    
    def set(self, prompt: str, response: str, context: dict = None):
        """Cache AI response"""
        cache_key = self._generate_cache_key(prompt, context)
        timestamp = time.time()
        
        # Store in memory cache
        self.memory_cache[cache_key] = CachedResponse(
            response=response,
            timestamp=timestamp,
            context_hash=cache_key
        )
        
        # Store in database
        try:
            with sqlite3.connect(self.cache_file) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO response_cache (cache_key, response, timestamp, context_hash, usage_count) VALUES (?, ?, ?, ?, 0)",
                    (cache_key, response, timestamp, cache_key)
                )
        except Exception as e:
            logging.error(f"Cache storage error: {e}")
        
        # Clean up if cache is too large
        if len(self.memory_cache) > self.max_size:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove least recently used items"""
        # Sort by usage count and timestamp
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: (x[1].usage_count, x[1].timestamp)
        )
        
        # Remove 20% of items
        items_to_remove = len(sorted_items) // 5
        for i in range(items_to_remove):
            del self.memory_cache[sorted_items[i][0]]

class CircuitBreaker:
    """Circuit breaker pattern for AI service reliability"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class OptimizedAIClient:
    """High-performance AI client with caching, pooling, and circuit breaker"""
    
    def __init__(self):
        self.model_pool = ModelPool(pool_size=3)
        self.cache = IntelligentCache()
        self.circuit_breaker = CircuitBreaker()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Response streaming
        self.streaming_enabled = True
        self.stream_callbacks = {}
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0,
            'circuit_breaker_trips': 0
        }
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the optimized AI client"""
        if not self.initialized:
            await self.model_pool.initialize_pool()
            self.initialized = True
            logging.info("OptimizedAIClient initialized successfully")
    
    async def generate_response(self, 
                              prompt: str, 
                              context: dict = None, 
                              stream: bool = True,
                              use_cache: bool = True) -> str:
        """Generate AI response with optimization"""
        
        if not self.initialized:
            await self.initialize()
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise Exception("AI service temporarily unavailable (circuit breaker open)")
        
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            # Check cache first
            if use_cache:
                cached_response = self.cache.get(prompt, context)
                if cached_response:
                    self.metrics['cache_hits'] += 1
                    logging.info(f"Cache hit for prompt: {prompt[:50]}...")
                    return cached_response
                else:
                    self.metrics['cache_misses'] += 1
            
            # Get model from pool
            model = await self.model_pool.get_model()
            if not model:
                raise Exception("No available model instances")
            
            try:
                # Prepare optimized request
                request_data = {
                    "model": "gpt-oss:20b",
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200,
                        "num_ctx": 2048,
                        "repeat_penalty": 1.1,
                        "top_k": 40,
                        "top_p": 0.9
                    }
                }
                
                # Add context if provided
                if context:
                    context_str = json.dumps(context)
                    request_data["prompt"] = f"Context: {context_str}\n\nUser: {prompt}\nAssistant:"
                
                # Execute request
                if stream:
                    response = await self._stream_response(model, request_data, prompt, context)
                else:
                    response = await self._single_response(model, request_data)
                
                # Cache successful response
                if use_cache and response:
                    self.cache.set(prompt, response, context)
                
                # Record success
                self.circuit_breaker.record_success()
                
                # Update metrics
                response_time = time.time() - start_time
                self.metrics['average_response_time'] = (
                    (self.metrics['average_response_time'] * (self.metrics['total_requests'] - 1) + response_time) 
                    / self.metrics['total_requests']
                )
                
                logging.info(f"Response generated in {response_time:.2f}s")
                return response
                
            finally:
                # Return model to pool
                self.model_pool.return_model(model)
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            logging.error(f"AI request failed: {e}")
            raise
    
    async def _single_response(self, model, request_data: dict) -> str:
        """Handle single response (non-streaming)"""
        response = await model['client'].post("/api/generate", json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            raise Exception(f"AI service error: {response.status_code}")
    
    async def _stream_response(self, model, request_data: dict, original_prompt: str, context: dict) -> str:
        """Handle streaming response"""
        full_response = ""
        
        async with model['client'].stream("POST", "/api/generate", json=request_data) as response:
            if response.status_code != 200:
                raise Exception(f"AI service error: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk_data = json.loads(line)
                        if 'response' in chunk_data:
                            chunk = chunk_data['response']
                            full_response += chunk
                            
                            # Call streaming callback if registered
                            if original_prompt in self.stream_callbacks:
                                callback = self.stream_callbacks[original_prompt]
                                callback(chunk, full_response)
                        
                        if chunk_data.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
        
        return full_response.strip()
    
    def register_stream_callback(self, prompt: str, callback):
        """Register callback for streaming responses"""
        self.stream_callbacks[prompt] = callback
    
    def unregister_stream_callback(self, prompt: str):
        """Unregister streaming callback"""
        if prompt in self.stream_callbacks:
            del self.stream_callbacks[prompt]
    
    def get_metrics(self) -> dict:
        """Get performance metrics"""
        return {
            **self.metrics,
            'cache_hit_rate': (
                self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
            ) * 100,
            'circuit_breaker_state': self.circuit_breaker.state
        }
    
    async def health_check(self) -> dict:
        """Perform health check"""
        try:
            start_time = time.time()
            response = await self.generate_response("Health check", use_cache=False)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'model_pool_size': len(self.model_pool.available_models),
                'cache_size': len(self.cache.memory_cache),
                'circuit_breaker_state': self.circuit_breaker.state
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }