from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ChatHistoryModel:
    def __init__(self):
        self.connection_string = os.getenv('MONGODB_URI')
        self.client = MongoClient(self.connection_string)
        self.db = self.client[os.getenv('DATABASE_NAME', 'datatalk')]
        self.chat_history = self.db.chat_history
        
        # Create indexes
        self.chat_history.create_index("user_id")
        self.chat_history.create_index([("user_id", 1), ("timestamp", -1)])
    
    def add_message(self, user_id: str, message_type: str, content: str):
        """Add a message to chat history"""
        message_data = {
            'user_id': user_id,
            'type': message_type,  # 'user', 'assistant', or 'system'
            'content': content,
            'timestamp': datetime.utcnow()
        }
        result = self.chat_history.insert_one(message_data)
        return str(result.inserted_id)
    
    def get_user_history(self, user_id: str, limit: int = 100):
        """Get chat history for a user, ordered by timestamp"""
        messages = self.chat_history.find(
            {'user_id': user_id}
        ).sort('timestamp', 1).limit(limit)
        
        return [
            {
                'id': str(msg['_id']),
                'type': msg['type'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat() if isinstance(msg['timestamp'], datetime) else msg['timestamp']
            }
            for msg in messages
        ]
    
    def clear_user_history(self, user_id: str):
        """Clear all chat history for a user"""
        result = self.chat_history.delete_many({'user_id': user_id})
        return result.deleted_count

