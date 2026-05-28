"""
RAG Service — Hybrid Search (TF-IDF + Sentence Embeddings)
NovaTech Consulting Knowledge Base Assistant

Architecture:
1. TF-IDF retrieval — fast, exact keyword matching
2. Sentence embeddings retrieval — semantic similarity
3. Reciprocal Rank Fusion — combines both rankings
4. Gemini generation — answers in user's preferred language
"""

import os
import re
import math
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

# Documents folder: configurable via env, defaults to smart_assistant/documents/
_default_docs = Path(__file__).parent.parent.parent.parent.parent / "documents"
DOCS_DIR = Path(os.environ.get("DOCS_DIR", str(_default_docs)))

INDEX_DIR = Path(__file__).parent.parent.parent / "index"


# ─────────────────────────────────────────────
# 1. DOCUMENT LOADING & CHUNKING
# ─────────────────────────────────────────────

def load_documents() -> List[Dict]:
    """Load all documents from corpus directory."""
    docs = []
    if not DOCS_DIR.exists():
        logger.warning(f"Documents directory not found: {DOCS_DIR}")
        return docs

    for path in sorted(DOCS_DIR.rglob("*")):
        if path.suffix not in (".md", ".txt", ".csv"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            doc_type = path.parent.name

            if path.suffix == ".csv":
                csv_lines = text.strip().split("\n")
                if len(csv_lines) > 1:
                    headers = csv_lines[0]
                    chunks = []
                    idx = 0
                    for line in csv_lines[1:]:
                        if line.strip() and not line.startswith("Project,Client"):
                            chunk_text_content = f"{headers}\n{line}"
                            chunks.append({
                                "chunk_id": f"{path.stem}_c{idx}",
                                "doc_id": path.stem,
                                "text": chunk_text_content,
                                "start_word": idx,
                                "filename": path.name,
                                "type": doc_type,
                            })
                            idx += 1
                else:
                    chunks = chunk_text(text, path.stem)
                    for chunk in chunks:
                        chunk["filename"] = path.name
                        chunk["type"] = doc_type
            else:
                chunks = chunk_text(text, path.stem)
                for chunk in chunks:
                    chunk["filename"] = path.name
                    chunk["type"] = doc_type

            docs.append({
                "id": path.stem,
                "filename": path.name,
                "path": str(path.relative_to(DOCS_DIR.parent)),
                "type": doc_type,
                "text": text,
                "chunks": chunks,
            })
        except Exception as e:
            logger.warning(f"Could not read {path}: {e}")

    logger.info(f"Loaded {len(docs)} documents from {DOCS_DIR}")
    return docs


def chunk_text(text: str, doc_id: str, chunk_size: int = 200, overlap: int = 40) -> List[Dict]:
    """Split document into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    idx = 0
    while i < len(words):
        chunk_words = words[i: i + chunk_size]
        chunks.append({
            "chunk_id": f"{doc_id}_c{idx}",
            "doc_id": doc_id,
            "text": " ".join(chunk_words),
            "start_word": i,
            "filename": "",
            "type": "",       
        })
        i += chunk_size - overlap
        idx += 1
    return chunks


# ─────────────────────────────────────────────
# 2. TF-IDF INDEX
# ─────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, alphanumeric only."""
    return re.findall(r"[a-z0-9]+", text.lower())


def build_tfidf_index(docs: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Build TF-IDF index over all chunks."""
    all_chunks = []
    for doc in docs:
        all_chunks.extend(doc["chunks"])

    N = len(all_chunks)
    df: Dict[str, int] = Counter()

    for chunk in all_chunks:
        terms = set(tokenize(chunk["text"]))
        for t in terms:
            df[t] += 1

    idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    for chunk in all_chunks:
        tokens = tokenize(chunk["text"])
        tf = Counter(tokens)
        total = len(tokens) or 1
        chunk["tfidf"] = {
            t: (tf[t] / total) * idf.get(t, 0)
            for t in tf
        }

    return all_chunks, idf


def tfidf_search(query: str, all_chunks: List[Dict], idf: Dict, top_k: int = 10) -> List[Tuple[float, Dict]]:
    """Search using TF-IDF cosine similarity."""
    q_tokens = tokenize(query)
    q_tf = Counter(q_tokens)
    total_q = len(q_tokens) or 1
    q_vec = {t: (q_tf[t] / total_q) * idf.get(t, 0) for t in q_tf if t in idf}

    scores = []
    for chunk in all_chunks:
        c_vec = chunk["tfidf"]
        dot = sum(q_vec.get(t, 0) * c_vec.get(t, 0) for t in q_vec)
        norm_q = math.sqrt(sum(v ** 2 for v in q_vec.values())) or 1
        norm_c = math.sqrt(sum(v ** 2 for v in c_vec.values())) or 1
        score = dot / (norm_q * norm_c)
        scores.append((score, chunk))

    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:top_k]


# ─────────────────────────────────────────────
# 3. EMBEDDINGS INDEX
# ─────────────────────────────────────────────

class EmbeddingIndex:
    """Semantic search using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        self.chunk_embeddings = None
        self.chunks_ref: List[Dict] = []
        self.model_name = model_name

    def build(self, all_chunks: List[Dict]):
        """Build embedding index."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np

            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

            texts = [c["text"] for c in all_chunks]
            logger.info(f"Encoding {len(texts)} chunks...")
            self.chunk_embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            self.chunks_ref = all_chunks
            logger.info("Embedding index built successfully")

        except Exception as e:
            logger.warning(f"Embedding index failed: {e}. Will use TF-IDF only.")
            self.model = None

    def search(self, query: str, top_k: int = 10) -> List[Tuple[float, Dict]]:
        """Search using cosine similarity of embeddings."""
        if self.model is None or self.chunk_embeddings is None:
            return []

        try:
            import numpy as np
            q_emb = self.model.encode([query], normalize_embeddings=True)[0]
            scores = self.chunk_embeddings @ q_emb
            top_indices = np.argsort(scores)[::-1][:top_k]
            return [(float(scores[i]), self.chunks_ref[i]) for i in top_indices]
        except Exception as e:
            logger.warning(f"Embedding search failed: {e}")
            return []


# ─────────────────────────────────────────────
# 4. RECIPROCAL RANK FUSION
# ─────────────────────────────────────────────

def reciprocal_rank_fusion(
    tfidf_results: List[Tuple[float, Dict]],
    embed_results: List[Tuple[float, Dict]],
    k: int = 60,
    tfidf_weight: float = 0.5,
    embed_weight: float = 0.5,
    top_k: int = 5
) -> List[Dict]:
    """
    Combine TF-IDF and embedding results using Reciprocal Rank Fusion.
    RRF score = sum(weight / (k + rank))
    """
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, Dict] = {}

    for rank, (_, chunk) in enumerate(tfidf_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + tfidf_weight / (k + rank + 1)
        chunk_map[cid] = chunk

    for rank, (_, chunk) in enumerate(embed_results):
        cid = chunk["chunk_id"]
        scores[cid] = scores.get(cid, 0) + embed_weight / (k + rank + 1)
        chunk_map[cid] = chunk

    # Sort by RRF score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Deduplicate: max 2 chunks per document
    seen: Dict[str, int] = {}
    results = []
    for cid in sorted_ids:
        chunk = chunk_map[cid]
        doc_id = chunk["doc_id"]
        if seen.get(doc_id, 0) < 2:
            chunk["rrf_score"] = round(scores[cid], 6)
            results.append(chunk)
            seen[doc_id] = seen.get(doc_id, 0) + 1
        if len(results) >= top_k:
            break

    return results


# ─────────────────────────────────────────────
# 5. MAIN RAG CLASS
# ─────────────────────────────────────────────

class RAGService:
    """
    Hybrid RAG: TF-IDF + Sentence Embeddings + RRF fusion.
    """

    def __init__(self):
        self.docs: List[Dict] = []
        self.all_chunks: List[Dict] = []
        self.idf: Dict = {}
        self.embedding_index = EmbeddingIndex()
        self._ready = False

    def initialize(self):
        """Load documents and build both indexes."""
        logger.info("Initializing RAG service...")

        self.docs = load_documents()
        if not self.docs:
            logger.error("No documents loaded!")
            return

        current_hash = self._get_docs_hash()
        if self._load_index(current_hash):
            logger.info("Loading index from cache")
        else:
            logger.info("Building fresh index (documents changed)")
            self.all_chunks, self.idf = build_tfidf_index(self.docs)
            logger.info(f"TF-IDF index: {len(self.all_chunks)} chunks")
            self.embedding_index.build(self.all_chunks)
            self._save_index(current_hash)

        self._ready = True
        logger.info("RAG service ready")

    def _get_docs_hash(self) -> str:
        h = hashlib.md5()
        for path in sorted(DOCS_DIR.rglob("*")):
            if path.suffix in (".md", ".txt", ".csv"):
                h.update(path.name.encode())
                h.update(str(path.stat().st_mtime).encode())
        return h.hexdigest()

    def _save_index(self, current_hash: str):
        try:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            with open(INDEX_DIR / "chunks.pkl", "wb") as f:
                pickle.dump(self.all_chunks, f)
            with open(INDEX_DIR / "idf.pkl", "wb") as f:
                pickle.dump(self.idf, f)
            if self.embedding_index.chunk_embeddings is not None:
                import numpy as np
                np.save(str(INDEX_DIR / "embeddings.npy"), self.embedding_index.chunk_embeddings)
            (INDEX_DIR / "docs_hash.txt").write_text(current_hash)
            logger.info(f"Index saved to cache ({len(self.all_chunks)} chunks)")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def _load_index(self, current_hash: str) -> bool:
        hash_file = INDEX_DIR / "docs_hash.txt"
        if not hash_file.exists():
            return False
        if hash_file.read_text().strip() != current_hash:
            return False
        required = [INDEX_DIR / "chunks.pkl", INDEX_DIR / "idf.pkl"]
        if not all(f.exists() for f in required):
            return False
        try:
            with open(INDEX_DIR / "chunks.pkl", "rb") as f:
                self.all_chunks = pickle.load(f)
            with open(INDEX_DIR / "idf.pkl", "rb") as f:
                self.idf = pickle.load(f)
            emb_file = INDEX_DIR / "embeddings.npy"
            if emb_file.exists():
                import numpy as np
                from sentence_transformers import SentenceTransformer
                self.embedding_index.model = SentenceTransformer(self.embedding_index.model_name)
                self.embedding_index.chunk_embeddings = np.load(str(emb_file))
                self.embedding_index.chunks_ref = self.all_chunks
            logger.info(f"Loaded {len(self.all_chunks)} chunks from cache")
            return True
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Hybrid search: TF-IDF + embeddings → RRF fusion.

        Returns list of chunks with metadata.
        """
        if not self._ready:
            logger.warning("RAG service not initialized")
            return []

        # TF-IDF search
        tfidf_results = tfidf_search(query, self.all_chunks, self.idf, top_k=15)

        # Embedding search
        embed_results = self.embedding_index.search(query, top_k=15)

        # Fuse results
        if embed_results:
            # Both available — true hybrid
            fused = reciprocal_rank_fusion(
                tfidf_results, embed_results,
                tfidf_weight=0.4, embed_weight=0.6,
                top_k=top_k
            )
        else:
            # Fallback to TF-IDF only
            fused = [chunk for _, chunk in tfidf_results[:top_k]]

        return fused

    def get_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string for LLM."""
        if not chunks:
            return ""

        parts = []
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get("rrf_score", 0)
            parts.append(
                f"[Source {i}: {chunk['filename']} | type: {chunk['type']} | score: {score}]\n"
                f"{chunk['text']}"
            )
        return "\n\n---\n\n".join(parts)

    @property
    def is_ready(self) -> bool:
        return self._ready

    def get_stats(self) -> Dict:
        return {
            "documents": len(self.docs),
            "chunks": len(self.all_chunks),
            "embedding_model": self.embedding_index.model_name if self.embedding_index.model else None,
            "hybrid_search": self.embedding_index.model is not None,
        }