"""
Unit tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app


class TestMain:
    """Test suite for main FastAPI application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DataTalk API Server"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "services" in data
        assert "database" in data["services"]
        assert "llm" in data["services"]
        assert "vector_store" in data["services"]
    
    def test_api_status(self, client):
        """Test API status endpoint"""
        response = client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "auth" in data["endpoints"]
        assert "chat" in data["endpoints"]

