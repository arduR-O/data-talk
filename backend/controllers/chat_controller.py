from orchestrator import chat

class ChatController:
    def __init__(self):
        pass
    
    def process_message(self, question: str) -> dict:
        try:
            response = chat(question)
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