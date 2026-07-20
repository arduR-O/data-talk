import os
import socket

# Set application-wide default socket timeout to prevent offline API hangs
socket.setdefaulttimeout(15.0)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
from routes.chat_routes import router as chat_router

app = FastAPI(
    title="DataTalk API",
    description="Complete API for DataTalk - Authentication and AI Chat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

@app.get("/")
async def root():
    return {
        "message": "DataTalk API Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    import os
    
    # 1. Database check (SQLite / MongoDB fallback)
    db_status = "operational"
    try:
        from models.chat_history import ChatHistoryModel
        history = ChatHistoryModel()
        if history.use_sqlite:
            import sqlite3
            conn = sqlite3.connect(history.sqlite_path)
            conn.cursor().execute("SELECT 1")
            conn.close()
        else:
            history.client.admin.command('ping')
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. LLM check (Groq)
    llm_status = "operational"
    try:
        from utils.llm_client import get_llm
        get_llm()
        if not os.getenv("GROQ_API_KEY"):
            llm_status = "error: GROQ_API_KEY environment variable missing"
    except Exception as e:
        llm_status = f"error: {str(e)}"

    # 3. Vector store check (Pinecone)
    vector_status = "operational"
    try:
        if not os.getenv("PINECONE_API_KEY"):
            vector_status = "disabled: PINECONE_API_KEY not configured (RAG features unavailable)"
        else:
            from pinecone import Pinecone
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            pc.list_indexes()
    except Exception as e:
        vector_status = f"error: {str(e)}"

    overall_status = "healthy"
    if "error" in db_status or "error" in llm_status or "error" in vector_status:
        overall_status = "unhealthy"

    return {
        "status": overall_status, 
        "services": {
            "database": db_status,
            "llm": llm_status,
            "vector_store": vector_status
        }
    }

@app.get("/api/status")
async def api_status():
    return {
        "message": "DataTalk API is operational",
        "endpoints": {
            "auth": {
                "signup": "POST /api/auth/signup",
                "login": "POST /api/auth/login", 
                "verify": "GET /api/auth/verify"
            },
            "chat": {
                "chat": "POST /api/chat"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )