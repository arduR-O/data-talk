import os
from functools import lru_cache
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Returns a cached, single instance of ChatGroq client."""
    return ChatGroq(
        model=os.getenv("LLM_MODEL", "qwen/qwen3-32b"),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )
