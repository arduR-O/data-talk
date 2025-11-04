"""
Unit tests for ChatController
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from controllers.chat_controller import ChatController
from langchain_core.messages import HumanMessage, AIMessage
from bson import ObjectId


class TestChatController:
    """Test suite for ChatController"""
    
    @pytest.fixture
    def chat_controller(self):
        """Create ChatController instance with mocked dependencies"""
        with patch('controllers.chat_controller.ChatHistoryModel') as mock_chat_model_class, \
             patch('controllers.chat_controller.UserModel') as mock_user_model_class, \
             patch('controllers.chat_controller.get_orchestrator') as mock_get_orchestrator:
            
            mock_chat_model = Mock()
            mock_user_model = Mock()
            mock_orchestrator = Mock()
            
            mock_chat_model_class.return_value = mock_chat_model
            mock_user_model_class.return_value = mock_user_model
            mock_get_orchestrator.return_value = mock_orchestrator
            
            controller = ChatController()
            controller.chat_history_model = mock_chat_model
            controller.user_model = mock_user_model
            controller.orchestrator = mock_orchestrator
            
            return controller
    
    def test_process_message_success(self, chat_controller, mock_user_id):
        """Test successful message processing"""
        question = "What is the weather?"
        db_url = "postgresql://test:test@localhost:5432/testdb"
        
        # Mock dependencies
        chat_controller.user_model.get_db_url.return_value = db_url
        chat_controller.chat_history_model.get_user_history.return_value = []
        chat_controller.orchestrator.chat.return_value = {
            'answer': 'The weather is sunny.',
            'routing': 'general',
            'resources': {'database': True, 'documents': False}
        }
        
        result = chat_controller.process_message(mock_user_id, question)
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert result['data']['response'] == 'The weather is sunny.'
        assert result['data']['routing'] == 'general'
        chat_controller.chat_history_model.add_message.assert_called()
        chat_controller.orchestrator.chat.assert_called_once()
    
    def test_process_message_with_history(self, chat_controller, mock_user_id):
        """Test message processing with conversation history"""
        question = "What about tomorrow?"
        db_url = "postgresql://test:test@localhost:5432/testdb"
        
        # Mock history
        history_messages = [
            {'type': 'user', 'content': 'What is the weather today?'},
            {'type': 'assistant', 'content': 'The weather is sunny.'}
        ]
        
        chat_controller.user_model.get_db_url.return_value = db_url
        chat_controller.chat_history_model.get_user_history.return_value = history_messages
        chat_controller.orchestrator.chat.return_value = {
            'answer': 'Tomorrow will be cloudy.',
            'routing': 'general',
            'resources': {'database': True, 'documents': False}
        }
        
        result = chat_controller.process_message(mock_user_id, question)
        
        assert result['success'] is True
        # Verify orchestrator was called with conversation history
        call_args = chat_controller.orchestrator.chat.call_args
        assert call_args[1]['conversation_history'] is not None
        assert len(call_args[1]['conversation_history']) == 2
    
    def test_process_message_no_db_url(self, chat_controller, mock_user_id):
        """Test message processing without database URL"""
        question = "What is the weather?"
        
        chat_controller.user_model.get_db_url.return_value = None
        chat_controller.chat_history_model.get_user_history.return_value = []
        chat_controller.orchestrator.chat.return_value = {
            'answer': 'I cannot access the database.',
            'routing': 'general',
            'resources': {'database': False, 'documents': False}
        }
        
        result = chat_controller.process_message(mock_user_id, question)
        
        assert result['success'] is True
        call_args = chat_controller.orchestrator.chat.call_args
        assert call_args[1]['db_url'] is None
    
    def test_process_message_error(self, chat_controller, mock_user_id):
        """Test message processing with error"""
        question = "What is the weather?"
        
        chat_controller.user_model.get_db_url.side_effect = Exception("Database error")
        
        result = chat_controller.process_message(mock_user_id, question)
        
        assert result['success'] is False
        assert result['status_code'] == 500
        assert 'failed' in result['message'].lower()
    
    def test_get_history_success(self, chat_controller, mock_user_id, mock_chat_message):
        """Test getting chat history"""
        chat_controller.chat_history_model.get_user_history.return_value = [mock_chat_message]
        
        result = chat_controller.get_history(mock_user_id)
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert len(result['data']['messages']) == 1
        assert result['data']['messages'][0]['content'] == mock_chat_message['content']
    
    def test_get_history_empty(self, chat_controller, mock_user_id):
        """Test getting empty chat history"""
        chat_controller.chat_history_model.get_user_history.return_value = []
        
        result = chat_controller.get_history(mock_user_id)
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert len(result['data']['messages']) == 0
    
    def test_get_history_error(self, chat_controller, mock_user_id):
        """Test getting history with error"""
        chat_controller.chat_history_model.get_user_history.side_effect = Exception("Database error")
        
        result = chat_controller.get_history(mock_user_id)
        
        assert result['success'] is False
        assert result['status_code'] == 500
    
    def test_clear_history_success(self, chat_controller, mock_user_id):
        """Test clearing chat history"""
        deleted_count = 5
        chat_controller.chat_history_model.clear_user_history.return_value = deleted_count
        
        result = chat_controller.clear_history(mock_user_id)
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert result['data']['deleted_count'] == deleted_count
    
    def test_clear_history_error(self, chat_controller, mock_user_id):
        """Test clearing history with error"""
        chat_controller.chat_history_model.clear_user_history.side_effect = Exception("Database error")
        
        result = chat_controller.clear_history(mock_user_id)
        
        assert result['success'] is False
        assert result['status_code'] == 500

