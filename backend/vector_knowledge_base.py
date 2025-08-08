#!/usr/bin/env python3
"""
Local Vector Knowledge Base for AI Browser
Semantic search and intelligent content indexing using local embeddings
"""

import asyncio
import json
import sqlite3
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import structlog
import pickle
import re
from sentence_transformers import SentenceTransformer
import faiss

logger = structlog.get_logger(__name__)

@dataclass
class ContentChunk:
    """A chunk of content with metadata"""
    id: str
    url: str
    title: str
    content: str
    chunk_type: str  # "paragraph", "heading", "list", "table"
    position: int
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class SemanticSearchResult:
    """Result from semantic search"""
    content_chunk: ContentChunk
    similarity_score: float
    relevance_explanation: str

class LocalVectorDB:
    """Local vector database using FAISS for fast similarity search"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".ai-browser" / "vector_db"
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model (local, no cloud required)
        self.embedding_model = None
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
        # FAISS index for fast similarity search
        self.faiss_index = None
        
        # SQLite for metadata storage
        self.db_file = self.db_path / "content.db"
        self.content_chunks = {}  # In-memory cache
        
        # Initialize database
        self._init_database()
        self._load_embedding_model()
        self._load_faiss_index()
        
        logger.info("Vector knowledge base initialized", db_path=str(self.db_path))
    
    def _init_database(self):
        """Initialize SQLite database for metadata"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS content_chunks (
                id TEXT PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                chunk_type TEXT,
                position INTEGER,
                timestamp TEXT,
                metadata TEXT,
                embedding BLOB
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url ON content_chunks(url);
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON content_chunks(timestamp);
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_type ON content_chunks(chunk_type);
        """)
        
        conn.commit()
        conn.close()
    
    def _load_embedding_model(self):
        """Load local sentence transformer model"""
        try:
            # Use a lightweight local model
            model_name = "all-MiniLM-L6-v2"  # 80MB model, good performance
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info("Embedding model loaded", model=model_name, dim=self.embedding_dim)
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            logger.warning("Vector search will be unavailable")
    
    def _load_faiss_index(self):
        """Load or create FAISS index"""
        index_file = self.db_path / "faiss_index.bin"
        
        if index_file.exists() and self.embedding_model:
            try:
                self.faiss_index = faiss.read_index(str(index_file))
                logger.info("FAISS index loaded", size=self.faiss_index.ntotal)
            except Exception as e:
                logger.warning("Failed to load FAISS index, creating new", error=str(e))
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new FAISS index"""
        if self.embedding_model:
            # Use IndexFlatIP for cosine similarity
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info("Created new FAISS index", dim=self.embedding_dim)
    
    def _save_faiss_index(self):
        """Save FAISS index to disk"""
        if self.faiss_index:
            index_file = self.db_path / "faiss_index.bin"
            faiss.write_index(self.faiss_index, str(index_file))
    
    async def add_page_content(self, url: str, title: str, html_content: str, 
                              page_metadata: Dict[str, Any] = None) -> int:
        """Add page content to the vector database"""
        try:
            logger.info("Adding page content to vector DB", url=url)
            
            # Extract and chunk content
            chunks = self._extract_content_chunks(url, title, html_content, page_metadata or {})
            
            if not chunks:
                logger.warning("No content chunks extracted", url=url)
                return 0
            
            # Generate embeddings for chunks
            if self.embedding_model:
                embeddings = await self._generate_embeddings([chunk.content for chunk in chunks])
            else:
                embeddings = None
            
            # Store in database
            added_count = 0
            conn = sqlite3.connect(self.db_file)
            
            for i, chunk in enumerate(chunks):
                embedding_blob = None
                if embeddings is not None:
                    embedding_blob = pickle.dumps(embeddings[i])
                
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO content_chunks 
                        (id, url, title, content, chunk_type, position, timestamp, metadata, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk.id, chunk.url, chunk.title, chunk.content,
                        chunk.chunk_type, chunk.position, chunk.timestamp,
                        json.dumps(chunk.metadata), embedding_blob
                    ))
                    
                    # Cache in memory
                    self.content_chunks[chunk.id] = chunk
                    added_count += 1
                    
                except sqlite3.Error as e:
                    logger.warning("Failed to store chunk", chunk_id=chunk.id, error=str(e))
            
            conn.commit()
            conn.close()
            
            # Add embeddings to FAISS index
            if embeddings is not None and self.faiss_index is not None:
                # Normalize embeddings for cosine similarity
                normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                self.faiss_index.add(normalized_embeddings)
                self._save_faiss_index()
            
            logger.info("Page content added to vector DB", 
                       url=url, chunks_added=added_count)
            
            return added_count
            
        except Exception as e:
            logger.error("Failed to add page content", url=url, error=str(e))
            return 0
    
    def _extract_content_chunks(self, url: str, title: str, html_content: str, 
                               metadata: Dict[str, Any]) -> List[ContentChunk]:
        """Extract meaningful content chunks from HTML"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        chunks = []
        position = 0
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract different types of content chunks
        
        # 1. Headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            if len(text) > 5:
                chunk = ContentChunk(
                    id=self._generate_chunk_id(url, text, position),
                    url=url,
                    title=title,
                    content=text,
                    chunk_type="heading",
                    position=position,
                    timestamp=datetime.now().isoformat(),
                    metadata={**metadata, "heading_level": heading.name}
                )
                chunks.append(chunk)
                position += 1
        
        # 2. Paragraphs
        for para in soup.find_all('p'):
            text = para.get_text(strip=True)
            if len(text) > 50:  # Only meaningful paragraphs
                chunk = ContentChunk(
                    id=self._generate_chunk_id(url, text, position),
                    url=url,
                    title=title,
                    content=text,
                    chunk_type="paragraph",
                    position=position,
                    timestamp=datetime.now().isoformat(),
                    metadata=metadata
                )
                chunks.append(chunk)
                position += 1
        
        # 3. Lists
        for list_elem in soup.find_all(['ul', 'ol']):
            items = list_elem.find_all('li')
            if items:
                list_text = ' | '.join(item.get_text(strip=True) for item in items)
                if len(list_text) > 30:
                    chunk = ContentChunk(
                        id=self._generate_chunk_id(url, list_text, position),
                        url=url,
                        title=title,
                        content=list_text,
                        chunk_type="list",
                        position=position,
                        timestamp=datetime.now().isoformat(),
                        metadata={**metadata, "list_type": list_elem.name, "items": len(items)}
                    )
                    chunks.append(chunk)
                    position += 1
        
        # 4. Tables
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if len(rows) > 1:  # Has header + data
                table_text = []
                for row in rows[:10]:  # Limit to first 10 rows
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = ' | '.join(cell.get_text(strip=True) for cell in cells)
                        if row_text:
                            table_text.append(row_text)
                
                if table_text:
                    content = '\n'.join(table_text)
                    chunk = ContentChunk(
                        id=self._generate_chunk_id(url, content, position),
                        url=url,
                        title=title,
                        content=content,
                        chunk_type="table",
                        position=position,
                        timestamp=datetime.now().isoformat(),
                        metadata={**metadata, "table_rows": len(table_text)}
                    )
                    chunks.append(chunk)
                    position += 1
        
        # 5. Article/main content
        main_content = soup.find(['main', 'article', '[role="main"]'])
        if main_content:
            text = main_content.get_text(strip=True, separator=' ')
            # Split long content into chunks
            if len(text) > 1000:
                sentences = re.split(r'[.!?]+', text)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if current_length + len(sentence) > 800 and current_chunk:
                        # Save current chunk
                        chunk_text = '. '.join(current_chunk) + '.'
                        chunk = ContentChunk(
                            id=self._generate_chunk_id(url, chunk_text, position),
                            url=url,
                            title=title,
                            content=chunk_text,
                            chunk_type="content_section",
                            position=position,
                            timestamp=datetime.now().isoformat(),
                            metadata=metadata
                        )
                        chunks.append(chunk)
                        position += 1
                        
                        # Start new chunk
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)
                
                # Add remaining chunk
                if current_chunk:
                    chunk_text = '. '.join(current_chunk) + '.'
                    chunk = ContentChunk(
                        id=self._generate_chunk_id(url, chunk_text, position),
                        url=url,
                        title=title,
                        content=chunk_text,
                        chunk_type="content_section",
                        position=position,
                        timestamp=datetime.now().isoformat(),
                        metadata=metadata
                    )
                    chunks.append(chunk)
        
        logger.info("Content chunks extracted", url=url, chunk_count=len(chunks))
        return chunks
    
    def _generate_chunk_id(self, url: str, content: str, position: int) -> str:
        """Generate unique ID for content chunk"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{url_hash}_{position}_{content_hash}"
    
    async def _generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for texts"""
        if not self.embedding_model:
            return None
        
        try:
            # Process in batches to avoid memory issues
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
                all_embeddings.append(embeddings)
            
            return np.vstack(all_embeddings)
            
        except Exception as e:
            logger.error("Failed to generate embeddings", error=str(e))
            return None
    
    async def semantic_search(self, query: str, limit: int = 10, 
                             filters: Dict[str, Any] = None) -> List[SemanticSearchResult]:
        """Perform semantic search over indexed content"""
        try:
            if not self.embedding_model or not self.faiss_index:
                logger.warning("Semantic search unavailable - missing model or index")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.faiss_index.search(query_embedding, limit * 2)  # Get more to allow filtering
            
            # Retrieve matching chunks from database
            results = []
            conn = sqlite3.connect(self.db_file)
            
            chunk_counter = 0
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or chunk_counter >= limit:  # -1 means no more results
                    break
                
                # Get chunk by index (this is approximate - in production you'd want better mapping)
                cursor = conn.execute("""
                    SELECT id, url, title, content, chunk_type, position, timestamp, metadata
                    FROM content_chunks 
                    ORDER BY timestamp DESC 
                    LIMIT 1 OFFSET ?
                """, (int(idx),))
                
                row = cursor.fetchone()
                if row:
                    chunk = ContentChunk(
                        id=row[0], url=row[1], title=row[2], content=row[3],
                        chunk_type=row[4], position=row[5], timestamp=row[6],
                        metadata=json.loads(row[7]) if row[7] else {}
                    )
                    
                    # Apply filters
                    if self._passes_filters(chunk, filters):
                        result = SemanticSearchResult(
                            content_chunk=chunk,
                            similarity_score=float(score),
                            relevance_explanation=f"Semantic similarity: {score:.3f}"
                        )
                        results.append(result)
                        chunk_counter += 1
            
            conn.close()
            
            logger.info("Semantic search completed", 
                       query=query, results_found=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Semantic search failed", query=query, error=str(e))
            return []
    
    async def keyword_search(self, query: str, limit: int = 10, 
                            filters: Dict[str, Any] = None) -> List[SemanticSearchResult]:
        """Perform traditional keyword search"""
        try:
            # Simple SQL-based keyword search
            keywords = query.lower().split()
            where_conditions = []
            params = []
            
            for keyword in keywords:
                where_conditions.append("(LOWER(content) LIKE ? OR LOWER(title) LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Apply filters
            filter_conditions, filter_params = self._build_filter_conditions(filters)
            if filter_conditions:
                where_clause += " AND " + filter_conditions
                params.extend(filter_params)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.execute(f"""
                SELECT id, url, title, content, chunk_type, position, timestamp, metadata
                FROM content_chunks 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            """, params + [limit])
            
            results = []
            for row in cursor.fetchall():
                chunk = ContentChunk(
                    id=row[0], url=row[1], title=row[2], content=row[3],
                    chunk_type=row[4], position=row[5], timestamp=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
                
                # Calculate keyword relevance score
                score = self._calculate_keyword_score(query, chunk.content + " " + chunk.title)
                
                result = SemanticSearchResult(
                    content_chunk=chunk,
                    similarity_score=score,
                    relevance_explanation=f"Keyword match score: {score:.3f}"
                )
                results.append(result)
            
            conn.close()
            
            logger.info("Keyword search completed", 
                       query=query, results_found=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Keyword search failed", query=query, error=str(e))
            return []
    
    def _passes_filters(self, chunk: ContentChunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk passes the given filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key == "url" and value not in chunk.url:
                return False
            elif key == "chunk_type" and chunk.chunk_type != value:
                return False
            elif key == "after_date" and chunk.timestamp < value:
                return False
            # Add more filter conditions as needed
        
        return True
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build SQL WHERE conditions for filters"""
        conditions = []
        params = []
        
        if not filters:
            return "", []
        
        if "url" in filters:
            conditions.append("url LIKE ?")
            params.append(f"%{filters['url']}%")
        
        if "chunk_type" in filters:
            conditions.append("chunk_type = ?")
            params.append(filters["chunk_type"])
        
        if "after_date" in filters:
            conditions.append("timestamp > ?")
            params.append(filters["after_date"])
        
        return " AND ".join(conditions), params
    
    def _calculate_keyword_score(self, query: str, text: str) -> float:
        """Calculate keyword relevance score"""
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Count keyword occurrences
        keywords = query_lower.split()
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            matches += text_lower.count(keyword)
        
        # Normalize by text length and keyword count
        if total_keywords == 0 or len(text) == 0:
            return 0.0
        
        score = (matches / total_keywords) * min(1.0, 100 / len(text))
        return min(1.0, score)
    
    async def get_related_content(self, url: str, limit: int = 5) -> List[ContentChunk]:
        """Get content related to a specific URL"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.execute("""
                SELECT id, url, title, content, chunk_type, position, timestamp, metadata
                FROM content_chunks 
                WHERE url = ?
                ORDER BY position
                LIMIT ?
            """, (url, limit))
            
            chunks = []
            for row in cursor.fetchall():
                chunk = ContentChunk(
                    id=row[0], url=row[1], title=row[2], content=row[3],
                    chunk_type=row[4], position=row[5], timestamp=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
                chunks.append(chunk)
            
            conn.close()
            return chunks
            
        except Exception as e:
            logger.error("Failed to get related content", url=url, error=str(e))
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            
            # Total chunks
            total_chunks = conn.execute("SELECT COUNT(*) FROM content_chunks").fetchone()[0]
            
            # Chunks by type
            chunk_types = conn.execute("""
                SELECT chunk_type, COUNT(*) 
                FROM content_chunks 
                GROUP BY chunk_type
            """).fetchall()
            
            # Recent activity
            recent_chunks = conn.execute("""
                SELECT COUNT(*) FROM content_chunks 
                WHERE timestamp > datetime('now', '-24 hours')
            """).fetchone()[0]
            
            conn.close()
            
            stats = {
                "total_chunks": total_chunks,
                "chunk_types": dict(chunk_types),
                "recent_chunks_24h": recent_chunks,
                "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None,
                "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0,
                "db_path": str(self.db_path)
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {"error": str(e)}

# Factory function for easy integration
async def create_vector_knowledge_base(db_path: Optional[Path] = None):
    """Factory function to create vector knowledge base"""
    return LocalVectorDB(db_path)