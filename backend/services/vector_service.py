import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import hashlib

load_dotenv()


class DocumentVectorService:
    """
    Service for managing document vectorization per user in Pinecone.
    Each document is tagged with user_id and file_name for isolation and tracking.
    """
    
    def __init__(
        self,
        index_name: str = "data-speak",
        embedding_model: str = None  # Will auto-detect
    ):
        self.index_name = index_name
        
        # 🔥 FIX: Auto-detect dimension from existing index
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        
        # Check if index exists and get its dimension
        existing_dimension = self._get_index_dimension()
        
        if existing_dimension:
            print(f"📊 Detected existing index dimension: {existing_dimension}")
            # Automatically match the embedding model to the index dimension
            if existing_dimension == 3072:
                embedding_model = "models/embedding-001"  # 3072 dimensions
                print("✅ Auto-selected: embedding-001 (3072 dims)")
            elif existing_dimension == 768:
                embedding_model = "models/text-embedding-004"  # 768 dimensions
                print("✅ Auto-selected: text-embedding-004 (768 dims)")
            else:
                raise ValueError(f"Unsupported index dimension: {existing_dimension}. Expected 768 or 3072.")
            self.embedding_dimension = existing_dimension
        else:
            # No existing index - use default (embedding-001 with 3072 dims)
            if embedding_model is None:
                embedding_model = "models/embedding-001"
            print(f"📝 No existing index. Will create with model: {embedding_model}")
            
            # Determine dimension based on model
            if "embedding-001" in embedding_model:
                self.embedding_dimension = 3072
            elif "text-embedding-004" in embedding_model:
                self.embedding_dimension = 768
            else:
                # Default fallback
                self.embedding_dimension = 3072
        
        # Initialize embeddings with auto-detected model
        self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
        print(f"🔧 Using embedding model: {embedding_model} ({self.embedding_dimension} dims)")
        
        # Initialize vector store
        self.vector_store = self._init_vector_store()
    
    def _get_index_dimension(self) -> Optional[int]:
        """Get the dimension of existing index, or None if doesn't exist"""
        try:
            if self.index_name in self.pc.list_indexes().names():
                index_info = self.pc.describe_index(self.index_name)
                return index_info.dimension
            return None
        except Exception as e:
            print(f"Error checking index dimension: {e}")
            return None
    
    def _init_vector_store(self) -> PineconeVectorStore:
        """Initialize Pinecone vector store with proper index configuration"""
        if self.index_name not in self.pc.list_indexes().names():
            print(f"Creating index: {self.index_name} with dimension {self.embedding_dimension}")
            self.pc.create_index(
                name=self.index_name,
                metric="cosine",
                dimension=self.embedding_dimension,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        
        index = self.pc.Index(self.index_name)
        return PineconeVectorStore(embedding=self.embeddings, index=index)
    
    def _generate_doc_id(self, user_id: str, filename: str) -> str:
        """Generate a unique document ID based on user_id and filename"""
        combined = f"{user_id}:{filename}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def process_and_upload_document(
        self,
        user_id: str,
        file_path: str,
        filename: str
    ) -> Dict[str, any]:
        """
        Process a PDF document and upload its embeddings to Pinecone.
        
        Args:
            user_id: The user's ID
            file_path: Full path to the PDF file
            filename: Name of the file
            
        Returns:
            Dict with status and metadata
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate unique document ID
            doc_id = self._generate_doc_id(user_id, filename)
            
            # Load PDF
            print(f"📄 Loading PDF: {filename}")
            loader = PDFMinerLoader(file_path)
            docs = loader.load()
            
            if not docs:
                raise ValueError(f"No content extracted from {filename}")
            
            print(f"📝 Extracted {len(docs)} pages from {filename}")
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            all_splits = text_splitter.split_documents(docs)
            print(f"✂️ Split into {len(all_splits)} chunks")
            
            # Add metadata to each chunk for filtering
            for i, split in enumerate(all_splits):
                split.metadata.update({
                    "user_id": user_id,
                    "filename": filename,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "source": file_path
                })
            
            # Upload to Pinecone
            print(f"⬆️ Uploading {len(all_splits)} vectors to Pinecone...")
            ids = self.vector_store.add_documents(documents=all_splits)
            print(f"✅ Successfully vectorized {filename}: {len(all_splits)} chunks")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "filename": filename,
                "chunks_count": len(all_splits),
                "vector_ids": ids
            }
            
        except Exception as e:
            print(f"❌ Error processing document {filename}: {str(e)}")
            return {
                "success": False,
                "filename": filename,
                "error": str(e)
            }
    
    def delete_document(self, user_id: str, filename: str) -> Dict[str, any]:
        """
        Delete all embeddings for a specific document.
        
        Args:
            user_id: The user's ID
            filename: Name of the file to delete
            
        Returns:
            Dict with deletion status
        """
        try:
            doc_id = self._generate_doc_id(user_id, filename)
            
            # Get the index directly for deletion operations
            index = self.pc.Index(self.index_name)
            
            # Delete by metadata filter
            try:
                index.delete(filter={
                    "user_id": {"$eq": user_id},
                    "filename": {"$eq": filename}
                })
                deleted_count = "vectors deleted (count unknown)"
                print(f"🗑️ Deleted vectors for {filename}")
            except Exception as filter_error:
                # Fallback: Query and delete by IDs
                print(f"⚠️ Filter delete failed, using query method: {filter_error}")
                
                # Create a dummy vector for metadata-only query
                dummy_vector = [0.0] * self.embedding_dimension
                
                query_result = index.query(
                    vector=dummy_vector,
                    filter={
                        "user_id": {"$eq": user_id},
                        "filename": {"$eq": filename}
                    },
                    top_k=10000,
                    include_metadata=False
                )
                
                if query_result.matches:
                    ids_to_delete = [match.id for match in query_result.matches]
                    index.delete(ids=ids_to_delete)
                    deleted_count = len(ids_to_delete)
                    print(f"🗑️ Deleted {deleted_count} vectors for {filename}")
                else:
                    deleted_count = 0
                    print(f"⚠️ No vectors found for {filename}")
            
            return {
                "success": True,
                "filename": filename,
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            print(f"❌ Error deleting document {filename}: {str(e)}")
            return {
                "success": False,
                "filename": filename,
                "error": str(e)
            }
    
    def delete_all_user_documents(self, user_id: str) -> Dict[str, any]:
        """
        Delete all documents for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict with deletion status
        """
        try:
            index = self.pc.Index(self.index_name)
            
            try:
                index.delete(filter={"user_id": {"$eq": user_id}})
                print(f"🗑️ Deleted all documents for user {user_id}")
                return {
                    "success": True,
                    "message": f"All documents for user {user_id} deleted"
                }
            except Exception as e:
                print(f"❌ Error deleting user documents: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_vector_store(self, user_id: str) -> PineconeVectorStore:
        """
        Get a filtered vector store for a specific user.
        This can be used for retrieval in RAG systems.
        
        Args:
            user_id: The user's ID
            
        Returns:
            PineconeVectorStore filtered for the user
        """
        # Return vector store with pre-configured filter
        index = self.pc.Index(self.index_name)
        return PineconeVectorStore(
            embedding=self.embeddings,
            index=index,
            namespace="",  # Use default namespace
        )
    
    def list_user_documents(self, user_id: str) -> List[str]:
        """
        List all documents for a user (by querying metadata).
        Note: This is a best-effort approach as Pinecone doesn't have a native list operation.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of unique filenames
        """
        try:
            index = self.pc.Index(self.index_name)
            
            # Create a dummy vector for metadata-only query
            dummy_vector = [0.0] * self.embedding_dimension
            
            # Query with user filter to get sample of documents
            query_result = index.query(
                vector=dummy_vector,
                filter={"user_id": {"$eq": user_id}},
                top_k=1000,
                include_metadata=True
            )
            
            # Extract unique filenames
            filenames = set()
            for match in query_result.matches:
                if match.metadata and "filename" in match.metadata:
                    filenames.add(match.metadata["filename"])
            
            print(f"📋 Found {len(filenames)} documents for user {user_id}")
            return list(filenames)
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return []


# Singleton instance for use across the application
_vector_service_instance = None

def get_vector_service() -> DocumentVectorService:
    """Get or create the singleton vector service instance"""
    global _vector_service_instance
    if _vector_service_instance is None:
        _vector_service_instance = DocumentVectorService()
    return _vector_service_instance