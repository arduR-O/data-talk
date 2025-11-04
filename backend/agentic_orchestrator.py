"""
Agentic Orchestrator - ReAct pattern with dynamic tool calling
Allows LLM to reason, plan, and execute multiple tool calls sequentially
"""

import os
from langchain_groq import ChatGroq
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

llm = ChatGroq(
    model="qwen/qwen3-32b",
    # model = "moonshotai/kimi-k2-instruct-0905",
    temperature=0
)

# ============================================================================
# DEBUG LOGGER
# ============================================================================

class DebugLogger:
    """Centralized debug logging for the agent"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logs = []
    
    def _log(self, level: str, message: str, data: dict = None):
        """Internal logging method"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)
        
        if self.enabled:
            # Console output with colors (if terminal supports it)
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
        """Get all logged entries"""
        return self.logs
    
    def clear(self):
        """Clear all logs"""
        self.logs = []
    
    def summary(self) -> dict:
        """Get a summary of the execution"""
        tool_calls = [log for log in self.logs if log["level"] == "TOOL"]
        errors = [log for log in self.logs if log["level"] == "ERROR"]
        
        return {
            "total_logs": len(self.logs),
            "tool_calls_count": len(tool_calls),
            "tools_used": [log["data"]["arguments"] for log in tool_calls],
            "errors_count": len(errors),
            "execution_time": f"{self.logs[-1]['timestamp']} (end)" if self.logs else "N/A"
        }


# Global debug logger instance
debug_logger = DebugLogger(enabled=True)  # Set to False to disable debug output


# ============================================================================
# TOOLS DEFINITION
# ============================================================================

class SQLQueryInput(BaseModel):
    """Input for SQL query tool"""
    query_description: str = Field(
        description="Natural language description of what SQL operation to perform. "
                    "Can be a SELECT query, CREATE TABLE, INSERT, UPDATE, DELETE, etc. "
                    "Be specific about what you want to accomplish."
    )

class DocumentSearchInput(BaseModel):
    """Input for document search tool"""
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
    
    Example descriptions:
        - "Get count of employees by department"
        - "Create a new table called projects with columns id, name, and status"
        - "Who is Omansh and what are his skills?"
        - "Calculate average salary across all departments"
    """
    debug_logger.tool_call("query_database", {"query_description": query_description})
    
    db_url = context.get('db_url')
    conversation_history = context.get('conversation_history', [])
    
    if not db_url:
        debug_logger.error("Database not configured")
        return "❌ Database not configured. User needs to provide a database URL first."
    
    try:
        # Check if this is a DDL operation (table creation, alteration)
        is_ddl = any(keyword in query_description.lower() 
                     for keyword in ['create table', 'alter table', 'drop table', 'create index'])
        
        debug_logger.info("Executing database query", 
                         is_ddl=is_ddl, 
                         description=query_description)
        
        result = ask_database(query_description, conversation_history, db_url)
        
        debug_logger.result("Database query completed", {"result_preview": result[:200]})
        
        # Add acknowledgment for DDL operations
        if is_ddl:
            if 'error' not in result.lower() and 'fail' not in result.lower():
                return f"✅ Database schema modified successfully.\n\n{result}"
        
        return result
    except Exception as e:
        debug_logger.error("Database query failed", e)
        return f"❌ Database error: {str(e)}"


@tool(args_schema=DocumentSearchInput)
def search_documents(search_query: str, context: dict) -> str:
    """
    Search through the user's uploaded PDF documents to find specific information.
    Use this to find names, contact details, policies, skills, etc.
    This tool will search the documents and return a *concise answer*
    to your query.
    
    Args:
        search_query: What to search for in the documents
        context: Context dictionary containing user_id
    
    Returns:
        A concise answer extracted from the documents.
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
        
        # --- NEW RAG CHAIN to extract/summarize ---
        # Combine the retrieved document contents
        context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
        
        # Create a simple prompt for extraction
        extraction_prompt_template = """
        You are an assistant. Your only job is to extract specific information from the given context.
        The user is asking for: "{query}"
        
        Answer *only* with the specific information requested, based *only* on the context below.
        If the information is not in the context, say "Information not found."
        
        Context:
        {context}
        """
        
        extraction_prompt = ChatPromptTemplate.from_template(extraction_prompt_template)
        
        # Create a simple chain
        chain = extraction_prompt | llm | StrOutputParser()
        
        debug_logger.info("Extracting answer from RAG context...")
        
        # Invoke the chain
        answer = chain.invoke({
            "query": search_query,
            "context": context_text
        })
        
        debug_logger.result("RAG extraction complete", data={"answer_preview": answer[:200]})
        
        # Return the clean, extracted answer
        return f"📄 Information found in documents: {answer}"

    except Exception as e:
        debug_logger.error("Document search failed", e)
        return f"❌ Document search error: {str(e)}"
# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """State for the agent graph"""
    messages: list[BaseMessage]
    user_id: str
    db_url: Optional[str]
    tool_context: dict  # Context passed to tools
    final_answer: Optional[str]


