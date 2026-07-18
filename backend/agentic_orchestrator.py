"""
Agentic Orchestrator - ReAct pattern with dynamic tool calling
Allows LLM to reason, plan, and execute multiple tool calls sequentially
"""

import os
import sqlite3
import contextvars
from utils.llm_client import get_llm
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from typing import List, Optional, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import existing systems
from nlp import ask_database
from utils.retriever_helper import get_user_retriever, check_user_has_documents

load_dotenv()

# Use shared, cached LLM client
llm = get_llm()

# ============================================================================
# DEBUG LOGGER
# ============================================================================

class DebugLogger:
    """Centralized debug logging for tracking tool invocations and execution steps"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logs = []
    
    def _log(self, level: str, message: str, data: dict = None):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
        
        if self.enabled:
            color_codes = {
                "INFO": "\033[94m",      # Blue
                "TOOL": "\033[95m",      # Magenta
                "SQL": "\033[96m",       # Cyan
                "RESULT": "\033[92m",    # Green
                "ERROR": "\033[91m",     # Red
                "REASONING": "\033[93m", # Yellow
                "RESET": "\033[0m"
            }
            
            color = color_codes.get(level, "")
            reset = color_codes["RESET"]
            
            print(f"\n{color}[{timestamp}] {level}: {message}{reset}")
            
            if data:
                print(f"{color}{'─' * 80}{reset}")
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 500:
                        value = value[:500] + "... (truncated)"
                    print(f"{color}{key}: {value}{reset}")
                print(f"{color}{'─' * 80}{reset}")
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, kwargs)
    
    def tool_call(self, tool_name: str, args: dict):
        self._log("TOOL", f"Calling tool: {tool_name}", {"arguments": args})
    
    def sql_query(self, query: str):
        self._log("SQL", "Generated SQL Query", {"query": query})
    
    def result(self, message: str, data: dict = None):
        self._log("RESULT", message, data)
    
    def error(self, message: str, error: Exception = None):
        error_data = {"error": str(error)} if error else None
        self._log("ERROR", message, error_data)
    
    def reasoning(self, thought: str):
        self._log("REASONING", "Agent Reasoning", {"thought": thought})
    
    def get_logs(self) -> List[dict]:
        return self.logs
    
    def clear(self):
        self.logs = []
    
    def summary(self) -> dict:
        tool_calls = [log for log in self.logs if log["level"] == "TOOL"]
        errors = [log for log in self.logs if log["level"] == "ERROR"]
        
        return {
            "total_logs": len(self.logs),
            "tool_calls_count": len(tool_calls),
            "tools_used": [log["data"]["arguments"] for log in tool_calls],
            "errors_count": len(errors),
            "execution_time": f"{self.logs[-1]['timestamp']} (end)" if self.logs else "N/A"
        }

# Thread-safe request logger context var
_debug_logger_var = contextvars.ContextVar("debug_logger_var")
_stream_callback_var = contextvars.ContextVar("stream_callback_var", default=None)

class ThreadSafeDebugLogger:
    """Thread-safe proxy for request-scoped DebugLogger"""
    @property
    def current(self) -> DebugLogger:
        try:
            return _debug_logger_var.get()
        except LookupError:
            default_logger = DebugLogger(enabled=True)
            _debug_logger_var.set(default_logger)
            return default_logger

    def __getattr__(self, name):
        return getattr(self.current, name)

    def __setattr__(self, name, value):
        setattr(self.current, name, value)

# Thread-safe proxy debug logger instance
debug_logger = ThreadSafeDebugLogger()

# ============================================================================
# TOOLS DEFINITION
# ============================================================================

class SQLQueryInput(BaseModel):
    """Input parameters for database queries"""
    query_description: str = Field(
        description="Natural language description of what SQL operation to perform. "
                    "Can be a SELECT query, CREATE TABLE, INSERT, UPDATE, DELETE, etc. "
                    "Be specific about what you want to accomplish."
    )

class DocumentSearchInput(BaseModel):
    """Input parameters for PDF/Text/Markdown searches"""
    search_query: str = Field(
        description="Search query to find relevant information in user's uploaded documents. "
                    "Be specific about what information you're looking for."
    )


@tool(args_schema=SQLQueryInput)
def query_database(query_description: str, context: dict) -> str:
    """
    Query the user's database using natural language.
    
    This tool translates a user's *question* or *command* into SQL.
    **DO NOT write SQL syntax in your description.**
    Provide a clear, natural language description of the goal.
    
    Args:
        query_description: Natural language question or command.
        context: Context dictionary (injected automatically)
    """
    debug_logger.tool_call("query_database", {"query_description": query_description})
    
    db_url = context.get('db_url')
    conversation_history = context.get('conversation_history', [])
    
    # Fallback to local SQLite demo database if no database is connected
    if not db_url:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_url = f"sqlite:///{os.path.join(base_dir, 'context', 'datatalk_demo.db')}"
        debug_logger.info("Database URL not provided. Using fallback SQLite demo DB.")
    
    try:
        is_ddl = any(keyword in query_description.lower() 
                     for keyword in ['create table', 'alter table', 'drop table', 'create index'])
        
        debug_logger.info("Executing database query", 
                         is_ddl=is_ddl, 
                         description=query_description)
        
        result = ask_database(query_description, conversation_history, db_url)
        
        debug_logger.result("Database query completed", {"result_preview": result[:200]})
        
        if is_ddl and 'error' not in result.lower() and 'fail' not in result.lower():
            return f"✅ Database schema modified successfully.\n\n{result}"
        
        return result
    except Exception as e:
        debug_logger.error("Database query failed", e)
        return f"❌ Database error: {str(e)}"


@tool(args_schema=DocumentSearchInput)
def search_documents(search_query: str, context: dict) -> str:
    """
    Search through the user's uploaded PDF, TXT, or MD documents to find specific information.
    Use this to find names, contact details, policies, skills, etc.
    This tool will search the documents and return a *concise answer*
    to your query.
    
    Args:
        search_query: What to search for in the documents
        context: Context dictionary containing user_id
    """
    debug_logger.tool_call("search_documents", {"search_query": search_query})
    
    user_id = context.get('user_id')
    
    if not user_id:
        debug_logger.error("User ID not provided")
        return "❌ User ID not provided."
    
    if not check_user_has_documents(user_id):
        debug_logger.info("No documents found for user", user_id=user_id)
        return "❌ No documents uploaded. User needs to upload PDF documents first."
    
    try:
        debug_logger.info("Searching documents", query=search_query)
        
        retriever = get_user_retriever(user_id, k=4)
        docs = retriever.invoke(search_query)
        
        if not docs:
            debug_logger.result("No relevant documents found")
            return "❌ No relevant information found in uploaded documents."
        
        debug_logger.result("Documents retrieved", 
                            data={
                                "count": len(docs),
                                "sources": [doc.metadata.get('filename', 'Unknown') for doc in docs]
                            })
        
        context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
        
        extraction_prompt_template = """
        You are an assistant. Your only job is to extract specific information from the given context.
        The user is asking for: "{query}"
        
        Answer *only* with the specific information requested, based *only* on the context below.
        If the information is not in the context, say "Information not found."
        
        Context:
        {context}
        """
        
        extraction_prompt = ChatPromptTemplate.from_template(extraction_prompt_template)
        chain = extraction_prompt | llm | StrOutputParser()
        
        debug_logger.info("Extracting answer from RAG context...")
        answer = chain.invoke({
            "query": search_query,
            "context": context_text
        })
        
        debug_logger.result("RAG extraction complete", data={"answer_preview": answer[:200]})
        return f"📄 Information found in documents: {answer}"

    except Exception as e:
        debug_logger.error("Document search failed", e)
        return f"❌ Document search error: {str(e)}"

# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    messages: list[BaseMessage]
    user_id: str
    db_url: Optional[str]
    tool_context: dict
    final_answer: Optional[str]

# ============================================================================
# AGENT NODES
# ============================================================================

def create_agent_node(tools: list):
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: AgentState):
        messages = state['messages']
        
        debug_logger.info("Agent reasoning phase", 
                          messages_count=len(messages),
                          last_message_type=type(messages[-1]).__name__)
        
        try:
            response_message = llm_with_tools.invoke(messages)
            
            # Stream final tokens if callback is registered and there are no tool calls
            if not response_message.tool_calls:
                callback = _stream_callback_var.get()
                if callback:
                    content_chunks = []
                    try:
                        for chunk in llm.stream(messages):
                            if chunk.content:
                                content_chunks.append(chunk.content)
                                callback(chunk.content)
                        response_message.content = "".join(content_chunks)
                    except Exception as stream_err:
                        debug_logger.error("Streaming failed, falling back to invoke", stream_err)
        except Exception as e:
            debug_logger.error("Groq API call failed", e)
            raise
        
        if response_message.tool_calls:
            debug_logger.info(f"Agent decided to call {len(response_message.tool_calls)} tool(s)")
            for i, tc in enumerate(response_message.tool_calls, 1):
                debug_logger.info(f"  Tool {i}: {tc['name']}", 
                                  args_preview=str(tc['args'])[:100])
        else:
            debug_logger.info("Agent decided to provide final answer")

        if response_message.content:
            debug_logger.reasoning(response_message.content[:300])
        
        return {"messages": [response_message]}

    return agent

def create_tool_node(tools: list):
    def tool_executor(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {"messages": []}
        
        debug_logger.info(f"Executing {len(last_message.tool_calls)} tool call(s)")
        
        context = {
            'user_id': state['user_id'],
            'db_url': state.get('db_url'),
            'conversation_history': [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage))]
        }
        
        tool_messages = []
        for i, tool_call in enumerate(last_message.tool_calls, 1):
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            debug_logger.info(f"Tool call {i}/{len(last_message.tool_calls)}: {tool_name}")
            
            tool_func = next((t for t in tools if t.name == tool_name), None)
            if not tool_func:
                debug_logger.error(f"Tool '{tool_name}' not found")
                continue
            
            try:
                # Direct invocation of func allowing manual context dictionary injection
                result = tool_func.func(**tool_args, context=context)
                debug_logger.result(f"Tool '{tool_name}' completed", 
                            data={"result_length": len(str(result))})
            except Exception as e:
                debug_logger.error(f"Tool '{tool_name}' failed", e)
                result = f"❌ Tool execution error: {str(e)}"
            
            from langchain_core.messages import ToolMessage
            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id']
                )
            )
        
        return {"messages": tool_messages}
    
    return tool_executor


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    messages = state['messages']
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    return "end"


def format_final_answer(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    
    if hasattr(last_message, 'content'):
        final_answer = last_message.content
    else:
        final_answer = str(last_message)
    
    return {"final_answer": final_answer}

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_agent_graph():
    tools = [query_database, search_documents]
    
    agent_node = create_agent_node(tools)
    tool_node = create_tool_node(tools)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("format_answer", format_final_answer)
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": "format_answer"
        }
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("format_answer", END)
    
    return workflow.compile()

# ============================================================================
# ORCHESTRATOR CLASS
# ============================================================================

class AgenticOrchestrator:
    def __init__(self):
        self.graph = create_agent_graph()
        self.system_message = self._create_system_message()
    
    def _create_system_message(self) -> str:
        # Enforcing structured Plan-then-Execute and Self-Correction logic
        return """You are DataTalk AI, a technical data assistant.
