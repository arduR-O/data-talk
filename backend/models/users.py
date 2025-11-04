from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class UserModel:
    def __init__(self):
        self.connection_string = os.getenv('MONGODB_URI')
        self.client = MongoClient(self.connection_string)
        self.db = self.client[os.getenv('DATABASE_NAME', 'datatalk')]
        self.users = self.db.users
        
        # Create indexes
        self.users.create_index("email", unique=True)
    
    def create_user(self, user_data):
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        try:
            result = self.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            if "duplicate key error" in str(e):
                raise Exception("User with this email already exists")
            raise e
    
    def find_user_by_email(self, email):
        return self.users.find_one({'email': email.lower()})
    
    def find_user_by_id(self, user_id):
        try:
            return self.users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    def update_db_url(self, user_id, db_url):
        """Update or set the database URL for a user"""
        try:
            result = self.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'db_url': db_url,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            if result.matched_count == 0:
                return None
            return self.find_user_by_id(user_id)
        except Exception as e:
            raise Exception(f"Failed to update DB URL: {str(e)}")
    
    def get_db_url(self, user_id):
        """Get the database URL for a user"""
        user = self.find_user_by_id(user_id)
        if user:
            return user.get('db_url')
        return None