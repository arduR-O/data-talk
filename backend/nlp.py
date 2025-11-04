import os
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.graph import START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage

from dotenv import load_dotenv

load_dotenv()

# --- LLM setup ---
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

def setup_employee_table(db):
    db.run("""
        CREATE TABLE IF NOT EXISTS employee (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            department VARCHAR(50),
            salary NUMERIC,
            email VARCHAR(100),
            join_date DATE
        )
    """)
    db.run("TRUNCATE TABLE employee RESTART IDENTITY")
    employees = [
        ("Alice", "HR", 50000, "alice@example.com", "2021-01-15"),
        ("Bob", "Engineering", 75000, "bob@example.com", "2020-03-10"),
        ("Charlie", "Finance", 60000, "charlie@example.com", "2022-07-25"),
        ("Diana", "Marketing", 55000, "diana@example.com", "2019-11-05"),
        ("Ethan", "Engineering", 80000, "ethan@example.com", "2021-08-19"),
        ("Fiona", "Finance", 62000, "fiona@example.com", "2020-12-30"),
        ("George", "HR", 52000, "george@example.com", "2022-04-14"),
        ("Hannah", "Engineering", 78000, "hannah@example.com", "2019-09-21"),
        ("Ian", "Marketing", 54000, "ian@example.com", "2021-06-11"),
        ("Jane", "Finance", 61000, "jane@example.com", "2020-10-01"),
    ]
    for name, dept, salary, email, join_date in employees:
        db.run(f"""
            INSERT INTO employee (name, department, salary, email, join_date)
            VALUES ('{name}', '{dept}', {salary}, '{email}', '{join_date}')
        """)
    print("Employee table created and 10 records inserted.")

# --- LangGraph pipeline setup ---
class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str
    conversation_history: list[BaseMessage]

system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results.

Never query for all the columns from a specific table, only ask for the
few relevant columns given the question.

Only use the following tables:
{table_info}
"""

user_prompt = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]

def create_database_graph(db_url: str):
    """Create a database graph with the provided database URL"""
    if not db_url:
        raise ValueError("Database URL is required")
    
    # Create database connection
    db = SQLDatabase.from_uri(db_url)
    
    def write_query(state: State):
        prompt = query_prompt_template.invoke(
            {
                "dialect": db.dialect,
                "top_k": 10,
                "table_info": db.get_table_info(),
                "input": state["question"],
            }
        )
        structured_llm = llm.with_structured_output(QueryOutput)
        result = structured_llm.invoke(prompt)
        return {"query": result["query"]}

    def execute_query(state: State):
        execute_query_tool = QuerySQLDatabaseTool(db=db)
        return {"result": execute_query_tool.invoke(state["query"])}

    def generate_answer(state: State):
        prompt = (
            "You are a friendly SQL assistant. "
            "Answer the user's latest request clearly and naturally, "
            "using the conversation history and SQL result only to get the right answer. "
            "Do not repeat the SQL query, the database schema, or the full context—"
            "just respond conversationally, as if you're chatting.\n\n"
            f"Conversation so far:\n{state['conversation_history']}\n\n"
            f"Latest user request: {state['question']}\n"
            f"SQL Result: {state['result']}\n\n"
            "Give only the answer that was asked for, in a helpful tone."
        )
        response = llm.invoke(prompt)
        return {"answer": response.content}

    # Build graph
    graph_builder = StateGraph(State).add_sequence(
        [write_query, execute_query, generate_answer]
    )
    graph_builder.add_edge(START, "write_query")
    graph = graph_builder.compile()
    
    return graph

def ask_database(question: str, conversation_history: list[BaseMessage], db_url: str = None) -> str:
    """Ask a natural language question and get an answer from the database.
    
    Args:
        question: The user's question
        conversation_history: List of conversation messages
        db_url: Database connection URL. If not provided, falls back to DB_URL env variable.
    """
    # Use provided db_url or fall back to environment variable
    if not db_url:
        db_url = os.getenv("DB_URL")
    
    if not db_url:
        raise ValueError("Database URL is required. Please provide a db_url parameter or set DB_URL environment variable.")
    
    # Create graph with the database URL
    graph = create_database_graph(db_url)
    
    initial_state = State(conversation_history=conversation_history, question=question)
    result = graph.invoke(initial_state)
    answer = result["answer"]

    # Track history for context
    conversation_history.append(HumanMessage(question))
    conversation_history.append(AIMessage(answer))

    return answer

