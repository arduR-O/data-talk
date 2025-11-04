from fastapi import APIRouter, HTTPException, Header, File, UploadFile, BackgroundTasks
from controllers.chat_controller import ChatController
from controllers.auth_controller import AuthController
from schemas.chat_schemas import ChatRequest, ChatResponse, DatabaseUrlRequest, DatabaseUrlResponse
from services.vector_service import get_vector_service
from typing import List, Optional
from pathlib import Path
from datetime import datetime

router = APIRouter()
chat_controller = ChatController()
auth_controller = AuthController()


def get_user_id_from_token(authorization: str = Header(...)) -> str:
    """Extract and verify user_id from authorization token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = auth_controller.verify_token(token)
        user = auth_controller.user_model.find_user_by_id(payload['user_id'])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return payload['user_id']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_request: ChatRequest,
    authorization: str = Header(...)
):
    """
    Chat endpoint for AI responses - requires authentication.
    Uses user's chat history and custom database URL if configured.
    """
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.process_message(user_id, chat_request.question)
    
    if result['success']:
        return {
            "response": result['data']['response']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )


@router.get("/chat/history")
async def get_chat_history(authorization: str = Header(...)):
    """Get chat history for the authenticated user"""
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.get_history(user_id)
    
    if result['success']:
        return {
            "messages": result['data']['messages']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )


@router.delete("/chat/history")
async def clear_chat_history(authorization: str = Header(...)):
    """Clear chat history for the authenticated user"""
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.clear_history(user_id)
    
    if result['success']:
        return {
            "message": "Chat history cleared successfully",
            "deleted_count": result['data']['deleted_count']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )


@router.post("/database-url", response_model=DatabaseUrlResponse)
async def save_database_url(
    db_request: DatabaseUrlRequest,
    authorization: str = Header(...)
):
    """
    Save or update the database URL for the authenticated user.
    This allows users to connect their own databases for querying.
    """
    user_id = get_user_id_from_token(authorization)
    
    try:
        updated_user = auth_controller.user_model.update_db_url(user_id, db_request.db_url)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "Database URL saved successfully",
            "db_url": db_request.db_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-url")
async def get_database_url(authorization: str = Header(...)):
    """Get the configured database URL for the authenticated user"""
    user_id = get_user_id_from_token(authorization)
    
    try:
        db_url = auth_controller.user_model.get_db_url(user_id)
        if db_url:
            return {
                "db_url": db_url,
                "configured": True
            }
        else:
            return {
                "db_url": None,
                "configured": False,
                "message": "No database URL configured"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/uploadfiles/")
async def create_upload_files(
    background_tasks: BackgroundTasks,
    authorization: str = Header(...),
    files: List[UploadFile] = File(...)
):
    """
    Save uploaded files into context/<user_id>/ directory and vectorize them.
    
    Accepts multiple files via multipart/form-data.
    Files are streamed to disk and then vectorized in the background.
    
    Example:
        Form field name: 'files'
        Multiple files can be uploaded in a single request
    """
    user_id = get_user_id_from_token(authorization)
    
    # Go up from routes/ to backend/, then into context/
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    saved = []
    vectorization_tasks = []
    
    for upload in files:
        # Sanitize filename to avoid directory traversal
        filename = Path(upload.filename).name
        dest_path = uploads_dir / filename
        
        # Stream write to avoid loading entire file into memory
        with open(dest_path, "wb") as out_file:
            while True:
                chunk = await upload.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                out_file.write(chunk)
        
        saved.append({
            "filename": filename,
            "path": str(dest_path)
        })
        
        # Schedule vectorization in background
        vector_service = get_vector_service()
        background_tasks.add_task(
            vector_service.process_and_upload_document,
            user_id,
            str(dest_path),
            filename
        )
    
    return {
        "message": f"Successfully uploaded {len(saved)} file(s). Vectorization in progress.",
        "saved": saved,
        "note": "Documents are being processed in the background and will be available for search shortly."
    }


@router.get("/uploadfiles/")
async def list_uploaded_files(authorization: str = Header(...)):
    """List all uploaded files for the authenticated user"""
    user_id = get_user_id_from_token(authorization)
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    
    if not uploads_dir.exists():
        return {
            "files": [],
            "message": "No files uploaded yet"
        }
    
    files = []
    for file_path in uploads_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size
            })
    
    return {
        "files": files,
        "count": len(files)
    }


@router.delete("/uploadfiles/{filename}")
async def delete_uploaded_file(
    filename: str,
    authorization: str = Header(...)
):
    """Delete a specific uploaded file and its vector embeddings for the authenticated user"""
    user_id = get_user_id_from_token(authorization)
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    file_path = uploads_dir / Path(filename).name  # Sanitize filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_relative_to(uploads_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        # Delete from filesystem
        file_path.unlink()
        
        # Delete from vector store
        vector_service = get_vector_service()
        vector_result = vector_service.delete_document(user_id, filename)
        
        return {
            "message": f"File '{filename}' deleted successfully",
            "file_deleted": True,
            "vectors_deleted": vector_result.get("success", False),
            "vectors_count": vector_result.get("deleted_count", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vectors/status")
async def get_vector_status(authorization: str = Header(...)):
    """Get vectorization status for the authenticated user's documents"""
    user_id = get_user_id_from_token(authorization)
    
    try:
        vector_service = get_vector_service()
        
        # Get documents from filesystem
        base_dir = Path(__file__).resolve().parent.parent
        uploads_dir = base_dir / "context" / user_id
        
        fs_files = set()
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                    fs_files.add(file_path.name)
        
        # Get documents from vector store
        vector_files = set(vector_service.list_user_documents(user_id))
        
        # Compare
        vectorized = list(fs_files.intersection(vector_files))
        pending = list(fs_files - vector_files)
        orphaned = list(vector_files - fs_files)  # In vectors but not in filesystem
        
        return {
            "total_files": len(fs_files),
            "vectorized": {
                "count": len(vectorized),
                "files": vectorized
            },
            "pending_vectorization": {
                "count": len(pending),
                "files": pending
            },
            "orphaned_vectors": {
                "count": len(orphaned),
                "files": orphaned,
                "note": "These exist in vector store but not in filesystem"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(authorization: str = Header(...)):
    """
    Get complete dashboard information for the authenticated user:
    - Database connection status
    - Uploaded files
    - Chat history count
    """
    user_id = get_user_id_from_token(authorization)
    
    try:
        # Get database URL
        db_url = auth_controller.user_model.get_db_url(user_id)
        
        # Get uploaded files
        base_dir = Path(__file__).resolve().parent.parent
        uploads_dir = base_dir / "context" / user_id
        
        files = []
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file():
                    files.append({
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "uploaded_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        # Get chat history count
        history_result = chat_controller.get_history(user_id)
        chat_count = len(history_result['data']['messages']) if history_result['success'] else 0
        
        return {
            "database": {
                "connected": db_url is not None,
                "url": db_url if db_url else None
            },
            "files": {
                "count": len(files),
                "items": files
            },
            "chat": {
                "message_count": chat_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))