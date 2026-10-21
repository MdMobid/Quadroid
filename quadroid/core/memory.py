"""
Quadroid Memory Engine — Persistent conversation storage, semantic recall, and user profile learning.

Architecture:
  - SQLite: Stores all conversation pairs with timestamps
  - ChromaDB: Vector store for semantic similarity search (RAG recall)
  - UserProfile: JSON file tracking learned user preferences and facts
  - Sentence Transformers: Local embedding model for offline-capable vector search
"""
import json
import sqlite3
import hashlib
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Silence HuggingFace and SentenceTransformers loggers
try:
    import huggingface_hub.utils.logging as hf_logging
    hf_logging.set_verbosity_error()
    hf_logging.disable_progress_bars()
except Exception:
    pass

from quadroid.config import Config

logger = logging.getLogger(__name__)

# Lazy-loaded heavy imports
_chroma_client = None
_collection = None
_embedding_fn = None


def _get_embedding_function():
    """Lazy-load the sentence-transformers embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
                _embedding_fn = SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"  # ~80MB, fast, works offline after first download
                )
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            _embedding_fn = None
    return _embedding_fn


def _get_chroma_collection():
    """Lazy-load ChromaDB client and collection."""
    global _chroma_client, _collection
    if _collection is None:
        try:
            import chromadb
            persist_dir = str(Config.MEMORY_DIR / "vectors")
            _chroma_client = chromadb.PersistentClient(path=persist_dir)
            embed_fn = _get_embedding_function()
            if embed_fn:
                _collection = _chroma_client.get_or_create_collection(
                    name="quadroid_memory",
                    embedding_function=embed_fn,
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                _collection = _chroma_client.get_or_create_collection(
                    name="quadroid_memory",
                    metadata={"hnsw:space": "cosine"}
                )
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB: {e}")
            _collection = None
    return _collection


class MemoryEngine:
    """Persistent memory system with conversation storage, semantic recall, and user profile."""

    def __init__(self):
        # Ensure memory directories exist
        Config.MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        # SQLite for conversation history
        self.db_path = Config.MEMORY_DIR / "conversations.db"
        self._init_db()

        # User profile (learned facts about the user)
        self.profile_path = Config.MEMORY_DIR / "user_profile.json"
        self.user_profile = self._load_profile()

    def _init_db(self):
        """Initialize SQLite conversation store."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                tools_used TEXT,
                session_id TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)
        """)
        conn.commit()
        conn.close()

    def _load_profile(self) -> Dict[str, Any]:
        """Load user profile from disk."""
        if self.profile_path.exists():
            try:
                return json.loads(self.profile_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "facts": {},       # key-value facts (e.g., "name": "Mobid")
            "preferences": {}, # learned preferences
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _save_profile(self):
        """Persist user profile to disk."""
        self.user_profile["updated_at"] = datetime.now().isoformat()
        self.profile_path.write_text(
            json.dumps(self.user_profile, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ── Store Conversations ──

    def store(self, user_input: str, assistant_response: str, tools_used: List[str] = None, session_id: str = None):
        """
        Store a conversation exchange in both SQLite and ChromaDB vector store.

        :param user_input: The user's query/command
        :param assistant_response: The assistant's response
        :param tools_used: List of tools invoked during this exchange
        :param session_id: Optional session identifier
        """
        timestamp = datetime.now().isoformat()
        tools_str = json.dumps(tools_used) if tools_used else "[]"

        # 1. Store in SQLite
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                "INSERT INTO conversations (timestamp, user_input, assistant_response, tools_used, session_id) VALUES (?, ?, ?, ?, ?)",
                (timestamp, user_input, assistant_response, tools_str, session_id or "")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store conversation in SQLite: {e}")

        # 2. Store in ChromaDB vector store
        try:
            collection = _get_chroma_collection()
            if collection is not None:
                # Create a combined document for embedding
                combined_text = f"User: {user_input}\nAssistant: {assistant_response}"
                doc_id = hashlib.md5(f"{timestamp}:{user_input}".encode()).hexdigest()

                collection.add(
                    documents=[combined_text],
                    metadatas=[{
                        "timestamp": timestamp,
                        "user_input": user_input[:500],
                        "assistant_response": assistant_response[:500],
                        "tools_used": tools_str
                    }],
                    ids=[doc_id]
                )
        except Exception as e:
            logger.warning(f"Failed to store in vector memory: {e}")

        # 3. Learn from the exchange
        self._learn_from_exchange(user_input, assistant_response)

    # ── Recall Past Context ──

    def recall(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Semantically search past conversations for relevant context.

        :param query: The current user query to find related past conversations
        :param max_results: Max number of results to return
        :returns: List of relevant past exchanges with similarity scores
        """
        if max_results is None:
            max_results = Config.MEMORY_MAX_RECALL

        results = []

        try:
            collection = _get_chroma_collection()
            if collection is not None and collection.count() > 0:
                search_results = collection.query(
                    query_texts=[query],
                    n_results=min(max_results, collection.count())
                )

                if search_results and search_results["documents"]:
                    for i, doc in enumerate(search_results["documents"][0]):
                        meta = search_results["metadatas"][0][i] if search_results["metadatas"] else {}
                        distance = search_results["distances"][0][i] if search_results["distances"] else 1.0

                        # Only include results with reasonable similarity (cosine distance < 0.8)
                        if distance < 0.8:
                            results.append({
                                "content": doc,
                                "user_input": meta.get("user_input", ""),
                                "assistant_response": meta.get("assistant_response", ""),
                                "timestamp": meta.get("timestamp", ""),
                                "similarity": round(1 - distance, 3)
                            })
        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")

        return results

    # ── User Profile Learning ──

    def _learn_from_exchange(self, user_input: str, assistant_response: str):
        """Extract and store user facts/preferences from conversation."""
        low = user_input.lower()

        # Learn user's name
        name_patterns = [
            ("my name is ", "name"),
            ("i'm ", "name"),
            ("i am ", "name"),
            ("call me ", "name"),
        ]
        for pattern, key in name_patterns:
            if pattern in low:
                idx = low.index(pattern) + len(pattern)
                name_candidate = user_input[idx:].strip().split(".")[0].split(",")[0].strip()
                if name_candidate and len(name_candidate) < 30:
                    self.user_profile["facts"]["name"] = name_candidate
                    self._save_profile()
                    break

        # Learn favorite things
        fav_patterns = [
            ("my favorite ", "favorite_"),
            ("i love ", "loves_"),
            ("i prefer ", "prefers_"),
            ("i like ", "likes_"),
        ]
        for pattern, prefix in fav_patterns:
            if pattern in low:
                idx = low.index(pattern) + len(pattern)
                rest = user_input[idx:].strip().split(".")[0].strip()
                if rest and len(rest) < 100:
                    # Try to extract "X is Y" or just store the whole thing
                    key = f"{prefix}{rest.split()[0].lower()}" if rest.split() else prefix
                    self.user_profile["preferences"][key] = rest
                    self._save_profile()
                    break

        # Learn occupation/role
        if "i work as" in low or "i'm a " in low or "i am a " in low:
            for pattern in ["i work as ", "i'm a ", "i am a "]:
                if pattern in low:
                    idx = low.index(pattern) + len(pattern)
                    role = user_input[idx:].strip().split(".")[0].strip()
                    if role and len(role) < 50:
                        self.user_profile["facts"]["occupation"] = role
                        self._save_profile()
                    break

    def get_profile_context(self) -> str:
        """Generate a context string from the user profile for the system prompt."""
        parts = []

        facts = self.user_profile.get("facts", {})
        if facts.get("name"):
            parts.append(f"The user's name is {facts['name']}.")
        if facts.get("occupation"):
            parts.append(f"The user works as {facts['occupation']}.")

        prefs = self.user_profile.get("preferences", {})
        for key, value in list(prefs.items())[:5]:  # Limit to 5 preferences
            clean_key = key.replace("_", " ").replace("favorite ", "favorite ").replace("likes ", "likes ")
            parts.append(f"User {clean_key}: {value}.")

        return " ".join(parts) if parts else ""

    def get_recall_context(self, query: str) -> str:
        """Generate a recall context string for injection into the system prompt."""
        recalls = self.recall(query)
        if not recalls:
            return ""

        context_parts = ["[MEMORY RECALL — Related past conversations:]"]
        for r in recalls:
            ts = r.get("timestamp", "")[:10]  # Just the date
            context_parts.append(f"- [{ts}] Q: {r['user_input'][:120]} → A: {r['assistant_response'][:120]}")

        return "\n".join(context_parts)

    # ── Stats & Management ──

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]

            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM conversations")
            row = cursor.fetchone()
            first_memory = row[0] if row[0] else "None"
            last_memory = row[1] if row[1] else "None"
            conn.close()

            collection = _get_chroma_collection()
            vector_count = collection.count() if collection else 0

            return {
                "total_conversations": total_conversations,
                "vector_entries": vector_count,
                "profile_facts": len(self.user_profile.get("facts", {})),
                "profile_preferences": len(self.user_profile.get("preferences", {})),
                "first_memory": first_memory,
                "last_memory": last_memory,
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_all(self):
        """Clear all stored memories (conversations, vectors, profile)."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("DELETE FROM conversations")
            conn.commit()
            conn.close()
        except Exception:
            pass

        try:
            collection = _get_chroma_collection()
            if collection and collection.count() > 0:
                # Delete all entries
                all_ids = collection.get()["ids"]
                if all_ids:
                    collection.delete(ids=all_ids)
        except Exception:
            pass

        self.user_profile = {
            "facts": {},
            "preferences": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_profile()

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent conversations from SQLite."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                "SELECT timestamp, user_input, assistant_response, tools_used FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "timestamp": row[0],
                    "user_input": row[1],
                    "assistant_response": row[2],
                    "tools_used": json.loads(row[3]) if row[3] else []
                }
                for row in rows
            ]
        except Exception:
            return []
