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


DEMO_MOCK_RESPONSES = {
    "list all departments and their budgets": {
        "routing": "sql",
        "answer": (
            "Here are the departments and their allocated budgets from the database:\n\n"
            "* **Engineering:** $500,000.00\n"
            "* **Product:** $250,000.00\n"
            "* **Marketing:** $150,000.00\n"
            "* **Sales:** $300,000.00\n"
            "* **HR:** $100,000.00"
        )
    },
    "show employee salaries and their departments": {
        "routing": "sql",
        "answer": (
            "Here is the list of employees, their salaries, and their departments:\n\n"
            "* **Alice Smith** (Engineering) — $95,000.00\n"
            "* **Bob Jones** (Engineering) — $105,000.00\n"
            "* **Charlie Brown** (Product) — $85,000.00\n"
            "* **Diana Prince** (Marketing) — $75,000.00\n"
            "* **Ethan Hunt** (Engineering) — $110,000.00\n"
            "* **Fiona Gallagher** (Sales) — $90,000.00\n"
            "* **George Costanza** (HR) — $60,000.00\n"
            "* **Hannah Baker** (Engineering) — $98,000.00\n"
            "* **Ian Malcolm** (Marketing) — $78,000.00\n"
            "* **Jane Doe** (Sales) — $115,000.00"
        )
    },
    "plot department salaries compared to their budgets": {
        "routing": "sql",
        "answer": (
            "Here is the comparison between total employee salaries and allocated budgets for each department:\n\n"
            "```CHART\n"
            "{\n"
            "  \"TYPE\": \"BAR\",\n"
            "  \"TITLE\": \"DEPARTMENT SALARIES VS BUDGETS\",\n"
            "  \"DATA\": [\n"
            "    {\"NAME\": \"Engineering Salaries\", \"VALUE\": 408000.0},\n"
            "    {\"NAME\": \"Engineering Budget\", \"VALUE\": 500000.0},\n"
            "    {\"NAME\": \"Product Salaries\", \"VALUE\": 85000.0},\n"
            "    {\"NAME\": \"Product Budget\", \"VALUE\": 250000.0},\n"
            "    {\"NAME\": \"Marketing Salaries\", \"VALUE\": 153000.0},\n"
            "    {\"NAME\": \"Marketing Budget\", \"VALUE\": 150000.0},\n"
            "    {\"NAME\": \"Sales Salaries\", \"VALUE\": 205000.0},\n"
            "    {\"NAME\": \"Sales Budget\", \"VALUE\": 300000.0},\n"
            "    {\"NAME\": \"HR Salaries\", \"VALUE\": 60000.0},\n"
            "    {\"NAME\": \"HR Budget\", \"VALUE\": 100000.0}\n"
            "  ]\n"
            "}\n"
            "```"
        )
    },
    "what are the company target budgets for next year from the document": {
        "routing": "rag",
        "answer": (
            "Based on the `demo_target_budgets.txt` document, the target budgets for next year are:\n\n"
            "* **Engineering:** Target: $520,000 (focused on infrastructure scaling)\n"
            "* **Product:** Target: $280,000 (mobile app launch readiness)\n"
            "* **Marketing:** Target: $165,000 (growth marketing and SEO campaigns)\n"
            "* **Sales:** Target: $330,000 (expanding sales team by 15%)\n"
            "* **HR:** Target: $110,000 (employee wellness and retention programs)"
        )
    },
    "are there any extra benefits listed in the csv": {
        "routing": "rag",
        "answer": (
            "Yes! Based on the uploaded `demo_extra_benefits.csv` file, the following extra benefits are listed:\n\n"
            "* **Health Insurance Premium:** Fully covered (100%) for all full-time employees.\n"
            "* **Gym Membership Reimbursement:** Up to $50/month per employee.\n"
            "* **Remote Work Stipend:** $150 one-time home office setup allowance.\n"
            "* **Learning & Development budget:** $1,500/year per employee for courses or certifications."
        )
    }
}


