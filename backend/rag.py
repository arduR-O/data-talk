import getpass
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain import hub
from load_docs import get_vector_store


load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")
  
llm = ChatGroq(
    model="gemma2-9b-it"
)

prompt = hub.pull("rlm/rag-prompt")

vector_store = get_vector_store()

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    # print(retrieved_docs)
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