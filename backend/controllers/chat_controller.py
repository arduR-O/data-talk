# from unified_orchestrator import get_orchestrator
from agentic_orchestrator import get_orchestrator
from models.chat_history import ChatHistoryModel
from models.users import UserModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from typing import Optional

class ChatController:
    """
    Controller for handling chat interactions.
    Uses unified orchestrator that intelligently routes between SQL and RAG.
    """
    
    def __init__(self):
        self.chat_history_model = ChatHistoryModel()
        self.user_model = UserModel()
        self.orchestrator = get_orchestrator()
    
    def process_message(self, user_id: str, question: str) -> dict:
        """
        Process a chat message with intelligent routing.
        
        Flow:
        1. Load user's chat history from database
        2. Get user's database URL (if configured)
        3. Send to unified orchestrator (auto-routes to SQL/RAG/both)
        4. Save conversation to history
        
        Args:
            user_id: User's unique identifier
            question: User's question
        
        Returns:
            dict with success status and response data
        """
        try:
            # Get user's database URL (might be None)
            db_url = self.user_model.get_db_url(user_id)
            
            # Load conversation history from database
            history_messages = self.chat_history_model.get_user_history(user_id)
            
            # Convert database messages to LangChain messages
            conversation_history = []
            for msg in history_messages:
                if msg['type'] == 'user':
                    conversation_history.append(HumanMessage(content=msg['content']))
                elif msg['type'] == 'assistant':
                    conversation_history.append(AIMessage(content=msg['content']))
            
            # Save user message to database first
            self.chat_history_model.add_message(user_id, 'user', question)
            
            # Process through unified orchestrator
            result = self.orchestrator.chat(
                question=question,
                user_id=user_id,
                conversation_history=conversation_history,
                db_url=db_url,
                debug=True
            )
            
            answer = result['answer']
            routing = result['routing']
            resources = result['resources']
            
            # Save assistant response to database
            self.chat_history_model.add_message(user_id, 'assistant', answer)
            
            return {
                'success': True,
                'data': {
                    'response': answer,
                    'routing': routing,  # 'sql', 'rag', 'hybrid', or 'general'
                    'resources': resources  # What resources are available
                },
                'status_code': 200
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Chat processing failed: {str(e)}',
                'status_code': 500
            }
    
    def get_history(self, user_id: str) -> dict:
        """
        Get chat history for a user.
        
        Args:
            user_id: User's unique identifier
        
        Returns:
            dict with success status and messages
        """
        try:
            messages = self.chat_history_model.get_user_history(user_id)
            return {
                'success': True,
                'data': {
                    'messages': messages
                },
                'status_code': 200
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to retrieve chat history: {str(e)}',
                'status_code': 500
            }
    
    def clear_history(self, user_id: str) -> dict:
        """
        Clear chat history for a user.
        
        Args:
            user_id: User's unique identifier
        
        Returns:
            dict with success status and deletion count
        """
        try:
            deleted_count = self.chat_history_model.clear_user_history(user_id)
            return {
                'success': True,
                'data': {
                    'deleted_count': deleted_count
                },
                'status_code': 200
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to clear chat history: {str(e)}',
                'status_code': 500
            }