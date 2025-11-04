"""
Unit tests for AuthController
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from controllers.auth_controller import AuthController
from datetime import datetime, timedelta
import jwt
import bcrypt


class TestAuthController:
    """Test suite for AuthController"""
    
    @pytest.fixture
    def auth_controller(self, mock_mongo_client):
        """Create AuthController instance with mocked dependencies"""
        with patch('controllers.auth_controller.UserModel') as mock_user_model_class:
            mock_user_model = Mock()
            mock_user_model.client.admin.command.return_value = True
            mock_user_model_class.return_value = mock_user_model
            
            controller = AuthController()
            controller.user_model = mock_user_model
            return controller
    
    def test_hash_password(self, auth_controller):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = auth_controller.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Verify the hash can be checked
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def test_verify_password_correct(self, auth_controller):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = auth_controller.hash_password(password)
        
        assert auth_controller.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, auth_controller):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = auth_controller.hash_password(password)
        
        assert auth_controller.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_invalid_hash(self, auth_controller):
        """Test password verification with invalid hash"""
        password = "TestPassword123!"
        invalid_hash = "invalid_hash_string"
        
        assert auth_controller.verify_password(password, invalid_hash) is False
    
    def test_generate_token(self, auth_controller):
        """Test JWT token generation"""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        
        token = auth_controller.generate_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = jwt.decode(
            token, 
            auth_controller.jwt_secret, 
            algorithms=[auth_controller.jwt_algorithm]
        )
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_verify_token_valid(self, auth_controller):
        """Test token verification with valid token"""
        user_id = "507f1f77bcf86cd799439011"
        email = "test@example.com"
        
        token = auth_controller.generate_token(user_id, email)
        payload = auth_controller.verify_token(token)
        
        assert payload['user_id'] == user_id
        assert payload['email'] == email
    
    def test_verify_token_expired(self, auth_controller):
        """Test token verification with expired token"""
        # Create an expired token manually
        payload = {
            'user_id': 'test_id',
            'email': 'test@example.com',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(
            payload, 
            auth_controller.jwt_secret, 
            algorithm=auth_controller.jwt_algorithm
        )
        
        with pytest.raises(Exception) as exc_info:
            auth_controller.verify_token(expired_token)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_verify_token_invalid(self, auth_controller):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(Exception) as exc_info:
            auth_controller.verify_token(invalid_token)
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_signup_success(self, auth_controller, mock_user_data):
        """Test successful user signup"""
        auth_controller.user_model.find_user_by_email.return_value = None
        auth_controller.user_model.create_user.return_value = "507f1f77bcf86cd799439011"
        
        result = auth_controller.signup(mock_user_data)
        
        assert result['success'] is True
        assert result['status_code'] == 201
        assert 'token' in result['data']
        assert result['data']['email'] == mock_user_data['email']
        auth_controller.user_model.create_user.assert_called_once()
    
    def test_signup_duplicate_email(self, auth_controller, mock_user_data):
        """Test signup with duplicate email"""
        auth_controller.user_model.find_user_by_email.return_value = {
            '_id': 'existing_id',
            'email': mock_user_data['email']
        }
        
        result = auth_controller.signup(mock_user_data)
        
        assert result['success'] is False
        assert result['status_code'] == 409
        assert 'already exists' in result['message'].lower()
        auth_controller.user_model.create_user.assert_not_called()
    
    def test_signup_database_error(self, auth_controller, mock_user_data):
        """Test signup with database error"""
        auth_controller.user_model.find_user_by_email.return_value = None
        auth_controller.user_model.create_user.side_effect = Exception("Database error")
        
        result = auth_controller.signup(mock_user_data)
        
        assert result['success'] is False
        assert result['status_code'] == 500
        assert 'failed' in result['message'].lower()
    
    def test_login_success(self, auth_controller, mock_login_credentials, mock_user_db_data):
        """Test successful login"""
        # Mock the password to be verifiable
        correct_password = mock_login_credentials['password']
        hashed_password = auth_controller.hash_password(correct_password)
        mock_user_db_data['password'] = hashed_password
        
        auth_controller.user_model.find_user_by_email.return_value = mock_user_db_data
        
        result = auth_controller.login(mock_login_credentials)
        
        assert result['success'] is True
        assert result['status_code'] == 200
        assert 'token' in result['data']
        assert result['data']['email'] == mock_login_credentials['email']
    
    def test_login_invalid_email(self, auth_controller, mock_login_credentials):
        """Test login with non-existent email"""
        auth_controller.user_model.find_user_by_email.return_value = None
        
        result = auth_controller.login(mock_login_credentials)
        
        assert result['success'] is False
        assert result['status_code'] == 401
        assert 'invalid' in result['message'].lower()
    
    def test_login_invalid_password(self, auth_controller, mock_login_credentials, mock_user_db_data):
        """Test login with incorrect password"""
        # Use a different password than what's hashed
        mock_user_db_data['password'] = auth_controller.hash_password("DifferentPassword")
        auth_controller.user_model.find_user_by_email.return_value = mock_user_db_data
        
        result = auth_controller.login(mock_login_credentials)
        
        assert result['success'] is False
        assert result['status_code'] == 401
        assert 'invalid' in result['message'].lower()
    
    def test_login_database_error(self, auth_controller, mock_login_credentials):
        """Test login with database error"""
        auth_controller.user_model.find_user_by_email.side_effect = Exception("Database error")
        
        result = auth_controller.login(mock_login_credentials)
        
        assert result['success'] is False
        assert result['status_code'] == 500
        assert 'failed' in result['message'].lower()

