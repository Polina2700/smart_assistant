import sqlite3
import json
import csv
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for chat logs and feedback"""
    
    def __init__(self, db_path: str = "chat_logs.db"):
        self.db_path = db_path
        self.init_database()
        self._init_sheets()

    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Chat logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    used_sources TEXT,
                    latency_ms INTEGER,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_log_id INTEGER NOT NULL,
                    rating TEXT NOT NULL,
                    comment TEXT,
                    improvement_suggestion TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_log_id) REFERENCES chat_logs (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON chat_logs(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_log_id ON feedback(chat_log_id)")
            
            # Add new columns to existing databases (safe migration)
            for col_ddl in [
                "ALTER TABLE chat_logs ADD COLUMN relevance_score REAL",
                "ALTER TABLE chat_logs ADD COLUMN conversation_type TEXT",
            ]:
                try:
                    cursor.execute(col_ddl)
                except Exception:
                    pass  # Column already exists

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        
    def _init_sheets(self):
        """Initialize Google Sheets client"""
        try:
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not creds_path:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, Sheets disabled")
                self.sheets_service = None
                return
        
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self.sheets_service = build("sheets", "v4", credentials=creds)
            self.spreadsheet_id = "1tZDaOyZzq3Egdn7TP_WIpnNyODU1_d4qUapoGgz8IwY"
            logger.info("Google Sheets integration initialized")
        except Exception as e:
            logger.warning(f"Google Sheets init failed: {e}")
            self.sheets_service = None

    _executor = ThreadPoolExecutor(max_workers=2)

    def log_chat(
        self,
        session_id: str,
        question: str,
        answer: str,
        used_sources: List[Dict],
        latency_ms: int,
        user_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        relevance_score: Optional[float] = None,
        conversation_type: Optional[str] = None
    ) -> int:
        """Log chat interaction and return log ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.now(timezone.utc).isoformat()
            sources_json = json.dumps(used_sources)

            cursor.execute("""
                INSERT INTO chat_logs
                (timestamp, user_id, session_id, question, answer, used_sources, latency_ms, status, error_message, relevance_score, conversation_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, user_id, session_id, question, answer, sources_json, latency_ms, status, error_message, relevance_score, conversation_type))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            try:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(
                    self._executor,
                    lambda: self._log_to_sheets(
                        log_id=log_id,
                        timestamp=timestamp,
                        session_id=session_id,
                        question=question,
                        answer=answer,
                        latency_ms=latency_ms,
                        relevance_score=relevance_score or 0.0,
                        conversation_type=conversation_type or "",
                        used_sources=used_sources,
                        error_message=error_message
                )
            )
            except RuntimeError:
                self._log_to_sheets(
                    log_id=log_id,
                    timestamp=timestamp,
                    session_id=session_id,
                    question=question,
                    answer=answer,
                    latency_ms=latency_ms,
                    relevance_score=relevance_score or 0.0,
                    conversation_type=conversation_type or "",
                    used_sources=used_sources,
                    error_message=error_message
                )
            
            logger.debug(f"Logged chat interaction - ID: {log_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log chat: {e}")
            # Return a temporary ID to avoid breaking the API response
            return 0
        
    def _log_to_sheets(self, log_id: int, timestamp: str, session_id: str,
                   question: str, answer: str, latency_ms: int,
                   relevance_score: float, conversation_type: str, used_sources: list = None, error_message: str = None):
        """Append a row to Google Sheets asynchronously"""
        if not self.sheets_service:
            return
        try:
            # Truncate answer to 2000 chars for readability
            short_answer = (answer or "")[:2000]
            values = [[
                log_id,                                                          # A - ID
                datetime.fromisoformat(timestamp).strftime("%d.%m.%Y %H:%M"),  # B - Timestamp
                session_id,                                                      # C - Session ID
                question,                                                        # D - Question
                short_answer,                                                    # E - Answer
                latency_ms,                                                      # F - Latency
                round(relevance_score, 3) if relevance_score else "",           # G - Relevance Score
                conversation_type or "",                                         # H - Conversation Type
                "",  # I - Rating
                "",  # J - User Comment
                "",  # K - Moderator Status
                "",  # L - Moderator Notes
                json.dumps(used_sources)[:500] if used_sources else "",         # M - Sources
                error_message or "",                                             # N - Error Message
            ]]
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Q&A!A:N",
                valueInputOption="RAW",
                body={"values": values}
            ).execute()
            logger.debug(f"Logged to Sheets: row {log_id}")
        except Exception as e:
            logger.warning(f"Sheets logging failed (non-critical): {e}")

    def _update_sheets_rating(self, chat_log_id: int, rating: str, comment: Optional[str] = None):
        """Find row by chat_log_id in column A and update rating in column I, comment in column J"""
        if not self.sheets_service:
            return
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Q&A!A:A"
            ).execute()
            rows = result.get("values", [])
            for i, row in enumerate(rows):
                if row and str(row[0]) == str(chat_log_id):
                    cell_range = f"Q&A!I{i + 1}:J{i + 1}"
                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=cell_range,
                        valueInputOption="RAW",
                        body={"values": [[rating, comment or ""]]}
                    ).execute()
                    logger.debug(f"Updated Sheets rating for log {chat_log_id} at row {i + 1}")
                    return
            logger.warning(f"chat_log_id {chat_log_id} not found in Sheets column A")
        except Exception as e:
            logger.warning(f"Sheets rating update failed (non-critical): {e}")

    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get conversation history for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT question, answer, timestamp 
                FROM chat_logs 
                WHERE session_id = ? AND status = 'success'
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Reverse to get chronological order and format
            history = []
            for question, answer, timestamp in reversed(rows):
                history.append({
                    "question": question,
                    "answer": answer,
                    "timestamp": timestamp
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM chat_logs WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared history for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear conversation history: {e}")
            raise

    def add_feedback(
        self,
        chat_log_id: int,
        rating: str,
        comment: Optional[str] = None,
        improvement_suggestion: Optional[str] = None
    ):
        """Add feedback for a chat response"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO feedback (chat_log_id, rating, comment, improvement_suggestion)
                VALUES (?, ?, ?, ?)
            """, (chat_log_id, rating, comment, improvement_suggestion))
            
            conn.commit()
            conn.close()

            self._update_sheets_rating(chat_log_id, rating, comment)
            logger.debug(f"Added feedback for log {chat_log_id}")

        except Exception as e:
            logger.error(f"Failed to add feedback: {e}")
            raise

    def get_chat_stats(self) -> Dict:
        """Get chat usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute("SELECT COUNT(*) FROM chat_logs")
            total_queries = cursor.fetchone()[0]
            
            # Successful queries
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE status = 'success'")
            successful_queries = cursor.fetchone()[0]
            
            # Average latency
            cursor.execute("SELECT AVG(latency_ms) FROM chat_logs WHERE status = 'success'")
            avg_latency = cursor.fetchone()[0] or 0
            
            # Feedback statistics
            cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")
            feedback_stats = {rating: count for rating, count in cursor.fetchall()}
            
            # Recent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM chat_logs 
                WHERE datetime(timestamp) > datetime('now', '-1 day')
            """)
            daily_activity = cursor.fetchone()[0]
            
            # Popular sessions
            cursor.execute("""
                SELECT session_id, COUNT(*) as message_count 
                FROM chat_logs 
                GROUP BY session_id 
                ORDER BY message_count DESC 
                LIMIT 5
            """)
            popular_sessions = [{"session_id": sid, "count": count} for sid, count in cursor.fetchall()]
            
            conn.close()
            
            return {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": round((successful_queries / total_queries * 100), 2) if total_queries > 0 else 0,
                "avg_latency_ms": round(avg_latency, 2),
                "daily_activity": daily_activity,
                "feedback": feedback_stats,
                "popular_sessions": popular_sessions
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def export_conversations_to_csv(self, filename: str = "conversations_export.csv") -> str:
        """Export all conversations to CSV"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT
                    cl.id, cl.timestamp, cl.session_id, cl.user_id,
                    cl.question, cl.answer, cl.latency_ms, cl.relevance_score, cl.conversation_type, cl.status,
                    f.rating, f.comment, f.improvement_suggestion
                FROM chat_logs cl
                LEFT JOIN feedback f ON cl.id = f.chat_log_id
                ORDER BY cl.timestamp DESC
            """)

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ID', 'Timestamp', 'Session ID', 'User ID',
                    'Question', 'Answer', 'Latency (ms)', 'Relevance Score', 'Conversation Type', 'Status',
                    'Rating', 'Comment', 'Improvement Suggestion'
                ])
                writer.writerows(cursor.fetchall())
            
            conn.close()
            logger.info(f"Exported conversations to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export conversations: {e}")
            raise