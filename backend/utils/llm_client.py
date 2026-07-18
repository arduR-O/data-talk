import os
from functools import lru_cache
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

@lru_cache(maxsize=1)
def get_llm():
    """Returns a cached, single instance of ChatGroq client or None for Demo Mode."""
    api_key = os.getenv("GROQ_API_KEY")
    
    # If missing or placeholder, return None (Demo Mode will intercept)
    if not api_key or api_key == "your_groq_api_key_here":
        print("⚠️ GROQ_API_KEY not found. Running in Demo Mode.")
        return None
        
    try:
        return ChatGroq(
            model=os.getenv("LLM_MODEL", "qwen/qwen3-32b"),
            temperature=0,
            api_key=api_key,
        )
    except Exception as e:
        print(f"⚠️ Failed to initialize LLM: {e}. Running in Demo Mode.")
        return None
