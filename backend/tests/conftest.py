"""
Pytest configuration and fixtures for unit tests
"""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from bson import ObjectId
from datetime import datetime

# Set test environment variables
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-unit-tests'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['JWT_EXPIRATION_HOURS'] = '24'
os.environ['MONGODB_URI'] = 'mongodb://test:test@localhost:27017/test'
os.environ['DATABASE_NAME'] = 'test_datatalk'
os.environ['GROQ_API_KEY'] = 'test-groq-key'
os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
os.environ['DB_URL'] = 'postgresql://test:test@localhost:5432/testdb'


@pytest.fixture
def mock_user_data():
    """Sample user data for testing"""
    return {
        'firstName': 'John',
        'lastName': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'SecurePassword123!'
    }


@pytest.fixture
def mock_user_db_data():
    """Sample user data as stored in database"""
    user_id = str(ObjectId())
    return {
        '_id': ObjectId(user_id),
        'firstName': 'John',
        'lastName': 'Doe',
        'email': 'john.doe@example.com',
        'password': '$2b$12$hashedpassword',  # Mock bcrypt hash
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


@pytest.fixture
def mock_login_credentials():
    """Sample login credentials"""
    return {
        'email': 'john.doe@example.com',
        'password': 'SecurePassword123!'
    }


@pytest.fixture
def mock_user_id():
    """Sample user ID"""
    return str(ObjectId())


@pytest.fixture
def mock_chat_message():
    """Sample chat message"""
    return {
        'id': str(ObjectId()),
        'type': 'user',
        'content': 'What is the weather?',
        'timestamp': datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client"""
    client = Mock()
    db = Mock()
    collection = Mock()
    
    client.__getitem__.return_value = db
    db.__getitem__.return_value = collection
    
    return client, db, collection


@pytest.fixture
def mock_vector_service():
    """Mock vector service"""
    service = Mock()
    service.get_user_vector_store.return_value = Mock()
    service.list_user_documents.return_value = ['document1.pdf', 'document2.pdf']
    service.process_and_upload_document.return_value = {
        'success': True,
        'doc_id': 'test-doc-id',
        'filename': 'test.pdf',
        'chunks_count': 5
    }
    return service