Your job is to follow user requests precisely by formulating search/query plans and executing them.

**CRITICAL PROTOCOL (PLAN-THEN-EXECUTE):**
1.  **Analyze the *entire* user request.**
2.  **Formulate a step-by-step query plan.** Decide what tools to call and in what order.
3.  **Execute the plan using tools.**
4.  **Self-Correction**: If a tool (like `query_database`) returns a database error (e.g., column not found, syntax error), DO NOT give up. Analyze the error message, review the schema in your mind, write a corrected query description, and call the tool again. You can try up to 3 times to get a working query.

**AVAILABLE TOOLS:**
1.  **query_database**: Use for any SQL operation (SELECT, CREATE, INSERT, etc.).
2.  **search_documents**: Use to find information inside user-uploaded documents (RAG).

**ROUTING DECISION:**
*   If information is in uploaded documents (e.g., policy documents, text notes), call `search_documents`.
*   If information is in the database (e.g., employee tables, projects, budget details), call `query_database`.
*   If it is a hybrid request (e.g., "Find the employee list in documents and get their salaries from the database"):
    *   **Step 1:** Call `search_documents` to get the list.
    *   **Step 2:** Call `query_database` with the results of Step 1 to fetch the salaries.
*   Do not stop until all parts of the user request are complete. Provide a final summary of what you did.

