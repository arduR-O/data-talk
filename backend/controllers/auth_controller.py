import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from models.users import UserModel
from dotenv import load_dotenv
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

load_dotenv()

class AuthController:
    def __init__(self):
        try:
            self.user_model = UserModel()
            if hasattr(self.user_model, 'client') and self.user_model.client:
                self.user_model.client.admin.command('ping')
                print("Successfully connected to MongoDB Atlas!")
            else:
                print("Using local SQLite auth database (fallback).")
        except Exception as e:
            print(f"MongoDB connection failed: {e}. Falling back to SQLite.")
            
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
        except Exception as e:
            import logging
            logging.error(f"Password verification error: {e}")
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

    def google_login(self, id_token_str: str) -> dict:
        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            allow_mock = os.getenv("ALLOW_MOCK_OAUTH", "false").lower() == "true"
            
            try:
                idinfo = google_id_token.verify_oauth2_token(
                    id_token_str,
                    google_requests.Request(),
                    client_id
                )
            except Exception as e:
                if allow_mock and id_token_str.startswith("mock_google_"):
                    email = id_token_str.replace("mock_google_", "")
                    name_part = email.split("@")[0]
                    idinfo = {
                        "email": email,
                        "given_name": name_part.capitalize(),
                        "family_name": "User",
                        "sub": f"mock_google_sub_{name_part}"
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Invalid Google ID Token: {str(e)}',
                        'status_code': 400
                    }

            email = idinfo['email']
            first_name = idinfo.get('given_name', 'Google')
            last_name = idinfo.get('family_name', 'User')

            user = self.user_model.find_user_by_email(email)
            
            if not user:
                signup_data = {
                    'firstName': first_name,
                    'lastName': last_name,
                    'email': email,
                    'password': self.hash_password("google-oauth-dummy-password-" + email)
                }
                user_id = self.user_model.create_user(signup_data)
                user = self.user_model.find_user_by_email(email)
            
            user_id_str = str(user['_id'])
            token = self.generate_token(user_id_str, user['email'])

            return {
                'success': True,
                'message': 'Google authentication successful',
                'data': {
                    'user_id': user_id_str,
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
                'message': f'Google authentication failed: {str(e)}',
                'status_code': 500
            }