def get_mock_response(user_id: str, session_id: str):
    import os
    if os.getenv("DEMO_MOCK_MODE", "true").lower() != "true":
        return None
        
    messages = chat_controller.chat_history_model.get_user_history(user_id, session_id=session_id)
    # Filter only messages for the current session to get the sequence index
    # Since each turn adds 2 messages (1 user, 1 assistant), the sequence index is len(messages) // 2
    seq_idx = len(messages) // 2
    
    # Pre-computed sequence responses
    responses = [
        # Sequence 1: SQL Budgets list
        {
            "routing": "sql",
            "answer": (
                "Here are the departments and their allocated budgets from the database:\n\n"
                "- **Engineering:** $500,000.00\n"
                "- **Product:** $250,000.00\n"
                "- **Marketing:** $150,000.00\n"
                "- **Sales:** $300,000.00\n"
                "- **HR:** $100,000.00"
            )
        },
        # Sequence 2: SQL Joining Salaries list
        {
            "routing": "sql",
            "answer": (
                "Here is the list of employees, their salaries, and their departments:\n\n"
                "- **Alice Smith** (Engineering) — $95,000.00\n"
                "- **Bob Jones** (Engineering) — $105,000.00\n"
                "- **Charlie Brown** (Product) — $85,000.00\n"
                "- **Diana Prince** (Marketing) — $75,000.00\n"
                "- **Ethan Hunt** (Engineering) — $110,000.00\n"
                "- **Fiona Gallagher** (Sales) — $90,000.00\n"
                "- **George Costanza** (HR) — $60,000.00\n"
                "- **Hannah Baker** (Engineering) — $98,000.00\n"
                "- **Ian Malcolm** (Marketing) — $78,000.00\n"
                "- **Jane Doe** (Sales) — $115,000.00"
            )
        },
        # Sequence 3: Recharts stacked bar chart visualization
        {
            "routing": "sql",
            "answer": (
                "Here is the comparison between total employee salaries and allocated budgets for each department:\n\n"
                "```CHART\n"
                "{\n"
                "  \"TYPE\": \"BAR\",\n"
                "  \"TITLE\": \"DEPARTMENT SALARIES VS BUDGETS\",\n"
                "  \"DATA\": [\n"
                "    {\"NAME\": \"Engineering Salaries\", \"VALUE\": 408000.0},\n"
                "    {\"NAME\": \"Engineering Budget\", \"VALUE\": 500000.0},\n"
                "    {\"NAME\": \"Product Salaries\", \"VALUE\": 85000.0},\n"
                "    {\"NAME\": \"Product Budget\", \"VALUE\": 250000.0},\n"
                "    {\"NAME\": \"Marketing Salaries\", \"VALUE\": 153000.0},\n"
                "    {\"NAME\": \"Marketing Budget\", \"VALUE\": 150000.0},\n"
                "    {\"NAME\": \"Sales Salaries\", \"VALUE\": 205000.0},\n"
                "    {\"NAME\": \"Sales Budget\", \"VALUE\": 300000.0},\n"
                "    {\"NAME\": \"HR Salaries\", \"VALUE\": 60000.0},\n"
                "    {\"NAME\": \"HR Budget\", \"VALUE\": 100000.0}\n"
                "  ]\n"
                "}\n"
                "```"
            )
        },
        # Sequence 4: RAG Doc Search Budgets
        {
            "routing": "rag",
            "answer": (
                "Based on the `demo_target_budgets.txt` document, the target budgets for next year are:\n\n"
                "- **Engineering:** Target: $520,000 (focused on infrastructure scaling)\n"
                "- **Product:** Target: $280,000 (mobile app launch readiness)\n"
                "- **Marketing:** Target: $165,000 (growth marketing and SEO campaigns)\n"
                "- **Sales:** Target: $330,000 (expanding sales team by 15%)\n"
                "- **HR:** Target: $110,000 (employee wellness and retention programs)"
            )
        },
        # Sequence 5: CSV Parsing extra benefits
        {
            "routing": "rag",
            "answer": (
                "Yes! Based on the uploaded `demo_extra_benefits.csv` file, the following extra benefits are listed:\n\n"
                "- **Health Insurance Premium:** Fully covered (100%) for all full-time employees.\n"
                "- **Gym Membership Reimbursement:** Up to $50/month per employee.\n"
                "- **Remote Work Stipend:** $150 one-time home office setup allowance.\n"
                "- **Learning & Development budget:** $1,500/year per employee for courses or certifications."
            )
        }
    ]
    
    if seq_idx < len(responses):
        return responses[seq_idx]
        
    return {
        "routing": "general",
        "answer": (
            "You have completed the sequence-based live demo simulation!\n\n"
            "To restart the sequence, please clear your active chat session in the sidebar, or ask standard questions if you disable `DEMO_MOCK_MODE` in the backend configuration."
        )
    }


