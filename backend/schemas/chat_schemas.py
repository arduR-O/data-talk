from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = 'default'

class ChatResponse(BaseModel):
    response: str
    routing: Optional[str] = None
    debug_logs: Optional[list] = None

class DatabaseUrlRequest(BaseModel):
    db_url: str

class DatabaseUrlResponse(BaseModel):
    message: str
    db_url: str