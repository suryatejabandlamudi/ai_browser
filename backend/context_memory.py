"""
Cross-Tab Context and Memory Management System
Maintains conversation history, user preferences, and context across browser tabs and sessions.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import aiosqlite

import structlog

logger = structlog.get_logger(__name__)

class ContextType(Enum):
    """Types of context data"""
    CONVERSATION = "conversation"
    PAGE_VISIT = "page_visit" 
    USER_ACTION = "user_action"
    FORM_DATA = "form_data"
    SEARCH_QUERY = "search_query"
    WORKFLOW = "workflow"
    PREFERENCE = "preference"
    SESSION = "session"

class MemoryScope(Enum):
    """Scope of memory storage"""
    SESSION = "session"      # Current browser session only
    TAB = "tab"             # Current tab only
    DOMAIN = "domain"       # Current domain/website
    GLOBAL = "global"       # All sessions and tabs

@dataclass
class ContextItem:
    """A single item of contextual information"""
    id: str
    context_type: ContextType
    scope: MemoryScope
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    tab_id: Optional[str] = None
    domain: Optional[str] = None
    timestamp: datetime = None
    expires_at: Optional[datetime] = None
    relevance_score: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class UserPreference:
    """User preference or setting"""
    key: str
    value: Any
    category: str
    description: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CrossTabMemoryManager:
    """Manages memory and context across browser tabs and sessions"""
    
    def __init__(self, db_path: str = "ai_browser_memory.db"):
        self.db_path = db_path
        self.memory_cache: Dict[str, ContextItem] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        self.active_tabs: Set[str] = set()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Context relevance decay rates
        self.decay_rates = {
            ContextType.CONVERSATION: 0.1,    # Conversations stay relevant longer
            ContextType.PAGE_VISIT: 0.3,      # Page visits decay faster
            ContextType.USER_ACTION: 0.2,     # Actions moderately relevant
            ContextType.FORM_DATA: 0.05,      # Form data very persistent
            ContextType.SEARCH_QUERY: 0.25,   # Search queries moderately persistent
            ContextType.WORKFLOW: 0.15,       # Workflows stay relevant
            ContextType.PREFERENCE: 0.0,      # Preferences don't decay
            ContextType.SESSION: 0.5          # Session data decays quickly
        }
    
    async def initialize(self):
        """Initialize the memory system and database"""
        try:
            await self._initialize_database()
            await self._load_user_preferences()
            await self._cleanup_expired_items()
            
            logger.info("Memory manager initialized", 
                       session_id=self.session_id,
                       db_path=self.db_path)
            
        except Exception as e:
            logger.error("Failed to initialize memory manager", error=str(e))
    
    async def _initialize_database(self):
        """Create database tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS context_items (
                    id TEXT PRIMARY KEY,
                    context_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    tab_id TEXT,
                    domain TEXT,
                    timestamp TEXT NOT NULL,
                    expires_at TEXT,
                    relevance_score REAL DEFAULT 1.0
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_type ON context_items(context_type);
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_scope ON context_items(scope);
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_domain ON context_items(domain);
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON context_items(timestamp);
            """)
            
            await db.commit()
    
    async def store_context(self, 
                          context_type: ContextType,
                          content: Dict[str, Any],
                          scope: MemoryScope = MemoryScope.SESSION,
                          tab_id: Optional[str] = None,
                          domain: Optional[str] = None,
                          ttl_hours: Optional[int] = None) -> str:
        """Store a context item in memory"""
        try:
            # Generate unique ID
            item_id = f"{context_type.value}_{datetime.now().timestamp()}"
            
            # Calculate expiration
            expires_at = None
            if ttl_hours:
                expires_at = datetime.now() + timedelta(hours=ttl_hours)
            elif context_type == ContextType.SESSION:
                expires_at = datetime.now() + timedelta(hours=24)  # Sessions expire in 24h
            elif context_type == ContextType.PAGE_VISIT:
                expires_at = datetime.now() + timedelta(hours=48)  # Page visits expire in 48h
            
            # Create context item
            context_item = ContextItem(
                id=item_id,
                context_type=context_type,
                scope=scope,
                content=content,
                metadata={
                    'session_id': self.session_id,
                    'created_by': 'ai_browser',
                    'version': '1.0'
                },
                tab_id=tab_id,
                domain=domain,
                expires_at=expires_at
            )
            
            # Store in cache
            self.memory_cache[item_id] = context_item
            
            # Store in database
            await self._persist_context_item(context_item)
            
            logger.debug("Context stored", 
                        item_id=item_id,
                        context_type=context_type.value,
                        scope=scope.value)
            
            return item_id
            
        except Exception as e:
            logger.error("Failed to store context", error=str(e))
            return ""
    
    async def _persist_context_item(self, item: ContextItem):
        """Persist a context item to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO context_items 
                (id, context_type, scope, content, metadata, tab_id, domain, timestamp, expires_at, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id,
                item.context_type.value,
                item.scope.value,
                json.dumps(item.content),
                json.dumps(item.metadata),
                item.tab_id,
                item.domain,
                item.timestamp.isoformat(),
                item.expires_at.isoformat() if item.expires_at else None,
                item.relevance_score
            ))
            await db.commit()
    
    async def get_relevant_context(self, 
                                 query: str,
                                 context_types: Optional[List[ContextType]] = None,
                                 scope: Optional[MemoryScope] = None,
                                 tab_id: Optional[str] = None,
                                 domain: Optional[str] = None,
                                 limit: int = 20) -> List[ContextItem]:
        """Retrieve relevant context based on query and filters"""
        try:
            # Build SQL query
            sql = """
                SELECT * FROM context_items 
                WHERE (expires_at IS NULL OR expires_at > ?)
            """
            params = [datetime.now().isoformat()]
            
            # Add filters
            if context_types:
                placeholders = ','.join(['?' for _ in context_types])
                sql += f" AND context_type IN ({placeholders})"
                params.extend([ct.value for ct in context_types])
            
            if scope:
                sql += " AND scope = ?"
                params.append(scope.value)
            
            if tab_id:
                sql += " AND (tab_id = ? OR tab_id IS NULL)"
                params.append(tab_id)
            
            if domain:
                sql += " AND (domain = ? OR domain IS NULL)"
                params.append(domain)
            
            # Order by relevance and recency
            sql += " ORDER BY relevance_score DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
            
            # Convert to ContextItem objects
            context_items = []
            for row in rows:
                item = self._row_to_context_item(row)
                if item:
                    # Calculate relevance to query
                    relevance = self._calculate_query_relevance(item, query)
                    item.relevance_score = relevance
                    context_items.append(item)
            
            # Sort by calculated relevance
            context_items.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.debug("Retrieved relevant context", 
                        query_preview=query[:50],
                        items_count=len(context_items))
            
            return context_items[:limit]
            
        except Exception as e:
            logger.error("Failed to get relevant context", error=str(e))
            return []
    
    def _row_to_context_item(self, row) -> Optional[ContextItem]:
        """Convert database row to ContextItem"""
        try:
            return ContextItem(
                id=row[0],
                context_type=ContextType(row[1]),
                scope=MemoryScope(row[2]),
                content=json.loads(row[3]),
                metadata=json.loads(row[4]),
                tab_id=row[5],
                domain=row[6],
                timestamp=datetime.fromisoformat(row[7]),
                expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
                relevance_score=row[9]
            )
        except Exception as e:
            logger.warning("Failed to convert row to context item", error=str(e))
            return None
    
    def _calculate_query_relevance(self, item: ContextItem, query: str) -> float:
        """Calculate how relevant a context item is to a query"""
        query_lower = query.lower()
        relevance = 0.0
        
        # Check content for query terms
        content_text = json.dumps(item.content).lower()
        query_words = query_lower.split()
        
        for word in query_words:
            if word in content_text:
                relevance += 0.2
        
        # Check metadata
        metadata_text = json.dumps(item.metadata).lower()
        for word in query_words:
            if word in metadata_text:
                relevance += 0.1
        
        # Boost recent items
        age_hours = (datetime.now() - item.timestamp).total_seconds() / 3600
        recency_boost = max(0, 1.0 - (age_hours / 168))  # Decay over a week
        
        # Apply context type weighting
        type_weights = {
            ContextType.CONVERSATION: 1.0,
            ContextType.FORM_DATA: 0.8,
            ContextType.WORKFLOW: 0.9,
            ContextType.USER_ACTION: 0.7,
            ContextType.PAGE_VISIT: 0.5,
            ContextType.SEARCH_QUERY: 0.6,
            ContextType.PREFERENCE: 1.2,
            ContextType.SESSION: 0.3
        }
        
        type_weight = type_weights.get(item.context_type, 1.0)
        
        return (relevance + recency_boost) * type_weight
    
    async def store_conversation(self, 
                               user_message: str,
                               ai_response: str,
                               tab_id: Optional[str] = None,
                               page_url: Optional[str] = None) -> str:
        """Store a conversation exchange"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(page_url).netloc if page_url else None
            
            conversation_data = {
                'user_message': user_message,
                'ai_response': ai_response,
                'page_url': page_url,
                'timestamp': datetime.now().isoformat()
            }
            
            return await self.store_context(
                context_type=ContextType.CONVERSATION,
                content=conversation_data,
                scope=MemoryScope.GLOBAL,
                tab_id=tab_id,
                domain=domain
            )
            
        except Exception as e:
            logger.error("Failed to store conversation", error=str(e))
            return ""
    
    async def store_user_action(self,
                              action_type: str,
                              parameters: Dict[str, Any],
                              page_url: str,
                              tab_id: Optional[str] = None,
                              success: bool = True) -> str:
        """Store a user action for learning and context"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(page_url).netloc
            
            action_data = {
                'action_type': action_type,
                'parameters': parameters,
                'page_url': page_url,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            
            return await self.store_context(
                context_type=ContextType.USER_ACTION,
                content=action_data,
                scope=MemoryScope.DOMAIN,
                tab_id=tab_id,
                domain=domain,
                ttl_hours=72  # Keep actions for 3 days
            )
            
        except Exception as e:
            logger.error("Failed to store user action", error=str(e))
            return ""
    
    async def store_form_data(self,
                            form_data: Dict[str, Any],
                            page_url: str,
                            tab_id: Optional[str] = None) -> str:
        """Store form data for auto-fill suggestions"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(page_url).netloc
            
            # Sanitize sensitive data
            sanitized_data = self._sanitize_form_data(form_data)
            
            form_context = {
                'form_data': sanitized_data,
                'page_url': page_url,
                'domain': domain,
                'timestamp': datetime.now().isoformat()
            }
            
            return await self.store_context(
                context_type=ContextType.FORM_DATA,
                content=form_context,
                scope=MemoryScope.DOMAIN,
                tab_id=tab_id,
                domain=domain,
                ttl_hours=168  # Keep form data for a week
            )
            
        except Exception as e:
            logger.error("Failed to store form data", error=str(e))
            return ""
    
    def _sanitize_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from form data"""
        sensitive_keys = ['password', 'passwd', 'pwd', 'ssn', 'social_security', 'credit_card', 'cvv', 'pin']
        sanitized = {}
        
        for key, value in form_data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def get_conversation_history(self, 
                                     tab_id: Optional[str] = None,
                                     domain: Optional[str] = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            context_items = await self.get_relevant_context(
                query="",
                context_types=[ContextType.CONVERSATION],
                tab_id=tab_id,
                domain=domain,
                limit=limit
            )
            
            conversations = []
            for item in context_items:
                conversations.append(item.content)
            
            # Sort by timestamp (most recent first)
            conversations.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return conversations
            
        except Exception as e:
            logger.error("Failed to get conversation history", error=str(e))
            return []
    
    async def store_user_preference(self,
                                  key: str,
                                  value: Any,
                                  category: str = "general",
                                  description: Optional[str] = None):
        """Store a user preference"""
        try:
            preference = UserPreference(
                key=key,
                value=value,
                category=category,
                description=description
            )
            
            self.user_preferences[key] = preference
            
            # Persist to database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (key, value, category, description, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    preference.key,
                    json.dumps(preference.value),
                    preference.category,
                    preference.description,
                    preference.timestamp.isoformat()
                ))
                await db.commit()
            
            logger.debug("User preference stored", key=key, category=category)
            
        except Exception as e:
            logger.error("Failed to store user preference", error=str(e))
    
    async def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        try:
            if key in self.user_preferences:
                return self.user_preferences[key].value
            return default
            
        except Exception as e:
            logger.error("Failed to get user preference", error=str(e))
            return default
    
    async def _load_user_preferences(self):
        """Load user preferences from database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM user_preferences") as cursor:
                    async for row in cursor:
                        preference = UserPreference(
                            key=row[0],
                            value=json.loads(row[1]),
                            category=row[2],
                            description=row[3],
                            timestamp=datetime.fromisoformat(row[4])
                        )
                        self.user_preferences[preference.key] = preference
            
            logger.info("User preferences loaded", count=len(self.user_preferences))
            
        except Exception as e:
            logger.error("Failed to load user preferences", error=str(e))
    
    async def _cleanup_expired_items(self):
        """Remove expired context items"""
        try:
            current_time = datetime.now()
            
            # Remove from cache
            expired_keys = [
                key for key, item in self.memory_cache.items()
                if item.expires_at and item.expires_at < current_time
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Remove from database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM context_items 
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (current_time.isoformat(),))
                await db.commit()
            
            if expired_keys:
                logger.info("Cleaned up expired context items", count=len(expired_keys))
                
        except Exception as e:
            logger.error("Failed to cleanup expired items", error=str(e))
    
    async def register_tab(self, tab_id: str):
        """Register a new tab"""
        self.active_tabs.add(tab_id)
        logger.debug("Tab registered", tab_id=tab_id)
    
    async def unregister_tab(self, tab_id: str):
        """Unregister a tab"""
        self.active_tabs.discard(tab_id)
        logger.debug("Tab unregistered", tab_id=tab_id)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Count items by type
                type_counts = {}
                async with db.execute("""
                    SELECT context_type, COUNT(*) FROM context_items GROUP BY context_type
                """) as cursor:
                    async for row in cursor:
                        type_counts[row[0]] = row[1]
                
                # Count items by scope
                scope_counts = {}
                async with db.execute("""
                    SELECT scope, COUNT(*) FROM context_items GROUP BY scope
                """) as cursor:
                    async for row in cursor:
                        scope_counts[row[0]] = row[1]
                
                # Total counts
                async with db.execute("SELECT COUNT(*) FROM context_items") as cursor:
                    total_items = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM user_preferences") as cursor:
                    total_preferences = (await cursor.fetchone())[0]
            
            return {
                'session_id': self.session_id,
                'active_tabs': len(self.active_tabs),
                'total_context_items': total_items,
                'total_preferences': total_preferences,
                'cache_size': len(self.memory_cache),
                'context_types': type_counts,
                'scopes': scope_counts
            }
            
        except Exception as e:
            logger.error("Failed to get memory stats", error=str(e))
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self._cleanup_expired_items()
            self.memory_cache.clear()
            self.active_tabs.clear()
            logger.info("Memory manager cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup memory manager", error=str(e))

# Global instance
memory_manager = CrossTabMemoryManager()