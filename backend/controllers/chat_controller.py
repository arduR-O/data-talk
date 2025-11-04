from orchestrator import chat
from models.chat_history import ChatHistoryModel
from models.users import UserModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from datetime import datetime

class ChatController:
    def __init__(self):
        self.chat_history_model = ChatHistoryModel()
        self.user_model = UserModel()
    
    def process_message(self, user_id: str, question: str) -> dict:
        """
        Process a chat message with full context:
        - Load user's chat history
        - Get user's database URL
        - Send to orchestrator
        - Save conversation to history
        """
        try:
            # Get user's database URL
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
            
            # Save user message to database
            self.chat_history_model.add_message(user_id, 'user', question)
            
            # Get AI response using orchestrator with history and db_url
            # Call with positional arguments in the correct order
            response = chat(question, conversation_history, db_url)
            
            # Save assistant response to database
            self.chat_history_model.add_message(user_id, 'assistant', response)
            
            return {
                'success': True,
                'data': {
                    'response': response
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
        """Get chat history for a user"""
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
        """Clear chat history for a user"""
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