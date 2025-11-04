"""
Unit tests for retriever_helper utility functions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.retriever_helper import get_user_retriever, check_user_has_documents


class TestRetrieverHelper:
    """Test suite for retriever helper functions"""
    
    def test_get_user_retriever(self, mock_user_id):
        """Test getting user retriever"""
        with patch('utils.retriever_helper.get_vector_service') as mock_get_service:
            mock_service = Mock()
            mock_vector_store = Mock()
            mock_retriever = Mock()
            
            mock_service.get_user_vector_store.return_value = mock_vector_store
            mock_vector_store.as_retriever.return_value = mock_retriever
            mock_get_service.return_value = mock_service
            
            k = 5
            retriever = get_user_retriever(mock_user_id, k=k)
            
            assert retriever == mock_retriever
            mock_service.get_user_vector_store.assert_called_once_with(mock_user_id)
            mock_vector_store.as_retriever.assert_called_once()
            call_args = mock_vector_store.as_retriever.call_args[1]
            assert call_args['search_kwargs']['k'] == k
            assert call_args['search_kwargs']['filter']['user_id'] == mock_user_id
    
    def test_get_user_retriever_default_k(self, mock_user_id):
        """Test getting user retriever with default k value"""
        with patch('utils.retriever_helper.get_vector_service') as mock_get_service:
            mock_service = Mock()
            mock_vector_store = Mock()
            mock_retriever = Mock()
            
            mock_service.get_user_vector_store.return_value = mock_vector_store
            mock_vector_store.as_retriever.return_value = mock_retriever
            mock_get_service.return_value = mock_service
            
            retriever = get_user_retriever(mock_user_id)
            
            call_args = mock_vector_store.as_retriever.call_args[1]
            assert call_args['search_kwargs']['k'] == 4  # Default value
    
    def test_check_user_has_documents_true(self, mock_user_id):
        """Test checking if user has documents when they do"""
        with patch('utils.retriever_helper.get_vector_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_user_documents.return_value = ['doc1.pdf', 'doc2.pdf']
            mock_get_service.return_value = mock_service
            
            result = check_user_has_documents(mock_user_id)
            
            assert result is True
            mock_service.list_user_documents.assert_called_once_with(mock_user_id)
    
    def test_check_user_has_documents_false(self, mock_user_id):
        """Test checking if user has documents when they don't"""
        with patch('utils.retriever_helper.get_vector_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_user_documents.return_value = []
            mock_get_service.return_value = mock_service
            
            result = check_user_has_documents(mock_user_id)
            
            assert result is False
    
    def test_check_user_has_documents_empty_list(self, mock_user_id):
        """Test checking documents with empty list"""
        with patch('utils.retriever_helper.get_vector_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_user_documents.return_value = []
            mock_get_service.return_value = mock_service
            
            result = check_user_has_documents(mock_user_id)
            
            assert result is False

