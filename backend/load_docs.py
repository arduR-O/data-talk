import os 
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone 
from langchain_community.document_loaders import PyPDFLoader
from pinecone import ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()

if not os.environ.get("PINECONE_API_KEY"):
  os.environ["PINECONE_API_KEY"] = getpass.getpass("Enter API key for Pinecone")
  
if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for NVIDIA: ")
  

def obtain_pdfs(context_folder_path : str):
    """
    Returns a list of PDF filenames from the specified context folder path.

    Args:
        context_folder_path (str): Path to the folder containing context files.

    Returns:
        List[str]: List of PDF filenames found in the folder.
    """
    files: list[str] = os.listdir(context_folder_path)
    pdfs: list[str] = []
    for file in files:
        if file.lower().endswith('.pdf'):
            pdfs.append(file)
    print("pdf files: ", pdfs)
    return pdfs

def init_pc_vector_store(index_name: str, embeddings: GoogleGenerativeAIEmbeddings) -> PineconeVectorStore:
    """
    Initializes a Pinecone vector store for document embeddings.

    Args:
        index_name (str): Name of the Pinecone index.
        embeddings (GoogleGenerativeAIEmbeddings): Embedding model instance.

    Returns:
        PineconeVectorStore: Initialized vector store object.
    """
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if index_name not in pc.list_indexes().names():
        print("Creating index")
        pc.create_index(
            name=index_name,
            metric="cosine",
            dimension=3072,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(pc.describe_index(index_name))
    index = pc.Index(index_name)
    return PineconeVectorStore(embedding=embeddings, index=index)

def add_to_db(context_folder_path: str, pdf_files: list[str], vector_store: PineconeVectorStore) -> None:
    """
    Loads PDF documents, splits them into chunks, and adds them to the vector store.

    Args:
        context_folder_path (str): Path to the folder containing PDF files.
        pdf_files (list[str]): List of PDF filenames to process.
        vector_store (PineconeVectorStore): Vector store to add documents to.
    """
    for pdf in tqdm(pdf_files):
        path = os.path.join(context_folder_path, pdf)
        loader = PyPDFLoader(path)
        docs = loader.load()  # TODO: explore async loading
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(docs)
        _ = vector_store.add_documents(documents=all_splits)


def get_vector_store(index_name: str = "data-talk", model: str = "models/gemini-embedding-001") -> PineconeVectorStore:
    """
    Initializes and returns a PineconeVectorStore for use in other modules.

    Args:
        index_name (str): Name of the Pinecone index.
        model (str): Embedding model name.

    Returns:
        PineconeVectorStore: Initialized vector store object.
    """
    embeddings: GoogleGenerativeAIEmbeddings = GoogleGenerativeAIEmbeddings(model=model)
    return init_pc_vector_store(index_name, embeddings)


if __name__ == "__main__":
    context_path: str = "./context"
    pdfs: list[str] = obtain_pdfs(context_path)
    vector_store: PineconeVectorStore = get_vector_store()
    add_to_db(context_path, pdfs, vector_store)

