import os
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
    return {
        "status": "healthy", 
        "services": {
            "authentication": "operational",
            "chat": "operational"
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