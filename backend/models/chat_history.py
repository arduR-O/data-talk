import sqlite3
import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
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
            self.chat_history.create_index([("user_id", 1), ("session_id", 1), ("timestamp", 1)])
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT DEFAULT 'default',
                type TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_history ON chat_history (user_id, session_id, timestamp)")
        try:
            cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        
    def _sqlite_conn(self):
        return sqlite3.connect(self.sqlite_path)
        
    def add_message(self, user_id: str, message_type: str, content: str, session_id: str = 'default'):
        if not self.use_sqlite:
            message_data = {
                'user_id': user_id,
                'session_id': session_id,
                'type': message_type,
                'content': content,
                'timestamp': datetime.now(timezone.utc)
            }
            result = self.chat_history.insert_one(message_data)
            return str(result.inserted_id)
        else:
            msg_id = str(ObjectId())
            conn = self._sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (id, user_id, session_id, type, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                msg_id,
                user_id,
                session_id,
                message_type,
                content,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
            conn.close()
            return msg_id
            
    def get_user_history(self, user_id: str, limit: int = 100, session_id: str = 'default'):
        if not self.use_sqlite:
            messages = self.chat_history.find(
                {'user_id': user_id, 'session_id': session_id}
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
                WHERE user_id = ? AND COALESCE(session_id, 'default') = ?
                ORDER BY timestamp ASC 
                LIMIT ?
            """, (user_id, session_id, limit))
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
            
    def clear_user_history(self, user_id: str, session_id: str = 'default'):
        if not self.use_sqlite:
            result = self.chat_history.delete_many({'user_id': user_id, 'session_id': session_id})
            return result.deleted_count
        else:
            conn = self._sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE user_id = ? AND COALESCE(session_id, 'default') = ?", (user_id, session_id))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count

    def get_user_sessions(self, user_id: str) -> list[dict]:
        if not self.use_sqlite:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$session_id",
                    "last_timestamp": {"$first": "$timestamp"},
                    "first_message": {"$last": "$content"}
                }},
                {"$sort": {"last_timestamp": -1}}
            ]
            results = list(self.chat_history.aggregate(pipeline))
            
            sessions = []
            for r in results:
                s_id = r["_id"] or "default"
                sessions.append({
                    "session_id": s_id,
                    "title": r["first_message"][:30] + "..." if r.get("first_message") else "New Chat",
                    "timestamp": r["last_timestamp"].isoformat() if isinstance(r["last_timestamp"], datetime) else r["last_timestamp"]
                })
            return sessions
        else:
            conn = self._sqlite_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(session_id, 'default') as session_id,
                    MAX(timestamp) as last_active,
                    (SELECT content FROM chat_history h2 
                     WHERE h2.user_id = ? 
                     AND COALESCE(h2.session_id, 'default') = COALESCE(chat_history.session_id, 'default') 
                     AND h2.type = 'user' 
                     ORDER BY h2.timestamp ASC LIMIT 1) as title
                FROM chat_history
                WHERE user_id = ?
                GROUP BY COALESCE(session_id, 'default')
                ORDER BY last_active DESC
            """, (user_id, user_id))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "session_id": row["session_id"],
                    "title": row["title"][:30] + "..." if row["title"] else "New Chat",
                    "timestamp": row["last_active"]
                }
                for row in rows
            ]
