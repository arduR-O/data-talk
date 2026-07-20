import os
import sqlite3
import re
from functools import lru_cache
from langchain_community.utilities import SQLDatabase
from utils.llm_client import get_llm
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.graph import START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# --- LLM setup ---
llm = get_llm()

def ensure_demo_db_seeded(db_url: str):
    """Seed the database with sample data if it's a new or empty SQLite database"""
    # Checking for specific substring to only target our default demo database
    if 'datatalk_demo.db' not in db_url:
        return
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    context_dir = os.path.join(base_dir, 'context')
    os.makedirs(context_dir, exist_ok=True)
    db_path = os.path.join(context_dir, 'datatalk_demo.db')
    
    # We check file size as a simple heuristic to see if tables were already seeded
    if os.path.exists(db_path) and os.path.getsize(db_path) > 10240:
        return
        
    print(f"Seeding local SQLite demo database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            budget REAL,
            manager_id INTEGER
        )
    """)
    
    # 2. Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            department_id INTEGER,
            salary REAL,
            email TEXT UNIQUE,
            join_date TEXT,
            FOREIGN KEY(department_id) REFERENCES department(id)
        )
    """)
    
    # 3. Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            budget REAL,
            start_date TEXT
        )
    """)
    
    # 4. Employee projects assignment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_project (
            employee_id INTEGER,
            project_id INTEGER,
            role TEXT,
            PRIMARY KEY(employee_id, project_id),
            FOREIGN KEY(employee_id) REFERENCES employee(id),
            FOREIGN KEY(project_id) REFERENCES project(id)
        )
    """)
    
    # Seed Departments
    departments = [
        ("Engineering", 500000.0),
        ("Product", 250000.0),
        ("Marketing", 150000.0),
        ("Sales", 300000.0),
        ("HR", 100000.0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO department (name, budget) VALUES (?, ?)", departments)
    
    # Seed Employees
    employees = [
        ("Alice Smith", 1, 95000.0, "alice@datatalk.ai", "2021-03-15"),
        ("Bob Jones", 1, 105000.0, "bob@datatalk.ai", "2020-06-10"),
        ("Charlie Brown", 2, 85000.0, "charlie@datatalk.ai", "2022-01-22"),
        ("Diana Prince", 3, 75000.0, "diana@datatalk.ai", "2021-11-05"),
        ("Ethan Hunt", 1, 110000.0, "ethan@datatalk.ai", "2020-08-19"),
        ("Fiona Gallagher", 4, 90000.0, "fiona@datatalk.ai", "2019-12-30"),
        ("George Costanza", 5, 60000.0, "george@datatalk.ai", "2022-04-14"),
        ("Hannah Baker", 1, 98000.0, "hannah@datatalk.ai", "2021-09-21"),
        ("Ian Malcolm", 3, 78000.0, "ian@datatalk.ai", "2021-05-11"),
        ("Jane Doe", 4, 115000.0, "jane@datatalk.ai", "2018-10-01")
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO employee (name, department_id, salary, email, join_date) 
        VALUES (?, ?, ?, ?, ?)
    """, employees)
    
    # Set Managers
    cursor.execute("UPDATE department SET manager_id = 2 WHERE name = 'Engineering'")
    cursor.execute("UPDATE department SET manager_id = 3 WHERE name = 'Product'")
    cursor.execute("UPDATE department SET manager_id = 4 WHERE name = 'Marketing'")
    cursor.execute("UPDATE department SET manager_id = 10 WHERE name = 'Sales'")
    cursor.execute("UPDATE department SET manager_id = 7 WHERE name = 'HR'")
    
    # Seed Projects
    projects = [
        ("Project Apollo", 150000.0, "2024-01-10"),
        ("Project Genesis", 80000.0, "2024-02-15"),
        ("Project Titan", 200000.0, "2024-03-01")
    ]
    cursor.executemany("INSERT OR IGNORE INTO project (name, budget, start_date) VALUES (?, ?, ?)", projects)
    
    # Seed Assignments
    assignments = [
        (1, 1, "Lead Developer"),
        (2, 1, "Architect"),
        (3, 2, "Product Manager"),
        (4, 3, "Marketing Coordinator"),
        (5, 3, "Security Engineer"),
        (8, 2, "Frontend Developer"),
        (9, 3, "Analyst")
    ]
    cursor.executemany("INSERT OR IGNORE INTO employee_project (employee_id, project_id, role) VALUES (?, ?, ?)", assignments)
    
    conn.commit()
    conn.close()
    print("SQLite Demo database successfully seeded!")

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

user_prompt = "Recent conversation (use this to resolve follow-up references like \"him\", \"that department\", \"last month\"):\n{history}\n\nQuestion: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)

def _format_history(history: list[BaseMessage], max_turns: int = 3) -> str:
    """Format the last few turns as plain text for the SQL-writing prompt.
    Previously this was accepted as a parameter but never actually read anywhere --
    conversation_history was threaded through State and appended to after every
    call, but write_query() below only ever used state['question'] in isolation,
    so follow-up questions referencing prior turns had nothing to resolve against."""
    if not history:
        return "(no prior conversation)"

    lines = []
    for msg in history[-(max_turns * 2):]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]

DANGEROUS_SQL_PATTERNS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bALTER\b',
    r'\bINSERT\b', r'\bUPDATE\b', r'\bCREATE\b', r'\bGRANT\b',
    r'\bREVOKE\b', r'\bEXEC\b', r'\bATTACH\b',
]

def validate_sql_safety(sql: str) -> bool:
    """Returns True if the SQL query is safe and read-only."""
    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return False
    return True

@lru_cache(maxsize=16)
def create_database_graph(db_url: str):
    if not db_url:
        raise ValueError("Database URL is required")
        
    ensure_demo_db_seeded(db_url)
    
    # SQLite does not support isolation level AUTOCOMMIT in SQLAlchemy
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url)
    else:
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        
    db = SQLDatabase(engine=engine)
    
    def write_query(state: State):
        prompt = query_prompt_template.invoke(
            {
                "dialect": db.dialect,
                "top_k": 10,
                "table_info": db.get_table_info(),
                "input": state["question"],
                "history": _format_history(state.get("conversation_history", [])),
            }
        )
        try:
            structured_llm = llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)
            query = result["query"]
        except Exception as struct_err:
            # Fall back to raw text invocation and SQL regex parsing if structured schema fails
            text_prompt = (
                f"{prompt.to_string()}\n\n"
                "Write a syntactically correct SQL query. Output ONLY the raw SQL query "
                "enclosed in a ```sql ... ``` code block. Do NOT write any other text or explanation."
            )
            try:
                raw_res = llm.invoke(text_prompt).content
                sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_res, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    query = sql_match.group(1).strip()
                else:
                    # Clean up lines and extract raw SELECT text
                    clean_lines = [l.strip() for l in raw_res.split("\n") if l.strip()]
                    query_lines = [l for l in clean_lines if not l.startswith("-") and not l.startswith("/")]
                    query = " ".join(query_lines).replace("```", "").strip()
            except Exception as fallback_err:
                raise ValueError(f"SQL generation failed: {struct_err} -> Fallback error: {fallback_err}")
        return {"query": query}

    def execute_query(state: State):
        execute_query_tool = QuerySQLDatabaseTool(db=db)
        query = state["query"]
        
        # SQL safety check
        if not validate_sql_safety(query):
            return {"result": "Error: Execution blocked. SQL query contains potentially unsafe operations."}
            
        # Safe detection of DDL/DML vs standard SELECT queries
        is_select = query.strip().lower().startswith("select")
        
        try:
            # We use include_columns=True to provide explicit column names so the LLM knows which field represents which value.
            if is_select:
                result = db.run(query, include_columns=True)
            else:
                result = db.run(query)
        except Exception as e:
            return {"result": f"Error executing query: {str(e)}"}

        if not is_select:
            return {"result": "Operation completed successfully."}
        
        return {"result": str(result)}

    def generate_answer(state: State):
        prompt = (
            "You are a SQL assistant. Your job is to report the results of a SQL operation. "
            "You must STICK to the facts provided.\n\n"
            "**CRITICAL RULES:**\n"
            "1. If the 'SQL Result' is a confirmation (e.g., 'Operation completed successfully', 'The table was updated'), "
            "   you MUST NOT invent any data or new tasks. Just confirm the action was successful. "
            "   (e.g., 'The table was created.' or 'The data was inserted.')\n"
            "2. If the 'SQL Result' contains data (from a SELECT), use ONLY that data to answer.\n"
            "3. If the 'SQL Result' is an error, state the error.\n"
            "4. DO NOT invent phone numbers, emails, skills, or any other details not "
            "   explicitly present in the 'SQL Result'.\n"
            "5. DO NOT suggest new, unrelated tasks (like inserting 'John Doe').\n\n"
            f"**Latest User Request:** {state['question']}\n"
            f"**SQL Result:** {state['result']}\n\n"
            "Based *only* on the SQL Result, what is the correct, direct response?"
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
    # Set default connection pointing to our auto-seeded demo SQLite database
    if not db_url:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_url = f"sqlite:///{os.path.join(base_dir, 'context', 'datatalk_demo.db')}"
    
    graph = create_database_graph(db_url)
    
    initial_state = State(conversation_history=conversation_history, question=question)
    result = graph.invoke(initial_state)
    answer = result["answer"]

    conversation_history.append(HumanMessage(question))
    conversation_history.append(AIMessage(answer))

    return answer