@router.post("/chat/stream")
async def chat_stream_endpoint(
    chat_request: ChatRequest,
    authorization: str = Header(...)
):
    user_id = get_user_id_from_token(authorization)
    
    # Intercept for pre-seeded simulation responses
    mock_data = get_mock_response(user_id, chat_request.session_id)
    if mock_data:
        async def mock_event_generator():
            # Save user query to history
            chat_controller.chat_history_model.add_message(user_id, 'user', chat_request.question, session_id=chat_request.session_id)
            
            # Artificial thinking delay
            await asyncio.sleep(5)
            
            # Stream response in chunks
            answer = mock_data["answer"]
            chunk_size = 8
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                yield f"data: {json.dumps({'token': chunk})}\n\n"
                await asyncio.sleep(0.01) # 10ms sleep
                
            # Save assistant response to history
            chat_controller.chat_history_model.add_message(user_id, 'assistant', answer, session_id=chat_request.session_id)
            
            final_data = {
                "done": True,
                "routing": mock_data["routing"],
                "debug_logs": [
                    {
                        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        "level": "INFO",
                        "message": "Demo Mode: Pre-computed response loaded successfully to preserve API tokens.",
                        "data": {}
                    }
                ]
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        return StreamingResponse(mock_event_generator(), media_type="text/event-stream")
    
    
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
    
    import os
    if not os.getenv("GROQ_API_KEY"):
        now = datetime.now().strftime("%I:%M:%S %p")
        return {
            "demo_mode": True,
            "messages": [
                {
                    "type": "system",
                    "content": "Welcome to DataTalk workspace. You are viewing a **demo session** with a pre-loaded SQLite database containing `employees` and `projects` tables. Ask questions in the chat below to see simulated agent responses.",
                    "timestamp": now
                },
                {
                    "type": "user",
                    "content": "How many employees are in each department?",
                    "timestamp": now
                },
                {
                    "type": "assistant",
                    "content": "I queried the demo database and found **6 employees** across **3 departments**.\n\n```sql\nSELECT department, COUNT(*) as count\nFROM employees\nGROUP BY department\nORDER BY count DESC;\n```\n\n| Department | Count |\n|---|---|\n| Engineering | 3 |\n| Sales | 2 |\n| Marketing | 1 |\n\nEngineering has the most staff. Would you like to see salary breakdowns?",
                    "timestamp": now,
                    "routing": "database"
                },
                {
                    "type": "user",
                    "content": "Yes, show me the average salary by department",
                    "timestamp": now
                },
                {
                    "type": "assistant",
                    "content": "Here are the average salaries by department:\n\n```sql\nSELECT department, ROUND(AVG(salary), 0) as avg_salary\nFROM employees\nGROUP BY department\nORDER BY avg_salary DESC;\n```\n\n```chart\n" + '{"type": "bar", "title": "Avg Salary by Department", "data": [{"name": "Engineering", "value": 116000}, {"name": "Sales", "value": 91500}, {"name": "Marketing", "value": 82000}]}' + "\n```\n\nEngineering leads at **$116,000** average, followed by Sales at **$91,500** and Marketing at **$82,000**.",
                    "timestamp": now,
                    "routing": "database"
                }
            ]
        }

    if result['success']:
        return {
            "demo_mode": False,
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


@router.get("/database/schema")
async def get_database_schema(authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization)
    
    try:
        db_url = auth_controller.user_model.get_db_url(user_id)
        if not db_url:
            db_url = "sqlite:///datatalk_demo.db"
            
        from sqlalchemy import create_engine, MetaData
        engine = create_engine(db_url)
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        tables_info = []
        for table_name, table in metadata.tables.items():
            columns = []
            for col in table.columns:
                columns.append({
                    "name": col.name,
                    "type": str(col.type),
                    "primary_key": col.primary_key
                })
            
            # Fetch sample rows
            try:
                with engine.connect() as conn:
                    # Fetch up to 1000 rows for virtualizer demonstration
                    res = conn.execute(table.select().limit(1000))
                    rows = [dict(row._mapping) for row in res]
            except Exception:
                rows = []
                
            tables_info.append({
                "name": table_name,
                "columns": columns,
                "sample_rows": rows
            })
            
        return {"tables": tables_info}
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
    
    # Track the filenames being uploaded in the current request to avoid deleting them
    uploading_filenames = {Path(u.filename).name for u in files}
    saved = []

    # Check if the uploads folder contains the pre-seeded demo files (both datatalk_user.db and demo_target_budgets.txt)
    # and neither is part of the current upload request. If so, this is the first user upload, and we should clear them.
    existing_names = {f.name for f in uploads_dir.iterdir() if f.is_file()}
    has_demo_db = "datatalk_user.db" in existing_names
    has_demo_doc = "demo_target_budgets.txt" in existing_names
    
    is_preconfigured_demo = (
        has_demo_db and has_demo_doc 
        and "datatalk_user.db" not in uploading_filenames
        and "demo_target_budgets.txt" not in uploading_filenames
    )
    
    if is_preconfigured_demo:
        print(f"🧹 First user upload detected. Cleaning up pre-seeded demo files for user {user_id}.")
        # Clear database cache/connections first to release locks
        from nlp import create_database_graph
        create_database_graph.cache_clear()
        import gc
        gc.collect()
        
        for name in ["datatalk_user.db", "demo_target_budgets.txt"]:
            f = uploads_dir / name
            try:
                if name == "demo_target_budgets.txt":
                    vector_service = get_vector_service()
                    if vector_service.available:
                        vector_service.delete_document(user_id, name)
                f.unlink(missing_ok=True)
            except Exception as e:
                print(f"Error cleaning up demo file {name}: {e}")
        
        # Reset the user's DB URL to empty so they start fresh
        auth_controller.user_model.update_db_url(user_id, "")
    
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
            # Clean up only previous database files in the uploads folder to start fresh with the new database
            for existing_file in list(uploads_dir.iterdir()):
                if existing_file.is_file() and existing_file.suffix.lower() in ['.db', '.sqlite'] and existing_file.name not in uploading_filenames:
                    try:
                        from nlp import create_database_graph
                        create_database_graph.cache_clear()
                        import gc
                        gc.collect()
                        existing_file.unlink()
                    except Exception as clean_err:
                        print(f"Error cleaning up old database {existing_file.name}: {clean_err}")

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
                if not db_url:
                    db_url = f"sqlite:///{uploads_dir.resolve()}/datatalk_user.db"
                    # Ensure the empty SQLite file is created
                    engine = create_engine(db_url)
                    with engine.connect() as conn:
                        pass
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
    
    # Clear the database graph cache so any newly uploaded tables or schema changes are loaded immediately
    from nlp import create_database_graph
    create_database_graph.cache_clear()
    import gc
    gc.collect()

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
        # Make deletion idempotent to handle race conditions / double clicks gracefully
        return {
            "message": f"File '{filename}' deleted successfully",
            "file_deleted": True,
            "vectors_deleted": False,
            "vectors_count": 0
        }
    
    if not file_path.is_relative_to(uploads_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        # Clear database mapping and clear graph cache first to release active SQLite file locks
        db_url = auth_controller.user_model.get_db_url(user_id)
        if db_url and file_path.name in db_url:
            auth_controller.user_model.update_db_url(user_id, "")

        from nlp import create_database_graph
        create_database_graph.cache_clear()
        
        import gc
        gc.collect()

        file_path.unlink()
            
        vectors_deleted = False
        deleted_count = 0
        
        # Only invoke deletion from the vector store if it was a vectorized text document
        if file_path.suffix.lower() in ['.pdf', '.txt', '.md']:
            vector_service = get_vector_service()
            if vector_service.available:
                try:
                    vector_result = vector_service.delete_document(user_id, filename)
                    vectors_deleted = vector_result.get("success", False)
                    deleted_count = vector_result.get("deleted_count", 0)
                except Exception as pc_err:
                    print(f"⚠️ Failed to delete vectors from Pinecone: {pc_err}")
        
        return {
            "message": f"File '{filename}' deleted successfully",
            "file_deleted": True,
            "vectors_deleted": vectors_deleted,
            "vectors_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploadfiles/{filename}")
async def get_uploaded_file_content(
    filename: str,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
):
    # Support standard Authorization header or token query param (for opening PDF in new tab)
    auth_header = authorization
    if not auth_header and token:
        auth_header = f"Bearer {token}"
        
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_id = get_user_id_from_token(auth_header)
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "context" / user_id
    file_path = uploads_dir / Path(filename).name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    if not file_path.is_relative_to(uploads_dir):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    ext = file_path.suffix.lower()
    
    if ext == '.csv':
        try:
            df = pd.read_csv(file_path)
            # Replace NaN with empty string to avoid JSON validation issues
            df = df.fillna("")
            preview_df = df.head(100)
            return {
                "type": "csv",
                "filename": filename,
                "columns": list(preview_df.columns),
                "rows": preview_df.to_dict(orient="records"),
                "total_rows": len(df)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read CSV: {str(e)}")
            
    elif ext in ['.txt', '.md']:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {
                "type": "text",
                "filename": filename,
                "content": content
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read text file: {str(e)}")
            
    elif ext == '.pdf':
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename
        )
        
    else:
        raise HTTPException(status_code=400, detail=f"File preview not supported for {ext} files")


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