"""
Unit tests for ChatHistoryModel
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from models.chat_history import ChatHistoryModel
from bson import ObjectId
from datetime import datetime, timezone


class TestChatHistoryModel:
    """Test suite for ChatHistoryModel"""
    
    @pytest.fixture
    def chat_history_model(self):
        """Create ChatHistoryModel instance with mocked MongoDB"""
        with patch('models.chat_history.MongoClient') as mock_client_class:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            
            mock_client_class.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_db.chat_history = mock_collection
            
            model = ChatHistoryModel()
            model.client = mock_client
            model.db = mock_db
            model.chat_history = mock_collection
            
            return model
    
    def test_add_message_success(self, chat_history_model):
        """Test adding a message successfully"""
        user_id = str(ObjectId())
        message_type = 'user'
        content = 'Hello, world!'
        
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        chat_history_model.chat_history.insert_one.return_value = mock_result
        
        message_id = chat_history_model.add_message(user_id, message_type, content)
        
        assert isinstance(message_id, str)
        assert message_id == str(mock_result.inserted_id)
        chat_history_model.chat_history.insert_one.assert_called_once()
        
        # Verify the message data structure
        call_args = chat_history_model.chat_history.insert_one.call_args[0][0]
        assert call_args['user_id'] == user_id
        assert call_args['type'] == message_type
        assert call_args['content'] == content
        assert 'timestamp' in call_args
    
    def test_get_user_history_success(self, chat_history_model):
        """Test getting user chat history"""
        user_id = str(ObjectId())
        mock_messages = [
            {
                '_id': ObjectId(),
                'user_id': user_id,
                'type': 'user',
                'content': 'Hello',
                'timestamp': datetime.now(timezone.utc)
            },
            {
                '_id': ObjectId(),
                'user_id': user_id,
                'type': 'assistant',
                'content': 'Hi there!',
                'timestamp': datetime.now(timezone.utc)
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter(mock_messages)
        chat_history_model.chat_history.find.return_value = mock_cursor
        
        result = chat_history_model.get_user_history(user_id)
        
        assert len(result) == 2
        assert result[0]['type'] == 'user'
        assert result[0]['content'] == 'Hello'
        assert result[1]['type'] == 'assistant'
        assert result[1]['content'] == 'Hi there!'
        assert 'id' in result[0]
        assert 'timestamp' in result[0]
    
    def test_get_user_history_empty(self, chat_history_model):
        """Test getting empty chat history"""
        user_id = str(ObjectId())
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter([])
        chat_history_model.chat_history.find.return_value = mock_cursor
        
        result = chat_history_model.get_user_history(user_id)
        
        assert len(result) == 0
    
    def test_get_user_history_with_limit(self, chat_history_model):
        """Test getting user history with limit"""
        user_id = str(ObjectId())
        limit = 10
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = iter([])
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        chat_history_model.chat_history.find.return_value = mock_cursor
        
        result = chat_history_model.get_user_history(user_id, limit=limit)
        
        mock_cursor.sort.assert_called_once_with('timestamp', 1)
        mock_cursor.limit.assert_called_once_with(limit)
    
    def test_clear_user_history_success(self, chat_history_model):
        """Test clearing user chat history"""
        user_id = str(ObjectId())
        deleted_count = 5
        
        mock_result = Mock()
        mock_result.deleted_count = deleted_count
        chat_history_model.chat_history.delete_many.return_value = mock_result
        
        result = chat_history_model.clear_user_history(user_id)
        
        assert result == deleted_count
        chat_history_model.chat_history.delete_many.assert_called_once_with({'user_id': user_id, 'session_id': 'default'})
    
    def test_clear_user_history_empty(self, chat_history_model):
        """Test clearing history when no messages exist"""
        user_id = str(ObjectId())
        
        mock_result = Mock()
        mock_result.deleted_count = 0
        chat_history_model.chat_history.delete_many.return_value = mock_result
        
        result = chat_history_model.clear_user_history(user_id)
        
        assert result == 0

