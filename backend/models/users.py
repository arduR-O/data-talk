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