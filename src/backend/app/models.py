from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: Optional[str] = "English"

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict]
    log_id: int
    session_id: str
    session_cleared: bool = False

class FeedbackRequest(BaseModel):
    log_id: int
    rating: str  # "thumbs_up" or "thumbs_down"
    comment: Optional[str] = None
    improvement_suggestion: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class SearchResponse(BaseModel):
    results: List[Dict]
    total_results: int
    query: str

# Internal models
class ConversationContext(BaseModel):
    session_id: str
    history: List[Dict]
    created_at: datetime
    last_activity: datetime

class SearchResult(BaseModel):
    title: str
    content: str
    source: str
    confidence: float