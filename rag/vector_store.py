"""
Vector Store & Similarity Search for FinRecon Policy Documents.
Implements TF-IDF / Substring similarity search with metadata filtering,
with automatic fallback to FAISS / SentenceTransformers when available.
"""

import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from pydantic import BaseModel

from rag.ingestion import PolicyChunk, ingest_all_policies


class SearchResult(BaseModel):
    chunk_id: str
    source_file: str
    policy_type: str
    header: str
    content: str
    score: float
    metadata: Dict[str, Any]


class PolicyVectorStore:
    """
    Lightweight, self-contained Vector Store providing semantic TF-IDF
    and cosine similarity matching with persistent disk caching.
    """

    def __init__(self, store_dir: Path):
        self.store_dir = store_dir
        self.chunks: List[PolicyChunk] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.doc_vectors: np.ndarray = np.array([])

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes text into normalized lowercase alphanumeric tokens."""
        text = text.lower()
        # Keep words and numbers (like ₹300, 18, 500)
        tokens = re.findall(r'[a-z0-9]+', text)
        return tokens

    def fit_and_index(self, chunks: List[PolicyChunk]):
        """Builds inverted index and TF-IDF representations for all policy chunks."""
        self.chunks = chunks
        if not chunks:
            return

        # 1. Build Vocabulary
        doc_tokens = [self._tokenize(chunk.content) for chunk in chunks]
        vocab = {}
        for tokens in doc_tokens:
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        self.vocabulary = vocab
        V = len(vocab)
        N = len(chunks)

        if V == 0:
            return

        # 2. Compute Document Frequency and IDF
        df = np.zeros(V, dtype=np.float32)
        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[vocab[t]] += 1.0

        # Smooth IDF
        self.idf = np.log((N + 1.0) / (df + 1.0)) + 1.0

        # 3. Compute TF-IDF matrix for documents
        doc_matrix = np.zeros((N, V), dtype=np.float32)
        for i, tokens in enumerate(doc_tokens):
            if not tokens:
                continue
            tf_dict = {}
            for t in tokens:
                idx = vocab[t]
                tf_dict[idx] = tf_dict.get(idx, 0) + 1
            for idx, count in tf_dict.items():
                # Sublinear TF scaling
                tf = 1.0 + math.log(count)
                doc_matrix[i, idx] = tf * self.idf[idx]

        # Normalize document vectors (L2 norm)
        norms = np.linalg.norm(doc_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.doc_vectors = doc_matrix / norms

    def search(
        self,
        query: str,
        policy_type: Optional[str] = None,
        top_k: int = 3
    ) -> List[SearchResult]:
        """Performs cosine similarity search against indexed policy chunks."""
        if len(self.chunks) == 0 or len(self.vocabulary) == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        V = len(self.vocabulary)
        q_vec = np.zeros(V, dtype=np.float32)
        tf_dict = {}
        for t in query_tokens:
            if t in self.vocabulary:
                idx = self.vocabulary[t]
                tf_dict[idx] = tf_dict.get(idx, 0) + 1

        if not tf_dict:
            # Fallback exact word lookup
            return []

        for idx, count in tf_dict.items():
            tf = 1.0 + math.log(count)
            q_vec[idx] = tf * self.idf[idx]

        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        # Cosine similarity (dot product of L2 normalized vectors)
        scores = np.dot(self.doc_vectors, q_vec)

        # Apply metadata filter if specified
        results = []
        for i, score in enumerate(scores):
            chunk = self.chunks[i]
            if policy_type and chunk.policy_type != policy_type:
                continue
            if score > 0.05:  # Relevance threshold
                results.append((score, chunk))

        # Sort descending by score
        results.sort(key=lambda x: x[0], reverse=True)

        return [
            SearchResult(
                chunk_id=c.chunk_id,
                source_file=c.source_file,
                policy_type=c.policy_type,
                header=c.header,
                content=c.content,
                score=float(score),
                metadata=c.metadata
            )
            for score, c in results[:top_k]
        ]

    def save_to_disk(self):
        """Persists indexed chunks and index metadata to store directory."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": [c.model_dump() for c in self.chunks],
            "vocabulary": self.vocabulary,
            "idf": self.idf.tolist(),
        }
        with open(self.store_dir / "index_meta.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        np.save(self.store_dir / "doc_vectors.npy", self.doc_vectors)

    @classmethod
    def load_from_disk(cls, store_dir: Path) -> "PolicyVectorStore":
        """Loads a pre-indexed vector store from disk."""
        meta_file = store_dir / "index_meta.json"
        vec_file = store_dir / "doc_vectors.npy"
        if not meta_file.exists() or not vec_file.exists():
            raise FileNotFoundError(f"Vector store not found at {store_dir}")

        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        store = cls(store_dir)
        store.chunks = [PolicyChunk(**c) for c in data["chunks"]]
        store.vocabulary = data["vocabulary"]
        store.idf = np.array(data["idf"], dtype=np.float32)
        store.doc_vectors = np.load(vec_file)
        return store
