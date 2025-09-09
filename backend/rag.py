import getpass
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph, MessagesState
from typing_extensions import List, TypedDict
from langchain import hub
from load_docs import get_vector_store
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver 
from langgraph.prebuilt import create_react_agent
from pypdf import PdfReader

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")
  
llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

# prompt = hub.pull("rlm/rag-prompt")
prompt = "You are an assistant for question-answering tasks. Use retrieve tool to obtain neccessary context to answer the question, the tool can be called as many time as required, just make sure to not fall into an infinite loop. If you don't know the answer, just say that you don't know. keep the answer concise."

print(prompt)

vector_store = get_vector_store()

@tool
def retrieve(query: str): # !the docstring is not helping
    """Retrieve chunks of text most similar to input query. It just does a semantic search and does not have reasoning capabilities. It should be used just as a fetch tool, reasoning about what needs to be fetched should be done by the llm"""
    retrieved_docs = vector_store.similarity_search(query)
    return {"context": retrieved_docs}

@tool 
def contextDetails():
    """Provides details about documents available for context"""
    documents = []
    context_folder_path = "./context"
    files = os.listdir(context_folder_path)
    for file in files:
        if file.lower().endswith('.pdf'):
            reader = PdfReader(os.path.join(context_folder_path, file))
            data = dict(reader.metadata) if reader.metadata else {}
            data["document_name"] = file
            documents.append(data)
    return {"documents_in_context": documents}
      

memory = MemorySaver()
agent_executor = create_react_agent(llm, [retrieve, contextDetails], checkpointer=memory)
# graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "abc123"}}

# input_message = "Kindly return a list of all the chapters covered in the textbook"
input_message = "generate a 10 question quiz on the first chapter of the book and then find their answers"

for event in agent_executor.stream(
    {"messages": [{"role":"system", "content": prompt},{"role": "user", "content": input_message}]},
    stream_mode="values",
    config=config,
):
    event["messages"][-1].pretty_print()