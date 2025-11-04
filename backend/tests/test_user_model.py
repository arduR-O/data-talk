"""
Unit tests for UserModel
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from models.users import UserModel
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError


class TestUserModel:
    """Test suite for UserModel"""
    
    @pytest.fixture
    def user_model(self):
        """Create UserModel instance with mocked MongoDB"""
        with patch('models.users.MongoClient') as mock_client_class:
            mock_client = Mock()
            mock_db = Mock()
            mock_collection = Mock()
            
            mock_client_class.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_db.users = mock_collection
            
            model = UserModel()
            model.client = mock_client
            model.db = mock_db
            model.users = mock_collection
            
            return model
    
    def test_create_user_success(self, user_model):
        """Test successful user creation"""
        user_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'password': 'hashed_password'
        }
        
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        user_model.users.insert_one.return_value = mock_result
        
        user_id = user_model.create_user(user_data)
        
        assert isinstance(user_id, str)
        assert user_id == str(mock_result.inserted_id)
        user_model.users.insert_one.assert_called_once()
        # Verify created_at and updated_at were added
        call_args = user_model.users.insert_one.call_args[0][0]
        assert 'created_at' in call_args
        assert 'updated_at' in call_args
    
    def test_create_user_duplicate_email(self, user_model):
        """Test user creation with duplicate email"""
        user_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john@example.com',
            'password': 'hashed_password'
        }
        
        user_model.users.insert_one.side_effect = DuplicateKeyError("duplicate key")
        
        with pytest.raises(Exception) as exc_info:
            user_model.create_user(user_data)
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_find_user_by_email_success(self, user_model):
        """Test finding user by email"""
        email = 'john@example.com'
        mock_user = {
            '_id': ObjectId(),
            'email': email,
            'firstName': 'John'
        }
        
        user_model.users.find_one.return_value = mock_user
        
        result = user_model.find_user_by_email(email)
        
        assert result == mock_user
        user_model.users.find_one.assert_called_once_with({'email': email.lower()})
    
    def test_find_user_by_email_not_found(self, user_model):
        """Test finding user by email when not found"""
        email = 'nonexistent@example.com'
        user_model.users.find_one.return_value = None
        
        result = user_model.find_user_by_email(email)
        
        assert result is None
    
    def test_find_user_by_id_success(self, user_model):
        """Test finding user by ID"""
        user_id = str(ObjectId())
        mock_user = {
            '_id': ObjectId(user_id),
            'email': 'john@example.com'
        }
        
        user_model.users.find_one.return_value = mock_user
        
        result = user_model.find_user_by_id(user_id)
        
        assert result == mock_user
    
    def test_find_user_by_id_invalid(self, user_model):
        """Test finding user by invalid ID"""
        invalid_id = 'invalid_id'
        
        result = user_model.find_user_by_id(invalid_id)
        
        assert result is None
    
    def test_find_user_by_id_not_found(self, user_model):
        """Test finding user by ID when not found"""
        user_id = str(ObjectId())
        user_model.users.find_one.return_value = None
        
        result = user_model.find_user_by_id(user_id)
        
        assert result is None
    
    def test_update_db_url_success(self, user_model):
        """Test updating database URL"""
        user_id = str(ObjectId())
        db_url = 'postgresql://test:test@localhost:5432/testdb'
        
        mock_user = {
            '_id': ObjectId(user_id),
            'email': 'john@example.com',
            'db_url': db_url
        }
        
        mock_update_result = Mock()
        mock_update_result.matched_count = 1
        user_model.users.update_one.return_value = mock_update_result
        user_model.users.find_one.return_value = mock_user
        
        result = user_model.update_db_url(user_id, db_url)
        
        assert result == mock_user
        user_model.users.update_one.assert_called_once()
        call_args = user_model.users.update_one.call_args
        assert call_args[0][0] == {'_id': ObjectId(user_id)}
        assert '$set' in call_args[0][1]
        assert call_args[0][1]['$set']['db_url'] == db_url
    
    def test_update_db_url_user_not_found(self, user_model):
        """Test updating DB URL for non-existent user"""
        user_id = str(ObjectId())
        db_url = 'postgresql://test:test@localhost:5432/testdb'
        
        mock_update_result = Mock()
        mock_update_result.matched_count = 0
        user_model.users.update_one.return_value = mock_update_result
        
        result = user_model.update_db_url(user_id, db_url)
        
        assert result is None
    
    def test_get_db_url_success(self, user_model):
        """Test getting database URL"""
        user_id = str(ObjectId())
        db_url = 'postgresql://test:test@localhost:5432/testdb'
        
        mock_user = {
            '_id': ObjectId(user_id),
            'db_url': db_url
        }
        
        user_model.users.find_one.return_value = mock_user
        
        result = user_model.get_db_url(user_id)
        
        assert result == db_url
    
    def test_get_db_url_no_url(self, user_model):
        """Test getting DB URL when user has no URL"""
        user_id = str(ObjectId())
        
        mock_user = {
            '_id': ObjectId(user_id),
            'email': 'john@example.com'
        }
        
        user_model.users.find_one.return_value = mock_user
        
        result = user_model.get_db_url(user_id)
        
        assert result is None
    
    def test_get_db_url_user_not_found(self, user_model):
        """Test getting DB URL for non-existent user"""
        user_id = str(ObjectId())
        user_model.users.find_one.return_value = None
        
        result = user_model.get_db_url(user_id)
        
        assert result is None

