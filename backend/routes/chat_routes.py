from fastapi import APIRouter, HTTPException, Header
from controllers.chat_controller import ChatController
from schemas.chat_schemas import ChatRequest, ChatResponse
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from pathlib import Path
from controllers.auth_controller import AuthController

app = FastAPI()
auth_controller = AuthController()

router = APIRouter()
chat_controller = ChatController()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """Chat endpoint for AI responses"""
    result = chat_controller.process_message(chat_request.question)
    
    if result['success']:
        return {
            "response": result['data']['response']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )

@router.post("/uploadfiles/")
async def create_upload_files(authorization: str = Header(...), files: List[UploadFile] = File(...)):
    """Save uploaded files into uploads/<user_id>/ directory.

    Expect multipart/form-data with field name 'files' (can be sent multiple times).
    Example form field name: files
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = auth_controller.verify_token(token)
        user = auth_controller.user_model.find_user_by_id(payload['user_id'])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    base_dir = Path(__file__).resolve().parent
    uploads_dir = base_dir / "uploads" / payload["user_id"]
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