# ============================================================================
# AGENT NODES
# ============================================================================

# ============================================================================
# AGENT NODES
# ============================================================================

def create_agent_node(tools: list):
    """
    Create the agent node - This version uses the ChatGroq model's
    native tool binding, which is robust and correct.
    """
    
    # Bind the tools to the LLM.
    # This automatically handles all the complex JSON schema formatting.
    # We use the 'llm' instance defined at the top of the file.
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: AgentState):
        """Agent reasoning node"""
        messages = state['messages']
        
        debug_logger.info("Agent reasoning phase", 
                          messages_count=len(messages),
                          last_message_type=type(messages[-1]).__name__)
        
        # Invoke the LLM with the message history.
        # The ChatGroq 'llm_with_tools' object correctly converts the
        # LangChain BaseMessage list (including Human, AI, and ToolMessages)
        # into the format the Groq API expects.
        try:
            response_message = llm_with_tools.invoke(messages)
        
        except Exception as e:
            debug_logger.error("Groq API call failed", e)
            raise
        
        # The response is already a LangChain AIMessage
        
        # Log the result
        if response_message.tool_calls:
            debug_logger.info(f"Agent decided to call {len(response_message.tool_calls)} tool(s)")
            for i, tc in enumerate(response_message.tool_calls, 1):
                debug_logger.info(f"  Tool {i}: {tc['name']}", 
                                  args_preview=str(tc['args'])[:100])
        else:
            debug_logger.info("Agent decided to provide final answer")

        if response_message.content:
            debug_logger.reasoning(response_message.content[:300])
        
        # Return the AIMessage to be added to the state
        return {"messages": [response_message]}

    return agent

def create_tool_node(tools: list):
    """Create tool execution node with context injection"""
    
    def tool_executor(state: AgentState):
        """Execute tools with injected context"""
        messages = state['messages']
        last_message = messages[-1]
        
        # Extract tool calls from the last message
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {"messages": []}
        
        debug_logger.info(f"Executing {len(last_message.tool_calls)} tool call(s)")
        
        # Prepare context for tools
        context = {
            'user_id': state['user_id'],
            'db_url': state.get('db_url'),
            'conversation_history': [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage))]
        }
        
        # Execute each tool call with context
        tool_messages = []
        for i, tool_call in enumerate(last_message.tool_calls, 1):
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            debug_logger.info(f"Tool call {i}/{len(last_message.tool_calls)}: {tool_name}")
            
            # Find the tool
            tool_func = next((t for t in tools if t.name == tool_name), None)
            if not tool_func:
                debug_logger.error(f"Tool '{tool_name}' not found")
                continue
            
            # We will call the underlying Python function (.func) directly.
            # This allows us to unpack the LLM-generated arguments (**tool_args)
            # and add our manually-injected 'context' argument as a keyword.

            # Execute tool
            try:
                # tool_func is the LangChain 'Tool' object.
                # tool_func.func is the raw Python function.
                result = tool_func.func(**tool_args, context=context)

                debug_logger.result(f"Tool '{tool_name}' completed", 
                            data={"result_length": len(str(result))})
            except Exception as e:
                debug_logger.error(f"Tool '{tool_name}' failed", e)
                result = f"❌ Tool execution error: {str(e)}"
            
            # Create tool message
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
    """Determine if we should continue or end"""
    messages = state['messages']
    last_message = messages[-1]
    
    # If there are tool calls, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise, we're done
    return "end"


def format_final_answer(state: AgentState):
    """Format the final answer"""
    messages = state['messages']
    last_message = messages[-1]
    
    # Extract content from last AI message
    if hasattr(last_message, 'content'):
        final_answer = last_message.content
    else:
        final_answer = str(last_message)
    
    return {"final_answer": final_answer}


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_agent_graph():
    """Create the agent graph with ReAct pattern"""
    
    # Define tools
    tools = [query_database, search_documents]
    
    # Create nodes
    agent_node = create_agent_node(tools)
    tool_node = create_tool_node(tools)
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("format_answer", format_final_answer)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": "format_answer"
        }
    )
    workflow.add_edge("tools", "agent")  # Loop back to agent after tools
    workflow.add_edge("format_answer", END)
    
    return workflow.compile()


# ============================================================================
# ORCHESTRATOR CLASS
# ============================================================================

