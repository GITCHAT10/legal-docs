import hashlib
import re
from typing import List, Dict, Any

class KnowledgeCore:
    """
    SKY-i KNOWLEDGE CORE: Ingests and indexes NEXUS operational DNA.
    Parse → Chunk → Embed → Index
    """
    def __init__(self):
        self.index: Dict[str, Dict[str, Any]] = {}

    def ingest(self, source: str, content: str):
        """Full ingestion pipeline."""
        chunks = self.parse_document(source, content)
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{source}_{i}_{chunk[:20]}".encode()).hexdigest()
            embedding = self._generate_embedding(chunk)

            self.index[chunk_id] = {
                "source": source,
                "text": chunk,
                "embedding": embedding
            }

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Vector-simulated retrieval logic using embeddings."""
        query_embedding = self._generate_embedding(query_text)
        results = []

        for item in self.index.values():
            score = self._cosine_similarity(query_embedding, item["embedding"])
            # Boost score based on keyword match for "production feel"
            if any(word in item["text"].lower() for word in query_text.lower().split()):
                score += 0.5

            results.append({"text": item["text"], "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Mock cosine similarity."""
        return sum(x*y for x,y in zip(v1, v2))

    def parse_document(self, source: str, content: str) -> List[str]:
        """Cleans and chunks document content."""
        clean_content = re.sub(r'\s+', ' ', content).strip()
        return self._chunk_text(clean_content)

    def _chunk_text(self, text: str, size: int = 500, overlap: int = 50) -> List[str]:
        chunks = []
        if not text: return chunks
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start += size - overlap
        return chunks

    def _generate_embedding(self, text: str) -> List[float]:
        """Mock embedding generation for MNOS Core compatibility."""
        return [0.1] * 128

knowledge_core = KnowledgeCore()
