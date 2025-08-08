"""
Smart Context Management Across Tabs
Maintains AI conversation continuity and intelligent context sharing
"""

import asyncio
import json
import logging
import sqlite3
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from collections import defaultdict

@dataclass
class TabContext:
    tab_id: str
    url: str
    title: str
    content_hash: str
    last_activity: datetime
    conversation_history: List[Dict[str, Any]]
    extracted_entities: Dict[str, Any]
    user_intent: str
    related_tabs: Set[str]
    context_score: float = 0.0

@dataclass
class GlobalContext:
    user_session_id: str
    active_task: Optional[str]
    task_progress: Dict[str, Any]
    cross_tab_memory: Dict[str, Any]
    learned_patterns: List[Dict[str, Any]]
    priority_contexts: List[str]

class SmartContextManager:
    """Intelligent context management for seamless AI experience across browser tabs"""
    
    def __init__(self, ai_client=None, db_path: str = "smart_context.db"):
        self.ai_client = ai_client
        self.db_path = db_path
        self.tab_contexts: Dict[str, TabContext] = {}
        self.global_context = GlobalContext(
            user_session_id=str(uuid.uuid4()),
            active_task=None,
            task_progress={},
            cross_tab_memory={},
            learned_patterns=[],
            priority_contexts=[]
        )
        
        # Context analysis settings
        self.max_context_age = timedelta(hours=2)
        self.context_similarity_threshold = 0.7
        self.max_conversation_history = 50
        self.learning_enabled = True
        
        # Initialize database
        self._init_database()
        
        # Load previous context
        asyncio.create_task(self._load_persistent_context())
    
    def _init_database(self):
        """Initialize SQLite database for persistent context storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tab_contexts (
                    tab_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    content_hash TEXT,
                    last_activity TEXT,
                    conversation_history TEXT,
                    extracted_entities TEXT,
                    user_intent TEXT,
                    related_tabs TEXT,
                    context_score REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS global_context (
                    session_id TEXT PRIMARY KEY,
                    active_task TEXT,
                    task_progress TEXT,
                    cross_tab_memory TEXT,
                    learned_patterns TEXT,
                    priority_contexts TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_relationships (
                    id TEXT PRIMARY KEY,
                    source_tab TEXT,
                    target_tab TEXT,
                    relationship_type TEXT,
                    strength REAL,
                    created_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tab_activity ON tab_contexts(last_activity)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_score ON tab_contexts(context_score DESC)
            """)
    
    async def register_tab(self, 
                          tab_id: str, 
                          url: str, 
                          title: str = "", 
                          content: str = "") -> TabContext:
        """Register a new tab or update existing tab context"""
        
        # Generate content hash for change detection
        content_hash = hashlib.md5(content.encode()).hexdigest() if content else ""
        
        # Check if tab already exists
        if tab_id in self.tab_contexts:
            existing_context = self.tab_contexts[tab_id]
            
            # Update if content changed
            if existing_context.content_hash != content_hash:
                existing_context.url = url
                existing_context.title = title
                existing_context.content_hash = content_hash
                existing_context.last_activity = datetime.now()
                
                # AI-powered context analysis for significant changes
                if content and self.ai_client:
                    await self._analyze_content_change(tab_id, content)
            
            return existing_context
        
        # Create new tab context
        tab_context = TabContext(
            tab_id=tab_id,
            url=url,
            title=title,
            content_hash=content_hash,
            last_activity=datetime.now(),
            conversation_history=[],
            extracted_entities={},
            user_intent="",
            related_tabs=set()
        )
        
        self.tab_contexts[tab_id] = tab_context
        
        # Perform initial AI analysis if content available
        if content and self.ai_client:
            await self._perform_initial_analysis(tab_id, content)
        
        # Find related tabs
        await self._find_related_tabs(tab_id)
        
        # Persist to database
        await self._persist_tab_context(tab_context)
        
        logging.info(f"Registered new tab: {tab_id} ({url})")
        return tab_context
    
    async def add_conversation_turn(self, 
                                  tab_id: str, 
                                  user_message: str, 
                                  ai_response: str,
                                  context_data: Dict[str, Any] = None):
        """Add conversation turn to tab context"""
        
        if tab_id not in self.tab_contexts:
            logging.warning(f"Tab {tab_id} not registered")
            return
        
        tab_context = self.tab_contexts[tab_id]
        
        conversation_turn = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'context_data': context_data or {},
            'turn_id': str(uuid.uuid4())
        }
        
        tab_context.conversation_history.append(conversation_turn)
        tab_context.last_activity = datetime.now()
        
        # Limit conversation history size
        if len(tab_context.conversation_history) > self.max_conversation_history:
            tab_context.conversation_history = tab_context.conversation_history[-self.max_conversation_history:]
        
        # AI-powered intent analysis
        if self.ai_client:
            await self._analyze_user_intent(tab_id, user_message, ai_response)
        
        # Update context score based on activity
        tab_context.context_score += 1.0
        
        # Check for cross-tab learning opportunities
        if self.learning_enabled:
            await self._learn_from_conversation(tab_id, conversation_turn)
        
        # Persist changes
        await self._persist_tab_context(tab_context)
    
    async def get_relevant_context(self, 
                                 tab_id: str, 
                                 user_query: str,
                                 max_contexts: int = 3) -> Dict[str, Any]:
        """Get relevant context from current and related tabs for AI query"""
        
        if tab_id not in self.tab_contexts:
            return {}
        
        current_tab = self.tab_contexts[tab_id]
        relevant_context = {
            'current_tab': {
                'url': current_tab.url,
                'title': current_tab.title,
                'user_intent': current_tab.user_intent,
                'recent_conversation': current_tab.conversation_history[-5:],
                'entities': current_tab.extracted_entities
            },
            'related_tabs': [],
            'global_context': {
                'active_task': self.global_context.active_task,
                'task_progress': self.global_context.task_progress,
                'session_insights': self._get_session_insights()
            },
            'cross_tab_memory': {}
        }
        
        # Find most relevant related tabs
        if self.ai_client:
            related_scores = await self._score_tab_relevance(tab_id, user_query)
            
            for related_tab_id, score in sorted(related_scores.items(), 
                                              key=lambda x: x[1], 
                                              reverse=True)[:max_contexts]:
                if related_tab_id != tab_id and score > self.context_similarity_threshold:
                    related_tab = self.tab_contexts.get(related_tab_id)
                    if related_tab:
                        relevant_context['related_tabs'].append({
                            'tab_id': related_tab_id,
                            'url': related_tab.url,
                            'title': related_tab.title,
                            'relevance_score': score,
                            'key_entities': related_tab.extracted_entities,
                            'recent_activity': related_tab.conversation_history[-3:]
                        })
        
        # Add cross-tab memory relevant to query
        relevant_memory = self._search_cross_tab_memory(user_query)
        relevant_context['cross_tab_memory'] = relevant_memory
        
        return relevant_context
    
    async def _perform_initial_analysis(self, tab_id: str, content: str):
        """AI-powered analysis of new tab content"""
        
        analysis_prompt = f"""
        Analyze this webpage content and extract key information:
        
        Content: {content[:2000]}...
        
        Extract:
        1. Main topic/theme
        2. Key entities (people, places, companies, products)
        3. User's likely intent for visiting this page
        4. Actionable items or next steps suggested
        5. Content category (news, shopping, research, work, etc.)
        
        Return structured JSON:
        {{
          "main_topic": "...",
          "entities": {{"people": [], "companies": [], "products": []}},
          "user_intent": "...",
          "actionable_items": [],
          "category": "...",
          "key_insights": []
        }}
        """
        
        try:
            ai_response = await self.ai_client.chat(
                message=analysis_prompt,
                context={'task': 'content_analysis'}
            )
            
            response_text = ai_response.get('response', '')
            
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                analysis_data = json.loads(response_text[start_idx:end_idx])
                
                tab_context = self.tab_contexts[tab_id]
                tab_context.extracted_entities = analysis_data.get('entities', {})
                tab_context.user_intent = analysis_data.get('user_intent', '')
                
                # Store insights in cross-tab memory
                insights = analysis_data.get('key_insights', [])
                for insight in insights:
                    self._store_cross_tab_insight(tab_id, insight, 'content_analysis')
                
                logging.info(f"Initial analysis complete for tab {tab_id}")
                
        except Exception as e:
            logging.error(f"Initial analysis failed for tab {tab_id}: {e}")
    
    async def _analyze_user_intent(self, tab_id: str, user_message: str, ai_response: str):
        """Analyze user intent from conversation"""
        
        intent_prompt = f"""
        Based on this conversation, what is the user's current intent?
        
        User: {user_message}
        AI: {ai_response[:200]}...
        
        Current tab: {self.tab_contexts[tab_id].url}
        
        Classify intent as one of:
        - research: Gathering information
        - task_completion: Trying to complete a specific task
        - problem_solving: Solving a specific problem
        - exploration: Browsing/exploring
        - work: Professional work activity
        - shopping: Making purchases
        - entertainment: Leisure activity
        
        Return just the classification word.
        """
        
        try:
            ai_response_obj = await self.ai_client.chat(
                message=intent_prompt,
                context={'task': 'intent_analysis'}
            )
            
            intent = ai_response_obj.get('response', '').strip().lower()
            
            # Update tab context
            tab_context = self.tab_contexts[tab_id]
            tab_context.user_intent = intent
            
            # Update global context if this seems to be main task
            if tab_context.context_score > 5.0:  # High activity tab
                self.global_context.active_task = intent
                
        except Exception as e:
            logging.error(f"Intent analysis failed: {e}")
    
    async def _find_related_tabs(self, tab_id: str):
        """Find tabs related to the given tab"""
        
        if tab_id not in self.tab_contexts:
            return
        
        current_tab = self.tab_contexts[tab_id]
        
        for other_tab_id, other_tab in self.tab_contexts.items():
            if other_tab_id == tab_id:
                continue
            
            # Calculate relationship score
            relationship_score = self._calculate_tab_similarity(current_tab, other_tab)
            
            if relationship_score > self.context_similarity_threshold:
                current_tab.related_tabs.add(other_tab_id)
                other_tab.related_tabs.add(tab_id)
                
                # Store relationship in database
                await self._store_tab_relationship(tab_id, other_tab_id, 'content_similarity', relationship_score)
    
    def _calculate_tab_similarity(self, tab1: TabContext, tab2: TabContext) -> float:
        """Calculate similarity score between two tabs"""
        
        similarity_score = 0.0
        
        # URL domain similarity
        try:
            from urllib.parse import urlparse
            domain1 = urlparse(tab1.url).netloc
            domain2 = urlparse(tab2.url).netloc
            
            if domain1 == domain2:
                similarity_score += 0.3
        except:
            pass
        
        # Title similarity (simple keyword overlap)
        title1_words = set(tab1.title.lower().split())
        title2_words = set(tab2.title.lower().split())
        
        if title1_words and title2_words:
            title_overlap = len(title1_words & title2_words) / len(title1_words | title2_words)
            similarity_score += title_overlap * 0.4
        
        # Entity overlap
        entities1 = set()
        entities2 = set()
        
        for entity_type, entity_list in tab1.extracted_entities.items():
            if isinstance(entity_list, list):
                entities1.update(entity_list)
        
        for entity_type, entity_list in tab2.extracted_entities.items():
            if isinstance(entity_list, list):
                entities2.update(entity_list)
        
        if entities1 and entities2:
            entity_overlap = len(entities1 & entities2) / len(entities1 | entities2)
            similarity_score += entity_overlap * 0.3
        
        return min(similarity_score, 1.0)
    
    async def _score_tab_relevance(self, current_tab_id: str, user_query: str) -> Dict[str, float]:
        """Score relevance of all tabs to current query using AI"""
        
        relevance_scores = {}
        current_tab = self.tab_contexts[current_tab_id]
        
        # Simple scoring for now - would use AI embedding similarity in production
        for tab_id, tab_context in self.tab_contexts.items():
            if tab_id == current_tab_id:
                continue
            
            score = 0.0
            
            # Recent activity bonus
            if tab_context.last_activity > datetime.now() - timedelta(minutes=30):
                score += 0.2
            
            # Related tab bonus
            if tab_id in current_tab.related_tabs:
                score += 0.3
            
            # Query keyword overlap with title/entities
            query_words = set(user_query.lower().split())
            title_words = set(tab_context.title.lower().split())
            
            if title_words:
                keyword_overlap = len(query_words & title_words) / len(query_words | title_words)
                score += keyword_overlap * 0.5
            
            relevance_scores[tab_id] = score
        
        return relevance_scores
    
    def _store_cross_tab_insight(self, tab_id: str, insight: str, insight_type: str):
        """Store insight for cross-tab memory"""
        
        insight_key = f"{insight_type}_{hashlib.md5(insight.encode()).hexdigest()[:8]}"
        
        self.global_context.cross_tab_memory[insight_key] = {
            'insight': insight,
            'source_tab': tab_id,
            'timestamp': datetime.now().isoformat(),
            'type': insight_type,
            'usage_count': 0
        }
    
    def _search_cross_tab_memory(self, query: str) -> Dict[str, Any]:
        """Search cross-tab memory for relevant insights"""
        
        relevant_memory = {}
        query_words = set(query.lower().split())
        
        for key, memory_item in self.global_context.cross_tab_memory.items():
            insight = memory_item['insight'].lower()
            insight_words = set(insight.split())
            
            # Simple keyword matching - would use semantic search in production
            if query_words & insight_words:
                overlap_score = len(query_words & insight_words) / len(query_words | insight_words)
                if overlap_score > 0.1:
                    relevant_memory[key] = {
                        **memory_item,
                        'relevance_score': overlap_score
                    }
                    # Increment usage count
                    self.global_context.cross_tab_memory[key]['usage_count'] += 1
        
        return relevant_memory
    
    def _get_session_insights(self) -> List[str]:
        """Generate session-level insights"""
        
        insights = []
        
        # Most active tabs
        active_tabs = sorted(
            self.tab_contexts.items(),
            key=lambda x: x[1].context_score,
            reverse=True
        )[:3]
        
        if active_tabs:
            insights.append(f"Most active: {active_tabs[0][1].title}")
        
        # Common intents
        intents = [tab.user_intent for tab in self.tab_contexts.values() if tab.user_intent]
        if intents:
            most_common_intent = max(set(intents), key=intents.count)
            insights.append(f"Primary activity: {most_common_intent}")
        
        return insights
    
    async def _persist_tab_context(self, tab_context: TabContext):
        """Persist tab context to database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tab_contexts
                    (tab_id, url, title, content_hash, last_activity, conversation_history, 
                     extracted_entities, user_intent, related_tabs, context_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tab_context.tab_id,
                    tab_context.url,
                    tab_context.title,
                    tab_context.content_hash,
                    tab_context.last_activity.isoformat(),
                    json.dumps(tab_context.conversation_history),
                    json.dumps(tab_context.extracted_entities),
                    tab_context.user_intent,
                    json.dumps(list(tab_context.related_tabs)),
                    tab_context.context_score
                ))
        except Exception as e:
            logging.error(f"Failed to persist tab context: {e}")
    
    async def _store_tab_relationship(self, 
                                    source_tab: str, 
                                    target_tab: str, 
                                    relationship_type: str, 
                                    strength: float):
        """Store tab relationship in database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO context_relationships
                    (id, source_tab, target_tab, relationship_type, strength, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"{source_tab}_{target_tab}_{relationship_type}",
                    source_tab,
                    target_tab,
                    relationship_type,
                    strength,
                    datetime.now().isoformat()
                ))
        except Exception as e:
            logging.error(f"Failed to store relationship: {e}")
    
    async def _load_persistent_context(self):
        """Load context from database on startup"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load tab contexts
                cursor = conn.execute("SELECT * FROM tab_contexts WHERE last_activity > ?", 
                                    ((datetime.now() - self.max_context_age).isoformat(),))
                
                for row in cursor.fetchall():
                    tab_context = TabContext(
                        tab_id=row[0],
                        url=row[1],
                        title=row[2] or "",
                        content_hash=row[3] or "",
                        last_activity=datetime.fromisoformat(row[4]),
                        conversation_history=json.loads(row[5] or "[]"),
                        extracted_entities=json.loads(row[6] or "{}"),
                        user_intent=row[7] or "",
                        related_tabs=set(json.loads(row[8] or "[]")),
                        context_score=row[9] or 0.0
                    )
                    
                    self.tab_contexts[tab_context.tab_id] = tab_context
                
                logging.info(f"Loaded {len(self.tab_contexts)} tab contexts from database")
                
        except Exception as e:
            logging.error(f"Failed to load persistent context: {e}")
    
    async def cleanup_old_contexts(self):
        """Clean up old, inactive contexts"""
        
        cutoff_time = datetime.now() - self.max_context_age
        
        # Remove from memory
        tabs_to_remove = []
        for tab_id, tab_context in self.tab_contexts.items():
            if tab_context.last_activity < cutoff_time:
                tabs_to_remove.append(tab_id)
        
        for tab_id in tabs_to_remove:
            del self.tab_contexts[tab_id]
        
        # Clean up database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tab_contexts WHERE last_activity < ?", 
                           (cutoff_time.isoformat(),))
                conn.execute("DELETE FROM context_relationships WHERE created_at < ?",
                           (cutoff_time.isoformat(),))
        except Exception as e:
            logging.error(f"Database cleanup failed: {e}")
        
        if tabs_to_remove:
            logging.info(f"Cleaned up {len(tabs_to_remove)} old tab contexts")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context state"""
        
        return {
            'total_tabs': len(self.tab_contexts),
            'active_tabs': len([t for t in self.tab_contexts.values() 
                              if t.last_activity > datetime.now() - timedelta(minutes=30)]),
            'primary_intent': self.global_context.active_task,
            'cross_tab_insights': len(self.global_context.cross_tab_memory),
            'learned_patterns': len(self.global_context.learned_patterns),
            'session_id': self.global_context.user_session_id
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for context management system"""
        
        return {
            'status': 'healthy',
            'context_summary': self.get_context_summary(),
            'ai_client_available': self.ai_client is not None,
            'database_accessible': Path(self.db_path).exists(),
            'learning_enabled': self.learning_enabled
        }