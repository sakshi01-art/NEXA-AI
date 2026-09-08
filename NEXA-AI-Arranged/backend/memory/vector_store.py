try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except Exception:
    HAS_CHROMADB = False

from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime

class FallbackCollection:
    def __init__(self, name: str):
        self.name = name
        self.items = [] # list of {"id": id, "document": doc, "metadata": meta}
        
    def add(self, documents: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        metadatas = metadatas or [{} for _ in documents]
        ids = ids or [f"{self.name}_{int(datetime.now().timestamp()*1000)}_{i}" for i in range(len(documents))]
        for doc, meta, item_id in zip(documents, metadatas, ids):
            self.items.append({"id": item_id, "document": doc, "metadata": meta})
            
    def upsert(self, documents: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        ids = ids or [f"{self.name}_{int(datetime.now().timestamp()*1000)}_{i}" for i in range(len(documents))]
        id_set = set(ids)
        self.items = [item for item in self.items if item["id"] not in id_set]
        self.add(documents, metadatas, ids)
        
    def get(self, where: Optional[Dict] = None) -> Dict[str, List]:
        filtered = self.items
        if where:
            filtered = [
                item for item in self.items
                if all(item["metadata"].get(k) == v for k, v in where.items())
            ]
        return {
            "documents": [item["document"] for item in filtered],
            "metadatas": [item["metadata"] for item in filtered],
            "ids": [item["id"] for item in filtered]
        }
        
    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, List]:
        if not self.items or not query_texts:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        query = query_texts[0].lower()
        # Rank by simple keyword matching
        scored = []
        for item in self.items:
            doc = item["document"].lower()
            overlap = sum(1 for word in query.split() if word in doc)
            scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [item for _, item in scored[:n_results]]
        return {
            "documents": [[item["document"] for item in top]],
            "metadatas": [[item["metadata"] for item in top]],
            "distances": [[0.1] * len(top)]
        }

class VectorMemoryStore:
    """Advanced vector-based memory with fallback semantic search"""
    
    def __init__(self, persist_directory: str = "./data/memory"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self.client = None
        
        if HAS_CHROMADB:
            try:
                self.client = chromadb.Client()
                self.conversations = self.client.get_or_create_collection(
                    name="conversations",
                    metadata={"description": "User conversation history"}
                )
                self.preferences = self.client.get_or_create_collection(
                    name="preferences",
                    metadata={"description": "User preferences and habits"}
                )
                self.knowledge = self.client.get_or_create_collection(
                    name="knowledge",
                    metadata={"description": "Learned knowledge about user's work"}
                )
                self.tasks = self.client.get_or_create_collection(
                    name="tasks",
                    metadata={"description": "Task patterns and workflows"}
                )
                return
            except Exception:
                self.client = None
                
        # Fallback in-memory collections
        self.conversations = FallbackCollection("conversations")
        self.preferences = FallbackCollection("preferences")
        self.knowledge = FallbackCollection("knowledge")
        self.tasks = FallbackCollection("tasks")
    
    async def store_conversation(
        self,
        user_input: str,
        assistant_response: str,
        metadata: Optional[Dict] = None
    ):
        """Store conversation with semantic embedding"""
        conversation_id = f"conv_{datetime.now().timestamp()}"
        self.conversations.add(
            documents=[
                f"User: {user_input}",
                f"Assistant: {assistant_response}"
            ],
            metadatas=[
                {"type": "user", "timestamp": datetime.now().isoformat(), **(metadata or {})},
                {"type": "assistant", "timestamp": datetime.now().isoformat(), **(metadata or {})}
            ],
            ids=[f"{conversation_id}_user", f"{conversation_id}_assistant"]
        )
    
    async def recall_similar_conversations(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar past conversations"""
        results = self.conversations.query(query_texts=[query], n_results=limit)
        if not results['documents'] or not results['documents'][0]:
            return []
        
        conversations = []
        for i, doc in enumerate(results['documents'][0]):
            dist = results['distances'][0][i] if 'distances' in results and results['distances'][0] else 0.5
            conversations.append({
                'content': doc,
                'metadata': results['metadatas'][0][i],
                'similarity': 1 - dist
            })
        return conversations
    
    async def learn_preference(
        self,
        category: str,
        preference: str,
        context: Optional[str] = None
    ):
        """Learn and store user preference"""
        pref_id = f"pref_{category}_{datetime.now().timestamp()}"
        self.preferences.add(
            documents=[preference],
            metadatas=[{
                "category": category,
                "context": context or "",
                "learned_at": datetime.now().isoformat(),
                "confidence": 1.0
            }],
            ids=[pref_id]
        )
    
    async def get_preferences(self, category: Optional[str] = None) -> List[Dict]:
        """Retrieve learned preferences"""
        if category:
            results = self.preferences.get(where={"category": category})
        else:
            results = self.preferences.get()
        
        if not results['documents']:
            return []
        
        preferences = []
        for i, doc in enumerate(results['documents']):
            preferences.append({
                'preference': doc,
                'metadata': results['metadatas'][i]
            })
        return preferences
    
    async def store_workflow_pattern(
        self,
        workflow_name: str,
        steps: List[str],
        trigger: Optional[str] = None,
        success_count: int = 0
    ):
        """Learn workflow patterns from user behavior"""
        workflow_id = f"workflow_{workflow_name.lower().replace(' ', '_')}"
        workflow_doc = f"Workflow: {workflow_name}\nTrigger: {trigger or 'manual'}\nSteps: {' -> '.join(steps)}"
        self.tasks.upsert(
            documents=[workflow_doc],
            metadatas=[{
                "name": workflow_name,
                "steps": json.dumps(steps),
                "trigger": trigger or "",
                "success_count": success_count,
                "last_executed": datetime.now().isoformat()
            }],
            ids=[workflow_id]
        )
    
    async def suggest_workflow(self, current_context: str) -> Optional[Dict]:
        """Suggest workflow based on current context"""
        results = self.tasks.query(query_texts=[current_context], n_results=1)
        if not results['documents'] or not results['documents'][0]:
            return None
        
        metadata = results['metadatas'][0][0]
        dist = results['distances'][0][0] if 'distances' in results and results['distances'][0] else 0.5
        return {
            'name': metadata['name'],
            'steps': json.loads(metadata['steps']),
            'trigger': metadata['trigger'],
            'confidence': 1 - dist,
            'success_count': metadata['success_count']
        }
    
    async def store_knowledge(
        self,
        topic: str,
        information: str,
        source: Optional[str] = None
    ):
        """Store learned knowledge about user's work/projects"""
        knowledge_id = f"know_{topic.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        self.knowledge.add(
            documents=[information],
            metadatas=[{
                "topic": topic,
                "source": source or "user",
                "stored_at": datetime.now().isoformat()
            }],
            ids=[knowledge_id]
        )
    
    async def query_knowledge(self, question: str, limit: int = 3) -> List[Dict]:
        """Query stored knowledge"""
        results = self.knowledge.query(query_texts=[question], n_results=limit)
        if not results['documents'] or not results['documents'][0]:
            return []
        
        knowledge = []
        for i, doc in enumerate(results['documents'][0]):
            dist = results['distances'][0][i] if 'distances' in results and results['distances'][0] else 0.5
            knowledge.append({
                'information': doc,
                'metadata': results['metadatas'][0][i],
                'relevance': 1 - dist
            })
        return knowledge
    
    def clear_all_memory(self):
        """Clear all stored memory"""
        self.__init__(self.persist_directory)
