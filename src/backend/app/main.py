"""
NovaTech Smart Assistant — FastAPI Application
"""

import os
import time
import logging
import sqlite3
import json
import html
import threading
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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
        if sheets_logger:
            sheets_logger.log_async([
                datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"),
                session_id, question, answer[:1000],
                confidence, latency_ms, language,
                json.dumps(sources)[:500], "", "", log_id,
            ])
        return log_id
    except Exception as e:
        logger.error(f"DB log failed: {e}")
        return 0

# ─────────────────────────────────────────────
# GOOGLE SHEETS LOGGER
# ─────────────────────────────────────────────

class SheetsLogger:
    HEADERS = [
        "Timestamp", "Session ID", "Question", "Answer",
        "Confidence", "Latency (ms)", "Language", "Sources",
        "Rating", "Comment", "Log ID",
    ]

    def __init__(self):
        self._ws = None
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            sheet_id = os.getenv("GOOGLE_SHEETS_ID")
            if not creds_path or not sheet_id:
                return
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)
            sh = client.open_by_key(sheet_id)
            try:
                self._ws = sh.worksheet("Conversations")
            except gspread.exceptions.WorksheetNotFound:
                self._ws = sh.add_worksheet("Conversations", rows=1000, cols=11)
            self.ensure_headers()
            logger.info("Google Sheets logger initialized")
        except Exception as e:
            logger.warning(f"Sheets logger init failed: {e}")
            self._ws = None

    def ensure_headers(self):
        try:
            if not self._ws.row_values(1):
                self._ws.append_row(self.HEADERS)
        except Exception as e:
            logger.warning(f"Sheets headers failed: {e}")

    def log(self, row_data: list):
        if self._ws is None:
            return
        try:
            self._ws.append_row(row_data, value_input_option="USER_ENTERED")
        except Exception as e:
            logger.warning(f"Sheets log failed: {e}")

    def log_async(self, row_data: list):
        threading.Thread(target=self.log, args=(row_data,), daemon=True).start()


# ─────────────────────────────────────────────
# SERVICES
# ─────────────────────────────────────────────

rag = RAGService()
generator = GeneratorService()
sheets_logger = SheetsLogger() if os.getenv("GOOGLE_SHEETS_ID") else None

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
        "admin": "/admin",
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


