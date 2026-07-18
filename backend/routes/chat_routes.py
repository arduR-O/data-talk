import json
import asyncio
from fastapi import APIRouter, HTTPException, Header, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from controllers.chat_controller import ChatController
from controllers.auth_controller import AuthController
from schemas.chat_schemas import ChatRequest, ChatResponse, DatabaseUrlRequest, DatabaseUrlResponse
from services.vector_service import get_vector_service
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from agentic_orchestrator import _stream_callback_var

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
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.process_message(user_id, chat_request.question, session_id=chat_request.session_id)
    
    if result['success']:
        return {
            "response": result['data']['response'],
            "routing": result['data'].get('routing'),
            "debug_logs": result['data'].get('debug_logs')
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )


@router.post("/chat/stream")
async def chat_stream_endpoint(
    chat_request: ChatRequest,
    authorization: str = Header(...)
):
    user_id = get_user_id_from_token(authorization)
    
    token_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    
    def stream_callback(token: str):
        try:
            loop.call_soon_threadsafe(token_queue.put_nowait, token)
        except Exception:
            pass

    async def event_generator():
        token = _stream_callback_var.set(stream_callback)
        
        chat_task = asyncio.create_task(
            asyncio.to_thread(
                chat_controller.process_message,
                user_id,
                chat_request.question,
                session_id=chat_request.session_id
            )
        )
        
        try:
            while not chat_task.done() or not token_queue.empty():
                try:
                    token_val = await asyncio.wait_for(token_queue.get(), timeout=0.05)
                    yield f"data: {json.dumps({'token': token_val})}\n\n"
                    token_queue.task_done()
                except asyncio.TimeoutError:
                    continue
            
            result = await chat_task
            if result['success']:
                final_data = {
                    "done": True,
                    "routing": result['data'].get('routing'),
                    "debug_logs": result['data'].get('debug_logs', [])
                }
                yield f"data: {json.dumps(final_data)}\n\n"
            else:
                yield f"data: {json.dumps({'error': result['message']})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            _stream_callback_var.reset(token)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/chat/sessions")
async def get_chat_sessions(authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.get_sessions(user_id)
    
    if result['success']:
        return {
            "sessions": result['data']['sessions']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )


@router.get("/chat/history")
async def get_chat_history(
    session_id: Optional[str] = 'default',
    authorization: str = Header(...)
):
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.get_history(user_id, session_id=session_id)
    
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
async def clear_chat_history(
    session_id: Optional[str] = 'default',
    authorization: str = Header(...)
):
    user_id = get_user_id_from_token(authorization)
    result = chat_controller.clear_history(user_id, session_id=session_id)
    
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
    user_id = get_user_id_from_token(authorization)
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    saved = []
    
    for upload in files:
        filename = Path(upload.filename).name
        dest_path = uploads_dir / filename
        
        MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB limit
        total_bytes = 0
        
        # Read file chunks incrementally to keep memory profile low
        with open(dest_path, "wb") as out_file:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_SIZE:
                    out_file.close()
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File {filename} exceeds the maximum size limit of 50MB"
                    )
                out_file.write(chunk)
        
        ext = dest_path.suffix.lower()
        
        # Branch actions based on file extension
        if ext in ['.db', '.sqlite']:
            # Instantly point the active user DB to the uploaded SQLite file
            file_db_url = f"sqlite:///{dest_path.resolve()}"
            auth_controller.user_model.update_db_url(user_id, file_db_url)
            saved.append({
                "filename": filename,
                "type": "database",
                "db_url": file_db_url
            })
        elif ext == '.csv':
            try:
                db_url = auth_controller.user_model.get_db_url(user_id)
                # Create a user-specific isolated SQLite DB if no db_url is currently set
                if not db_url or 'datatalk_demo.db' in db_url:
                    db_url = f"sqlite:///{uploads_dir.resolve()}/datatalk_user.db"
                    auth_controller.user_model.update_db_url(user_id, db_url)
                
                # Sanitize the filename to ensure it conforms to SQLite table name parameters
                table_name = dest_path.stem.lower()
                table_name = "".join([c if c.isalnum() or c == '_' else '_' for c in table_name])
                
                df = pd.read_csv(dest_path)
                engine = create_engine(db_url)
                df.to_sql(table_name, con=engine, if_exists='replace', index=False)
                
                saved.append({
                    "filename": filename,
                    "type": "csv_table",
                    "table_name": table_name,
                    "db_url": db_url
                })
            except Exception as csv_err:
                saved.append({
                    "filename": filename,
                    "type": "csv_error",
                    "error": str(csv_err)
                })
        else:
            saved.append({
                "filename": filename,
                "type": "document",
                "path": str(dest_path)
            })
            
            # Spin off the vectorization to a background thread to prevent endpoint timeout
            vector_service = get_vector_service()
            background_tasks.add_task(
                vector_service.process_and_upload_document,
                user_id,
                str(dest_path),
                filename
            )
    
    return {
        "message": f"Successfully uploaded {len(saved)} file(s). Data mapped.",
        "saved": saved
    }


@router.get("/uploadfiles/")
async def list_uploaded_files(authorization: str = Header(...)):
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
    user_id = get_user_id_from_token(authorization)
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    file_path = uploads_dir / Path(filename).name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_relative_to(uploads_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        file_path.unlink()
        
        # Clear the database URL mapping if the deleted file was the active connection source
        db_url = auth_controller.user_model.get_db_url(user_id)
        if db_url and file_path.name in db_url:
            auth_controller.user_model.update_db_url(user_id, "")
            
        vectors_deleted = False
        deleted_count = 0
        
        # Only invoke deletion from the vector store if it was a vectorized text document
        if file_path.suffix.lower() in ['.pdf', '.txt', '.md']:
            vector_service = get_vector_service()
            vector_result = vector_service.delete_document(user_id, filename)
            vectors_deleted = vector_result.get("success", False)
            deleted_count = vector_result.get("deleted_count", 0)
        
        return {
            "message": f"File '{filename}' deleted successfully",
            "file_deleted": True,
            "vectors_deleted": vectors_deleted,
            "vectors_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vectors/status")
async def get_vector_status(authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization)
    
    try:
        vector_service = get_vector_service()
        
        base_dir = Path(__file__).resolve().parent.parent
        uploads_dir = base_dir / "context" / user_id
        
        fs_files = set()
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.md']:
                    fs_files.add(file_path.name)
        
        vector_files = set(vector_service.list_user_documents(user_id))
        
        vectorized = list(fs_files.intersection(vector_files))
        pending = list(fs_files - vector_files)
        orphaned = list(vector_files - fs_files)
        
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
                "files": orphaned
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard(authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization)
    
    try:
        db_url = auth_controller.user_model.get_db_url(user_id)
        
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
        
        history_result = chat_controller.get_history(user_id)
        chat_count = len(history_result['data']['messages']) if history_result['success'] else 0
        
        return {
            "database": {
                "connected": db_url is not None and db_url.strip() != "",
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