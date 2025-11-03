import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from models.users import UserModel
from dotenv import load_dotenv

load_dotenv()

class AuthController:
    def __init__(self):
        try:
            self.user_model = UserModel()
            self.user_model.client.admin.command('ping')
            print("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            raise e
            
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.jwt_expiration = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except:
            return False
    
    def generate_token(self, user_id: str, email: str) -> str:
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
    
    def signup(self, user_data: dict) -> dict:
        try:
            existing_user = self.user_model.find_user_by_email(user_data['email'])
            if existing_user:
                return {
                    'success': False,
                    'message': 'User with this email already exists',
                    'status_code': 409
                }
            
            hashed_password = self.hash_password(user_data['password'])
            
            user_db_data = {
                'firstName': user_data['firstName'],
                'lastName': user_data['lastName'],
                'email': user_data['email'].lower(),
                'password': hashed_password,
                'is_active': True
            }
            
            user_id = self.user_model.create_user(user_db_data)
            token = self.generate_token(user_id, user_data['email'])
            
            return {
                'success': True,
                'message': 'User created successfully',
                'data': {
                    'user_id': user_id,
                    'email': user_data['email'],
                    'firstName': user_data['firstName'],
                    'lastName': user_data['lastName'],
                    'token': token
                },
                'status_code': 201
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}',
                'status_code': 500
            }
    
    def login(self, credentials: dict) -> dict:
        try:
            user = self.user_model.find_user_by_email(credentials['email'])
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'status_code': 401
                }
            
            if not self.verify_password(credentials['password'], user['password']):
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'status_code': 401
                }
            
            token = self.generate_token(str(user['_id']), user['email'])
            
            return {
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user_id': str(user['_id']),
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName'],
                    'token': token
                },
                'status_code': 200
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Login failed: {str(e)}',
                'status_code': 500
            }