@app.get("/api/sheets/status")
async def sheets_status():
    return {
        "enabled": sheets_logger is not None and sheets_logger._ws is not None,
        "sheet_id": os.getenv("GOOGLE_SHEETS_ID"),
        "worksheet": "Conversations",
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin(page: int = 1, session: str = "", q: str = ""):
    PAGE_SIZE = 20

    def e(s):
        return html.escape(str(s) if s is not None else "")

    def conf_cls(c):
        return f"conf-{c}" if c in ("high", "medium", "low", "none", "simple") else "conf-none"

    try:
        conn = sqlite3.connect(DB_PATH)

        total = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        avg_lat = round(conn.execute("SELECT AVG(latency_ms) FROM chat_logs").fetchone()[0] or 0)
        by_conf = dict(conn.execute(
            "SELECT confidence, COUNT(*) FROM chat_logs GROUP BY confidence"
        ).fetchall())

        conditions, params = [], []
        if session:
            conditions.append("session_id = ?")
            params.append(session)
        if q:
            conditions.append("question LIKE ?")
            params.append(f"%{q}%")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        filtered_total = conn.execute(
            f"SELECT COUNT(*) FROM chat_logs {where}", params
        ).fetchone()[0]
        total_pages = max(1, (filtered_total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(1, min(page, total_pages))
        offset = (page - 1) * PAGE_SIZE

        rows = conn.execute(
            f"SELECT id, timestamp, session_id, question, answer, confidence, latency_ms, language "
            f"FROM chat_logs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [PAGE_SIZE, offset],
        ).fetchall()

        fb_rows = conn.execute(
            "SELECT chat_log_id, rating, comment FROM feedback ORDER BY id DESC LIMIT 200"
        ).fetchall()

        conn.close()
    except Exception as ex:
        return HTMLResponse(f"<pre>DB error: {html.escape(str(ex))}</pre>", status_code=500)

    # ── stats cards ───────────────────────────────────────────────────────────
    CONF_COLORS = {"high": "#1a7a1a", "medium": "#b86000"}
    stats_html = "".join(
        f'<div class="stat-card"><div class="val">{e(v)}</div><div class="lbl">{e(l)}</div></div>'
        for l, v in [("Total queries", total), ("Avg latency", f"{avg_lat} ms")]
    )
    for conf, count in sorted(by_conf.items()):
        color = CONF_COLORS.get(conf, "#c0392b")
        stats_html += (
            f'<div class="stat-card">'
            f'<div class="val" style="color:{color}">{count}</div>'
            f'<div class="lbl">{e(conf)}</div></div>'
        )

    # ── search form ───────────────────────────────────────────────────────────
    form_html = (
        f'<form method="get" action="/admin">'
        f'<input type="text" name="session" placeholder="Session ID" value="{e(session)}">'
        f'<input type="text" name="q" placeholder="Search question…" value="{e(q)}">'
        f'<button type="submit">Filter</button>'
        f'<a href="/admin" style="padding:6px 10px;color:#666">Reset</a>'
        f'<span style="margin-left:auto;color:#888;font-size:.85rem">{filtered_total} rows</span>'
        f'</form>'
    )

    # ── chat logs rows ────────────────────────────────────────────────────────
    log_rows_html = ""
    for row_id, ts, sess, question, answer, conf, lat, lang in rows:
        ts_short = (ts[:16].replace("T", " ")) if ts else ""
        q_text = (question or "")[:50] + ("…" if len(question or "") > 50 else "")
        a_text = (answer or "")[:80] + ("…" if len(answer or "") > 80 else "")
        log_rows_html += (
            f'<tr>'
            f'<td>{e(row_id)}</td>'
            f'<td style="white-space:nowrap">{e(ts_short)}</td>'
            f'<td><a href="/admin?session={e(sess)}">{e(sess)}</a></td>'
            f'<td title="{e(question)}">{e(q_text)}</td>'
            f'<td title="{e(answer)}">{e(a_text)}</td>'
            f'<td class="{conf_cls(conf)}">{e(conf)}</td>'
            f'<td style="text-align:right">{e(lat)}</td>'
            f'<td>{e(lang)}</td>'
            f'</tr>'
        )
    if not log_rows_html:
        log_rows_html = '<tr><td colspan="8" style="text-align:center;color:#aaa;padding:20px">No records</td></tr>'

    # ── pagination ────────────────────────────────────────────────────────────
    def page_url(p):
        parts = [f"page={p}"]
        if session:
            parts.append(f"session={html.escape(session)}")
        if q:
            parts.append(f"q={html.escape(q)}")
        return "/admin?" + "&amp;".join(parts)

    pagination_html = '<div class="pagination">'
    if page > 1:
        pagination_html += f'<a href="{page_url(page - 1)}">← Prev</a>'
    for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
        cls = ' class="active"' if p == page else ""
        pagination_html += f'<a href="{page_url(p)}"{cls}>{p}</a>'
    if page < total_pages:
        pagination_html += f'<a href="{page_url(page + 1)}">Next →</a>'
    pagination_html += (
        f'<span style="color:#999;font-size:.85rem;line-height:2.2">page {page} / {total_pages}</span>'
        f'</div>'
    )

    # ── feedback rows ─────────────────────────────────────────────────────────
    fb_html = ""
    for log_id, rating, comment in fb_rows:
        icon = "👍" if str(rating).lower() in ("up", "good", "positive", "👍", "thumbs_up") else "👎"
        fb_html += (
            f'<tr>'
            f'<td>{e(log_id)}</td>'
            f'<td>{icon} {e(rating)}</td>'
            f'<td>{e(comment or "")}</td>'
            f'</tr>'
        )
    if not fb_html:
        fb_html = '<tr><td colspan="3" style="text-align:center;color:#aaa;padding:20px">No feedback yet</td></tr>'

    # ── full page ─────────────────────────────────────────────────────────────
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin — NovaTech Assistant</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 24px 28px; background: #f4f4f4; color: #222; }}
    h1 {{ margin: 0 0 6px; font-size: 1.35rem; }}
    .sub {{ color: #888; font-size: .85rem; margin-bottom: 22px; }}
    h2 {{ font-size: .8rem; font-weight: 700; margin: 28px 0 10px; color: #666; text-transform: uppercase; letter-spacing: .07em; }}
    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    .stat-card {{ background: white; border-radius: 8px; padding: 12px 18px; min-width: 110px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    .stat-card .val {{ font-size: 1.6rem; font-weight: 700; line-height: 1.2; }}
    .stat-card .lbl {{ font-size: .72rem; color: #999; margin-top: 3px; text-transform: uppercase; letter-spacing: .04em; }}
    form {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    input[type=text] {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: .9rem; min-width: 170px; }}
    input[type=text]:focus {{ outline: none; border-color: #888; }}
    button {{ padding: 6px 14px; background: #222; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: .9rem; }}
    button:hover {{ background: #444; }}
    a {{ color: #0055cc; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .table-wrap {{ overflow-x: auto; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-top: 10px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; font-size: .84rem; }}
    th {{ background: #f0f0f0; padding: 9px 11px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; white-space: nowrap; }}
    td {{ padding: 7px 11px; border-bottom: 1px solid #f0f0f0; vertical-align: top; max-width: 320px; word-break: break-word; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #fafafa; }}
    .conf-high {{ color: #1a7a1a; font-weight: 600; }}
    .conf-medium {{ color: #b86000; font-weight: 600; }}
    .conf-low, .conf-none, .conf-simple {{ color: #c0392b; font-weight: 600; }}
    .pagination {{ display: flex; gap: 6px; align-items: center; margin-top: 12px; flex-wrap: wrap; }}
    .pagination a {{ padding: 4px 10px; background: white; border: 1px solid #ccc; border-radius: 4px; font-size: .85rem; }}
    .pagination a.active {{ background: #222; color: white; border-color: #222; pointer-events: none; }}
    .pagination a:hover:not(.active) {{ background: #eee; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>NovaTech Assistant — Admin</h1>
  <p class="sub"><a href="/">Chat UI</a> &nbsp;·&nbsp; <a href="/docs">API Docs</a> &nbsp;·&nbsp; <a href="/api/health">Health</a></p>

  <h2>Summary</h2>
  <div class="stats">{stats_html}</div>

  <h2>Chat Logs</h2>
  {form_html}
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>ID</th><th>Time (UTC)</th><th>Session</th><th>Question</th><th>Answer</th>
        <th>Confidence</th><th>Latency ms</th><th>Language</th>
      </tr></thead>
      <tbody>{log_rows_html}</tbody>
    </table>
  </div>
  {pagination_html}

  <h2>Feedback</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Log ID</th><th>Rating</th><th>Comment</th></tr></thead>
      <tbody>{fb_html}</tbody>
    </table>
  </div>
</body>
</html>"""

    return HTMLResponse(content=content)


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