from fastapi import APIRouter, HTTPException
from controllers.chat_controller import ChatController
from schemas.chat_schemas import ChatRequest, ChatResponse

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