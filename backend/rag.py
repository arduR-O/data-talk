# rag_langgraph.py
import getpass
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from load_docs import get_vector_store
from langchain_core.tools import tool
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from pypdf import PdfReader
from typing_extensions import TypedDict

load_dotenv()

# --- Groq API key ---
if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")

# --- LLM setup ---
llm = ChatGroq(
    model="qwen/qwen3-32b"
)

# --- Vector store ---
vector_store = get_vector_store()



# --- Define state ---
class State(TypedDict):
    question: str
    retrieved_context: str
    answer: str

# --- Tools as LangGraph steps ---
def retrieve_context(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    if retrieved_docs:
        context_text = "\n".join([doc.page_content for doc in retrieved_docs])
    else:
        context_text = ""
    return {"retrieved_context": context_text}

def generate_answer(state: State):
    prompt = f"""
    You are an assistant for question-answering tasks. 
    Use the following context to answer the user's question concisely and conversationally.
    
    Context:
    {state['retrieved_context']}
    
    Question:
    {state['question']}
    
    If the answer is not in the context, just say you don't know.
    """
    response = llm.invoke(prompt)
    return {"answer": response.content}

# --- Build LangGraph ---
graph_builder = StateGraph(State).add_sequence(
    [retrieve_context, generate_answer]
)
graph_builder.add_edge(START, "retrieve_context")
graph = graph_builder.compile()