**DATA VISUALIZATION RULE:**
If the user asks for a chart or graph, or if the database query returns numerical/tabular data that would benefit from visual representation (e.g. comparing values, trend lines, proportion breakdowns), you MUST append a chart JSON block at the very end of your response inside a code block tagged with 'chart'.
Format the block exactly like this:
```chart
{
  "type": "bar" | "line" | "pie",
  "title": "Chart Title",
  "data": [
    {"name": "category or label", "value": 123.45}
  ]
}
```
Only use "name" and "value" keys in the data objects. Do not write any other keys in "data" items.
"""

    def chat(
        self,
        question: str,
        user_id: str,
        conversation_history: Optional[List[BaseMessage]] = None,
        db_url: Optional[str] = None,
        debug: bool = True
    ) -> dict:
        # Initialize thread-safe debug logger for this request
        request_logger = DebugLogger()
        _debug_logger_var.set(request_logger)
        debug_logger.enabled = debug
        debug_logger.clear()
        
        debug_logger.info("=" * 80)
        debug_logger.info("NEW CHAT REQUEST")
        debug_logger.info("=" * 80)
        debug_logger.info("User question", question=question, user_id=user_id)
        
        if conversation_history is None:
            conversation_history = []
            
        # Fallback to local SQLite demo database if no db_url is supplied
        if not db_url:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_url = f"sqlite:///{os.path.join(base_dir, 'context', 'datatalk_demo.db')}"
            debug_logger.info("Assigned default demo database connection URL")
        
        has_documents = check_user_has_documents(user_id)
        has_database = True
        
        debug_logger.info("Resources available", 
                          database=has_database, 
                          documents=has_documents)
        
        resource_context = "\n\n**CURRENT RESOURCES:**\n"
        resource_context += "✅ Database connected (Demo database or Custom connection)\n"
        
        if has_documents:
            resource_context += "✅ Documents uploaded\n"
        else:
            resource_context += "❌ No documents uploaded\n"
        
        messages = [SystemMessage(content=self.system_message + resource_context)]
        messages.extend(conversation_history[-6:])
        messages.append(HumanMessage(content=question))
        
        initial_state = AgentState(
            messages=messages,
            user_id=user_id,
            db_url=db_url,
            tool_context={},
            final_answer=None
        )
        
        debug_logger.info("Starting agent graph execution")
        
        try:
            final_state = self.graph.invoke(initial_state, config={"recursion_limit": 25})
            answer = final_state.get('final_answer', "I apologize, but I couldn't generate a response.")
            
            tools_used = set()
            for msg in final_state['messages']:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_used.add(tool_call['name'])
            
            routing = 'general'
            if 'query_database' in tools_used and 'search_documents' in tools_used:
                routing = 'hybrid'
            elif 'query_database' in tools_used:
                routing = 'sql'
            elif 'search_documents' in tools_used:
                routing = 'rag'
            
            debug_logger.info("Agent execution completed", 
                             routing=routing,
                             tools_used=list(tools_used))
            
            if debug:
                print("\n" + "=" * 80)
                print("EXECUTION SUMMARY")
                print("=" * 80)
                summary = debug_logger.summary()
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("=" * 80 + "\n")
            
            # Identify if we are using the seeded datatalk_demo.db database file
            is_demo = 'datatalk_demo.db' in db_url
            
            return {
                'answer': answer,
                'routing': routing,
                'resources': {
                    'database': has_database,
                    'documents': has_documents,
                    'is_demo_db': is_demo
                },
                'tools_used': list(tools_used),
                'debug_logs': debug_logger.get_logs() if debug else []
            }
            
        except Exception as e:
            debug_logger.error("Agent execution failed", e)
            
            if debug:
                print("\n" + "=" * 80)
                print("EXECUTION FAILED")
                print("=" * 80)
                print(f"Error: {str(e)}")
                print("=" * 80 + "\n")
            
            return {
                'answer': f"I encountered an error: {str(e)}",
                'routing': 'error',
                'resources': {
                    'database': has_database,
                    'documents': has_documents,
                    'is_demo_db': 'datatalk_demo.db' in db_url if db_url else False
                },
                'tools_used': [],
                'debug_logs': debug_logger.get_logs() if debug else []
            }


_orchestrator_instance = None

def get_orchestrator() -> AgenticOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgenticOrchestrator()
    return _orchestrator_instance


def chat(
    question: str, 
    conversation_history: List[BaseMessage], 
    db_url: str,
    user_id: str,
    debug: bool = False
) -> str:
    orchestrator = get_orchestrator()
    result = orchestrator.chat(question, user_id, conversation_history, db_url, debug=debug)
    return result['answer']


def chat_with_debug(
    question: str,
    user_id: str,
    conversation_history: Optional[List[BaseMessage]] = None,
    db_url: Optional[str] = None
) -> dict:
    orchestrator = get_orchestrator()
    return orchestrator.chat(question, user_id, conversation_history, db_url, debug=True)