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
orchestrator_history = []

def chat(question: str) -> str:
    """
    Main orchestrator function that decides which pipeline to use
    and returns a conversational answer.
    """
    # Track user input
    orchestrator_history.append(HumanMessage(question))

    # Decide which pipeline
    pipeline = decide_pipeline(question)

    if pipeline == "sql":
        answer = ask_database(question, orchestrator_history)
    else:
        # RAG pipeline (simplified, no config/memory)
        answer = ask_rag(question, orchestrator_history)

    # Track assistant response
    orchestrator_history.append(AIMessage(answer))

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
