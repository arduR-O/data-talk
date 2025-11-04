# orchestrator.py
import getpass
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from rag import ask_rag
from nlp import ask_database
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
load_dotenv()

# --- Groq API key setup ---
if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# --- Pipeline decision ---
def decide_pipeline(question: str) -> str:
    """
    Simple LLM-based classifier to choose pipeline.
    Returns 'rag' or 'sql'.
    """
    prompt = f"""
    You are a smart AI assistant that decides whether a user question
    should be answered using a document retrieval system (RAG) 
    or a SQL database system (SQL).

    Question: "{question}"

    Answer with exactly one word: 'rag' or 'sql'.
    """
    response = llm.invoke(prompt)
    choice = response.content.strip().lower()
    if choice not in ["rag", "sql"]:
        return "rag"  # fallback
    return choice

# --- Conversational memory for orchestrator ---
# Store conversation history per user_id
orchestrator_histories = {}

def chat(question: str, user_id: str = None, db_url: str = None) -> str:
    """
    Main orchestrator function that decides which pipeline to use
    and returns a conversational answer.
    
    Args:
        question: The user's question
        user_id: Optional user ID for conversation history tracking
        db_url: Optional database URL for SQL queries. If not provided, 
                SQL pipeline will fall back to DB_URL env variable.
    """
    # Get or create conversation history for this user
    if user_id:
        if user_id not in orchestrator_histories:
            orchestrator_histories[user_id] = []
        conversation_history = orchestrator_histories[user_id]
    else:
        # Fallback to global history if no user_id provided
        if "global" not in orchestrator_histories:
            orchestrator_histories["global"] = []
        conversation_history = orchestrator_histories["global"]
    
    # Track user input
    conversation_history.append(HumanMessage(question))

    # Decide which pipeline
    pipeline = decide_pipeline(question)

    if pipeline == "sql":
        # Pass db_url to ask_database if provided
        answer = ask_database(question, conversation_history, db_url=db_url)
    else:
        # RAG pipeline (simplified, no config/memory)
        answer = ask_rag(question, conversation_history)

    # Track assistant response
    conversation_history.append(AIMessage(answer))

    return answer

# --- Chat loop ---
if __name__ == "__main__":
    print("Start chatting with your AI Data Scientist! (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        answer = chat(user_input)
        print(f"Assistant: {answer}\n")
