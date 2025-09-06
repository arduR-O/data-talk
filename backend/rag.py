import getpass
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone 
from langchain_community.document_loaders import PyPDFLoader
from pinecone import ServerlessSpec
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain import hub

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")
  
if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for NVIDIA: ")

if not os.environ.get("PINECONE_API_KEY"):
  os.environ["PINECONE_API_KEY"] = getpass.getpass("Enter API key for Pinecone")
  
llm = ChatGroq(
    model="gemma2-9b-it"
)

# print(llm.invoke("Hello there"))


embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
pc = Pinecone(api_key = os.environ["PINECONE_API_KEY"])
index_name = "data-talk"
if index_name not in pc.list_indexes().names():
    print("Creating index")
    pc.create_index(name=index_name,
                      metric="cosine",
                      dimension=3072,
                      spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                        ),
    )
    print(pc.describe_index(index_name))

index = pc.Index(index_name)
vector_store = PineconeVectorStore(embedding = embeddings, index = index)

#for now only covering OCR-ed pdfs, ocr can be used added later
# loader = PyPDFLoader("./deeplearningbook.pdf") #!TODO: make a default folder for pdf uploades, then use os to find all pdfs and then ocr, store docs in database. 
# docs = loader.load() #!TODO: explore async loading


# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# all_splits = text_splitter.split_documents(docs)

# _ = vector_store.add_documents(documents=all_splits)
# print(docs[15].page_content[:500])

prompt = hub.pull("rlm/rag-prompt")


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

response = graph.invoke({"question": "Kindly return a list of all the chapters covered in the textbook"})
print(response["answer"])