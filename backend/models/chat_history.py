import sqlite3
import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ChatHistoryModel:
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
            self.chat_history = self.db.chat_history
            self.chat_history.create_index("user_id")
            self.chat_history.create_index([("user_id", 1), ("timestamp", -1)])
            print("Successfully connected to MongoDB Atlas for Chat History!")
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
        # Creating index on user_id and timestamp to optimize chronological sorting performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_history ON chat_history (user_id, timestamp)")
        conn.commit()
        conn.close()
        
    def _sqlite_conn(self):
        return sqlite3.connect(self.sqlite_path)
        
    def add_message(self, user_id: str, message_type: str, content: str):
        if not self.use_sqlite:
            message_data = {
                'user_id': user_id,
                'type': message_type,
                'content': content,
                'timestamp': datetime.utcnow()
            }
            result = self.chat_history.insert_one(message_data)
            return str(result.inserted_id)
        else:
            msg_id = str(ObjectId())
            conn = self._sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (id, user_id, type, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                msg_id,
                user_id,
                message_type,
                content,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            conn.close()
            return msg_id
            
    def get_user_history(self, user_id: str, limit: int = 100):
        if not self.use_sqlite:
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
        else:
            conn = self._sqlite_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row['id'],
                    'type': row['type'],
                    'content': row['content'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
            
    def clear_user_history(self, user_id: str):
        if not self.use_sqlite:
            result = self.chat_history.delete_many({'user_id': user_id})
            return result.deleted_count
        else:
            conn = self._sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
