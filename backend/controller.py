from typing import Annotated, Union, List
from fastapi import FastAPI, File, UploadFile, HTTPException
from pathlib import Path
import os
from pydantic import BaseModel
from orchestrator import chat
import uvicorn
from fastapi.middleware.cors import CORSMiddleware 
from controllers.auth_controller import AuthController

app = FastAPI()
auth_controller = AuthController()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question :str 

@app.post("/")
def read_root(question : Question):
    return {"response" : chat(question.question)}

@app.post("/uploadfiles/")
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

if __name__ == "__main__":
    uvicorn.run("controller:app", port=8000, log_level="info")