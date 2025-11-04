from orchestrator import chat
from models.users import UserModel

class ChatController:
    def __init__(self):
        self.user_model = UserModel()
    
    def process_message(self, question: str, user_id: str = None) -> dict:
        try:
            # Get user's database URL if user_id is provided
            db_url = None
            if user_id:
                db_url = self.user_model.get_db_url(user_id)
            
            # Call orchestrator with user_id and db_url
            response = chat(question, user_id=user_id, db_url=db_url)
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