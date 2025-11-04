from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    response: str

class DatabaseUrlRequest(BaseModel):
    db_url: str

class DatabaseUrlResponse(BaseModel):
    message: str
    db_url: str