class AgenticOrchestrator:
    """
    Agentic orchestrator using ReAct pattern.
    
    The LLM can:
    1. Reason about what tools to use
    2. Call multiple tools sequentially
    3. Use results from one tool to inform the next
    4. Handle complex multi-step queries
    """
    
    def __init__(self):
        self.graph = create_agent_graph()
        self.system_message = self._create_system_message()
    
    def _create_system_message(self) -> str:
        """Create the system message for the agent"""
        return """You are DataTalk AI, a technical data assistant.
Your job is to follow user requests precisely.

**AVAILABLE TOOLS:**
1. **query_database**: Use for any SQL operation (SELECT, CREATE, INSERT, etc.).
2. **search_documents**: Use to find information inside user-uploaded documents (RAG).

**DECISION PROCESS (MUST FOLLOW):**

1.  **Analyze the *entire* user request.**
2.  **Is the information needed in the documents?**
    * If YES (e.g., "Omansh's skills", "contact details", "policy info"), you **MUST** call `search_documents` FIRST.
3.  **Does the request involve the database?**
    * If YES (e.g., "create table", "insert data", "get count"), you **MUST** call `query_database`.
4.  **Is it a hybrid request? (e.g., "Find info in docs AND put it in the database")**
    * **Step 1:** Call `search_documents` to get the information.
    * **Step 2:** Use the information from Step 1 to call `query_database` (e.g., to `CREATE` and `INSERT`).
5.  **Do not stop until *all* parts of the user's request are complete.**
6.  **Do not invent new tasks.** Once all steps from the user's request are done, provide a final, simple confirmation.
"""

    def chat(
        self,
        question: str,
        user_id: str,
        conversation_history: Optional[List[BaseMessage]] = None,
        db_url: Optional[str] = None,
        debug: bool = True  # New parameter to control debug output
    ) -> dict:
        """
        Main chat interface with agentic reasoning.
        
        Args:
            question: User's question
            user_id: User identifier
            conversation_history: Previous conversation messages
            db_url: Database connection URL (optional)
            debug: Enable/disable debug logging (default: True)
        
        Returns:
            dict with answer and metadata
        """
        # Configure debug logger
        debug_logger.enabled = debug
        debug_logger.clear()  # Clear previous logs
        
        debug_logger.info("=" * 80)
        debug_logger.info("NEW CHAT REQUEST")
        debug_logger.info("=" * 80)
        debug_logger.info("User question", question=question, user_id=user_id)
        
        if conversation_history is None:
            conversation_history = []
        
        # Check available resources
        has_documents = check_user_has_documents(user_id)
        has_database = db_url is not None and db_url.strip() != ""
        
        debug_logger.info("Resources available", 
                         database=has_database, 
                         documents=has_documents)
        
        # Build resource context
        resource_context = "\n\n**CURRENT RESOURCES:**\n"
        if has_database:
            resource_context += "✅ Database connected\n"
        else:
            resource_context += "❌ Database not connected\n"
        
        if has_documents:
            resource_context += "✅ Documents uploaded\n"
        else:
            resource_context += "❌ No documents uploaded\n"
        
        # Prepare messages
        messages = [SystemMessage(content=self.system_message + resource_context)]
        
        # Add conversation history (last 6 messages)
        messages.extend(conversation_history[-6:])
        
        # Add current question
        messages.append(HumanMessage(content=question))
        
        # Prepare initial state
        initial_state = AgentState(
            messages=messages,
            user_id=user_id,
            db_url=db_url,
            tool_context={},
            final_answer=None
        )
        
        debug_logger.info("Starting agent graph execution")
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            answer = final_state.get('final_answer', "I apologize, but I couldn't generate a response.")
            
            # Determine which tools were used
            tools_used = set()
            for msg in final_state['messages']:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_used.add(tool_call['name'])
            
            # Map to routing types
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
            
            # Print execution summary
            if debug:
                print("\n" + "=" * 80)
                print("EXECUTION SUMMARY")
                print("=" * 80)
                summary = debug_logger.summary()
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("=" * 80 + "\n")
            
            return {
                'answer': answer,
                'routing': routing,
                'resources': {
                    'database': has_database,
                    'documents': has_documents
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
                    'documents': has_documents
                },
                'tools_used': [],
                'debug_logs': debug_logger.get_logs() if debug else []
            }


# ============================================================================
# SINGLETON AND CONVENIENCE FUNCTIONS
# ============================================================================

_orchestrator_instance = None

def get_orchestrator() -> AgenticOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgenticOrchestrator()
    return _orchestrator_instance


def chat(
    question: str, 
    conversation_history: List[BaseMessage], 
    db_url: str,
    user_id: str,
    debug: bool = False  # Add debug parameter
) -> str:
    """
    Backwards compatible interface.
    
    Args:
        question: User's question
        conversation_history: Previous messages
        db_url: Database URL
        user_id: User ID
        debug: Enable debug logging (default: False for backwards compatibility)
    
    Returns:
        Answer string
    """
    orchestrator = get_orchestrator()
    result = orchestrator.chat(question, user_id, conversation_history, db_url, debug=debug)
    return result['answer']


def chat_with_debug(
    question: str,
    user_id: str,
    conversation_history: Optional[List[BaseMessage]] = None,
    db_url: Optional[str] = None
) -> dict:
    """
    Convenience function for debugging.
    Returns full result including debug logs.
    
    Args:
        question: User's question
        user_id: User ID
        conversation_history: Previous messages
        db_url: Database URL
    
    Returns:
        dict with answer, routing, tools_used, and debug_logs
    """
    orchestrator = get_orchestrator()
    return orchestrator.chat(question, user_id, conversation_history, db_url, debug=True)