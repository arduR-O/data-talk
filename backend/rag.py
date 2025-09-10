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
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage


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
    conversation_history: list[BaseMessage]

# --- Tools as LangGraph steps ---
def retrieve_context(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    if retrieved_docs:
        context_text = "\n".join([doc.page_content for doc in retrieved_docs])
    else:
        context_text = ""
    state["conversation_history"].append(AIMessage(context_text)) #! IT SHOULD BE TOOLMESSAGE
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
    history_str = "conversation history: " "\n".join(
        f"{msg.type.capitalize()}: {msg.content}" for msg in state["conversation_history"]
    )
    response = llm.invoke(prompt + history_str)
    state["conversation_history"].append(response)
    return {"answer": response.content}

# --- Build LangGraph ---
graph_builder = StateGraph(State).add_sequence(
    [retrieve_context, generate_answer]
)
graph_builder.add_edge(START, "retrieve_context")
graph_builder.add_edge("retrieve_context", "generate_answer")
graph = graph_builder.compile()

def ask_rag(question: str, conversation_history : list[BaseMessage] ) -> str:
    # Run pipeline
    # history_str = "\n".join(
    #     f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history
    # )
    initial_state = State(conversation_history = conversation_history, question= question)
    result = graph.invoke(initial_state)
    print(result)
    print(type(result))
    answer = result["answer"]
    # Track history for context
    # conversation_history.append({"role": "user", "content": question})
    # conversation_history.append({"role": "assistant", "content": answer})
    conversation_history.append(HumanMessage(content=question))
    conversation_history.append(AIMessage(content=answer))

    return answer

if __name__ == "__main__":
    question = "name of authors of the books"
    conversation_history = []
    print(ask_rag(question, conversation_history))