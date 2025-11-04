# Unit Tests for DataTalk Backend

This directory contains comprehensive unit tests for the DataTalk backend API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_auth_controller.py   # Tests for authentication controller
├── test_chat_controller.py  # Tests for chat controller
├── test_user_model.py       # Tests for user model
├── test_chat_history_model.py  # Tests for chat history model
├── test_retriever_helper.py # Tests for retriever utility functions
└── test_main.py             # Tests for main FastAPI app
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_auth_controller.py
```

### Run Specific Test Class

```bash
pytest tests/test_auth_controller.py::TestAuthController
```

### Run Specific Test Method

```bash
pytest tests/test_auth_controller.py::TestAuthController::test_signup_success
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run with Verbose Output

```bash
pytest -v
```

## Test Coverage

The test suite covers:

- **AuthController**: Password hashing, JWT token generation/verification, signup, login
- **ChatController**: Message processing, history management, error handling
- **UserModel**: User CRUD operations, database URL management
- **ChatHistoryModel**: Message storage and retrieval
- **Retriever Helper**: Vector store retrieval functions
- **Main API**: Health checks and status endpoints

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for files, `test_*` for functions
2. Use fixtures from `conftest.py` for common test data
3. Mock external dependencies (database, APIs, etc.)
4. Test both success and error cases
5. Keep tests isolated and independent

## Example Test

```python
def test_function_success(self, fixture):
    """Test description"""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result["success"] is True
    assert result["status_code"] == 200
```

## Notes

- All tests use mocking to avoid dependencies on external services
- MongoDB, Pinecone, and other external services are mocked
- Environment variables are set in `conftest.py` for testing
- Tests are designed to run quickly and independently

