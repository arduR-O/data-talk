import sqlite3
import os
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class UserModel:
    def __init__(self):
        self.use_sqlite = False
        self.connection_string = os.getenv('MONGODB_URI')
        
        # Check if MongoDB connection details are present; if not, fallback immediately
        if not self.connection_string:
            self._init_sqlite()
            return
            
        try:
            # Using serverSelectionTimeoutMS to fail fast in offline/local environments
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client[os.getenv('DATABASE_NAME', 'datatalk')]
            self.users = self.db.users
            self.users.create_index("email", unique=True)
            print("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            # Reverting to SQLite file to allow the app to run completely self-contained
            print(f"MongoDB connection failed: {e}. Falling back to SQLite.")
            self._init_sqlite()
    
    def _init_sqlite(self):
        self.use_sqlite = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        context_dir = os.path.join(base_dir, 'context')
        os.makedirs(context_dir, exist_ok=True)
        self.sqlite_path = os.path.join(context_dir, 'datatalk_auth.db')
        
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        # Mirroring fields from MongoDB structure to support identical controller mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                firstName TEXT,
                lastName TEXT,
                email TEXT UNIQUE,
                password TEXT,
                is_active INTEGER,
                db_url TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def _sqlite_conn(self):
        return sqlite3.connect(self.sqlite_path)
    
    def create_user(self, user_data):
        user_data['created_at'] = datetime.now(timezone.utc)
        user_data['updated_at'] = datetime.now(timezone.utc)
        
        if not self.use_sqlite:
            try:
                result = self.users.insert_one(user_data)
                return str(result.inserted_id)
            except Exception as e:
                if isinstance(e, DuplicateKeyError) or "duplicate key" in str(e).lower():
                    raise Exception("User with this email already exists")
                raise e
        else:
            user_id = str(ObjectId())
            conn = self._sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (id, firstName, lastName, email, password, is_active, db_url, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    user_data.get('firstName'),
                    user_data.get('lastName'),
                    user_data.get('email', '').lower(),
                    user_data.get('password'),
                    1 if user_data.get('is_active', True) else 0,
                    user_data.get('db_url'),
                    user_data['created_at'].isoformat(),
                    user_data['updated_at'].isoformat()
                ))
                conn.commit()
                return user_id
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise Exception("User with this email already exists")
                raise e
            finally:
                conn.close()
    
    def find_user_by_email(self, email):
        if not self.use_sqlite:
            return self.users.find_one({'email': email.lower()})
            
        conn = self._sqlite_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Converting database row to match the exact schema expected by AuthController
        return {
            '_id': ObjectId(row['id']),
            'id': row['id'],
            'firstName': row['firstName'],
            'lastName': row['lastName'],
            'email': row['email'],
            'password': row['password'],
            'is_active': bool(row['is_active']),
            'db_url': row['db_url'],
            'created_at': datetime.fromisoformat(row['created_at']),
            'updated_at': datetime.fromisoformat(row['updated_at'])
        }
    
    def find_user_by_id(self, user_id):
        if not self.use_sqlite:
            try:
                return self.users.find_one({'_id': ObjectId(user_id)})
            except:
                return None
                
        conn = self._sqlite_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Preserving original ObjectId wrapper to prevent breaking route controllers
        return {
            '_id': ObjectId(row['id']),
            'id': row['id'],
            'firstName': row['firstName'],
            'lastName': row['lastName'],
            'email': row['email'],
            'password': row['password'],
            'is_active': bool(row['is_active']),
            'db_url': row['db_url'],
            'created_at': datetime.fromisoformat(row['created_at']),
            'updated_at': datetime.fromisoformat(row['updated_at'])
        }
    
    def update_db_url(self, user_id, db_url):
        try:
            if not self.use_sqlite:
                result = self.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {
                        '$set': {
                            'db_url': db_url,
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
                if result.matched_count == 0:
                    return None
                return self.find_user_by_id(user_id)
            else:
                conn = self._sqlite_conn()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET db_url = ?, updated_at = ? 
                    WHERE id = ?
                """, (db_url, datetime.now(timezone.utc).isoformat(), str(user_id)))
                conn.commit()
                updated_rows = cursor.rowcount
                conn.close()
                
                if updated_rows == 0:
                    return None
                return self.find_user_by_id(user_id)
        except Exception as e:
            raise Exception(f"Failed to update DB URL: {str(e)}")
    
    def get_db_url(self, user_id):
        user = self.find_user_by_id(user_id)
        if user:
            return user.get('db_url')
        return None