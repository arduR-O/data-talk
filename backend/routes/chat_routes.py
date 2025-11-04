from fastapi import APIRouter, HTTPException, Header
from controllers.chat_controller import ChatController
from schemas.chat_schemas import ChatRequest, ChatResponse, DatabaseUrlRequest, DatabaseUrlResponse
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from pathlib import Path
from controllers.auth_controller import AuthController

app = FastAPI()
auth_controller = AuthController()

router = APIRouter()
chat_controller = ChatController()

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
    authorization: Optional[str] = Header(None)
):
    """Chat endpoint for AI responses"""
    user_id = None
    if authorization:
        try:
            user_id = get_user_id_from_token(authorization)
        except HTTPException:
            # If token is invalid, continue without user_id (for backward compatibility)
            pass
    
    result = chat_controller.process_message(chat_request.question, user_id=user_id)
    
    if result['success']:
        return {
            "response": result['data']['response']
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
    """Save or update the database URL for the authenticated user"""
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

@router.post("/uploadfiles/")
async def create_upload_files(authorization: str = Header(...), files: List[UploadFile] = File(...)):
    """Save uploaded files into uploads/<user_id>/ directory.

    Expect multipart/form-data with field name 'files' (can be sent multiple times).
    Example form field name: files
    """
    user_id = get_user_id_from_token(authorization)
    
    # Go up from routes/ to backend/, then into context/
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for upload in files:
        # Sanitize filename to avoid directory traversal
        filename = Path(upload.filename).name
        dest_path = uploads_dir / filename

        # Stream write to avoid loading entire file into memory
        with open(dest_path, "wb") as out_file:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                out_file.write(chunk)

        saved.append(str(dest_path))

    return {"saved": saved}