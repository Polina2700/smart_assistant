"""
NovaTech Smart Assistant — FastAPI Application
"""

import os
import time
import logging
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.services.rag import RAGService
from app.services.generator import GeneratorService

load_dotenv()

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="NovaTech Smart Assistant",
    description="AI-powered knowledge base assistant for NovaTech Consulting",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

DB_PATH = Path(__file__).parent.parent / "chat_logs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            sources TEXT,
            confidence TEXT,
            latency_ms INTEGER,
            language TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_log_id INTEGER NOT NULL,
            rating TEXT NOT NULL,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON chat_logs(session_id)")
    conn.commit()
    conn.close()

def log_chat(session_id, question, answer, sources, confidence, latency_ms, language):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO chat_logs (timestamp, session_id, question, answer, sources, confidence, latency_ms, language) VALUES (?,?,?,?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(),
                session_id, question, answer,
                json.dumps(sources), confidence, latency_ms, language,
            )
        )
        log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        return log_id
    except Exception as e:
        logger.error(f"DB log failed: {e}")
        return 0

# ─────────────────────────────────────────────
# SERVICES
# ─────────────────────────────────────────────

rag = RAGService()
generator = GeneratorService()

@app.on_event("startup")
async def startup():
    init_db()
    rag.initialize()
    stats = rag.get_stats()
    logger.info(f"RAG ready: {stats}")

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    language: Optional[str] = "English"

class ChatResponse(BaseModel):
    response: str
    sources: List[dict]
    log_id: int
    session_id: str
    confidence: str

class FeedbackRequest(BaseModel):
    log_id: int
    rating: str
    comment: Optional[str] = None

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    frontend = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if frontend.exists():
        return FileResponse(frontend)
    return {"message": "NovaTech Smart Assistant API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    stats = rag.get_stats()
    return {
        "status": "healthy" if rag.is_ready else "initializing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rag": stats,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start = time.time()
    session_id = request.session_id or "default"
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"[{session_id}] Q: {message[:80]}")

    # Simple query check (greetings, small talk)
    if generator.is_simple_query(message):
        answer = generator.generate_simple_response(message, request.language)
        latency = int((time.time() - start) * 1000)
        log_id = log_chat(session_id, message, answer, [], "simple", latency, request.language)
        return ChatResponse(
            response=answer,
            sources=[],
            log_id=log_id,
            session_id=session_id,
            confidence="simple",
        )

    # Retrieve relevant chunks
    chunks = rag.search(message, top_k=8)
    logger.info(f"[{session_id}] Retrieved {len(chunks)} chunks")

    # Generate answer
    result = generator.generate(
        query=message,
        context_chunks=chunks,
        session_id=session_id,
        language=request.language,
    )

    latency = int((time.time() - start) * 1000)
    logger.info(f"[{session_id}] Latency: {latency}ms | Confidence: {result['confidence']}")

    log_id = log_chat(
        session_id, message,
        result["answer"], result["sources"],
        result["confidence"], latency, request.language,
    )

    return ChatResponse(
        response=result["answer"],
        sources=result["sources"],
        log_id=log_id,
        session_id=session_id,
        confidence=result["confidence"],
    )


@app.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str, limit: int = 10):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT question, answer, timestamp FROM chat_logs WHERE session_id=? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        conn.close()

        history = [
            {"question": q, "answer": a, "timestamp": t}
            for q, a, t in reversed(rows)
        ]
        return {"session_id": session_id, "history": history, "message_count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    generator.clear_history(session_id)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM chat_logs WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB clear failed: {e}")
    return {"status": "success", "session_id": session_id}


@app.post("/api/feedback")
async def feedback(request: FeedbackRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO feedback (chat_log_id, rating, comment) VALUES (?,?,?)",
            (request.log_id, request.rating, request.comment)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        total = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        avg_latency = conn.execute("SELECT AVG(latency_ms) FROM chat_logs").fetchone()[0] or 0
        by_confidence = dict(conn.execute(
            "SELECT confidence, COUNT(*) FROM chat_logs GROUP BY confidence"
        ).fetchall())
        by_language = dict(conn.execute(
            "SELECT language, COUNT(*) FROM chat_logs GROUP BY language"
        ).fetchall())
        conn.close()

        return {
            "total_queries": total,
            "avg_latency_ms": round(avg_latency, 1),
            "by_confidence": by_confidence,
            "by_language": by_language,
            "rag": rag.get_stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Static files for frontend
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")