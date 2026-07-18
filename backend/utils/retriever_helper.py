from services.vector_service import get_vector_service
from langchain_core.retrievers import BaseRetriever


def get_user_retriever(user_id: str, k: int = 4) -> BaseRetriever:
    """
    Get a retriever configured for a specific user's documents.
    
    This retriever will only search through documents uploaded by the specified user,
    ensuring complete isolation between users.
    
    Args:
        user_id: The user's ID
        k: Number of documents to retrieve (default: 4)
        
    Returns:
        BaseRetriever: A retriever configured for the user's documents
        
    Example:
        ```python
        retriever = get_user_retriever(user_id="123", k=5)
        docs = retriever.get_relevant_documents("What is machine learning?")
        ```
    """
    vector_service = get_vector_service()
    vector_store = vector_service.get_user_vector_store(user_id)
    
    # Return a retriever with the user's documents
    return vector_store.as_retriever(
        search_kwargs={
            "k": k,
            "filter": {"user_id": user_id}  # Ensures only user's docs are retrieved
        }
    )


def check_user_has_documents(user_id: str) -> bool:
    """
    Check if a user has any vectorized documents.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if user has documents, False otherwise
    """
    vector_service = get_vector_service()
    if not vector_service.available:
        return False
    documents = vector_service.list_user_documents(user_id)
    return len(documents) > 0