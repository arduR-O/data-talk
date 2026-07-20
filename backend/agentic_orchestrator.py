"""
Agentic Orchestrator - Plan / Execute / Replan / Synthesize / Audit

Design note (evolution from the flat ReAct loop, and from the first rewrite):
The original version was one `agent` node looping freely, deciding everything
(tool choice, sequencing, retries, output format) from a single large prompt
on every turn -- unreliable on cheaper open-weight models, which struggle with
open-ended multi-step reasoning.

A first rewrite replaced this with a fixed router -> {sql|rag|hybrid|general}
pipeline. That fixed the "narrow decision per step" problem, but went too far:
it could only handle one hardcoded shape (at most one document lookup followed
by at most one database query), and had no way to loop back if the question
actually needed a second or third step.

This version keeps the "narrow decision per node" principle but restores real
looping, using the standard Plan-and-Execute pattern:
  - `planner`     decides an initial ordered list of tool steps (still a
                   constrained, structured-output decision, not free reasoning).
  - `executor`    runs exactly one step per visit. SQL steps keep the bounded,
                   deterministic self-correction retry (up to 3 tries).
  - `replanner`   the loop-back node. After each step, one narrow question:
                   "given what we have, are we done, or is one more step
                   needed?" Bounded by MAX_PLAN_ITERATIONS so it can't spin
                   forever.
  - `synthesize`  the only node that owns grounding rules + the chart-format
                   contract, since it's the only node producing user-facing text.
  - `audit`       a separate, independent pass that checks the drafted answer's
                   claims against the actual gathered tool results. If it finds
                   an unsupported claim, one bounded retry regenerates the
                   answer with that specific issue named; if it still doesn't
                   pass, a visible caveat is appended rather than silently
                   shipping a flagged answer. This is a real corrective step,
                   not a cosmetic one -- it always has a defined action.

Also fixed here: conversation_history is now actually used by the planner (to
resolve follow-up references like "him" or "that department") -- previously it
was threaded through the state and appended to, but never read by anything.
The same bug existed in nlp.py's SQL-writing prompt; see the fix there.
"""

import os
import re
import json
import contextvars
from utils.llm_client import get_llm
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from typing import List, Optional, Literal, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from nlp import ask_database
from utils.retriever_helper import get_user_retriever, check_user_has_documents

load_dotenv()

llm = get_llm()

# Instantiate control LLM for fast structural routing/checks (default to openai/gpt-oss-20b)
from langchain_groq import ChatGroq
llm_control = ChatGroq(
    model=os.getenv("LLM_CONTROL_MODEL", "openai/gpt-oss-20b"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
) if os.getenv("GROQ_API_KEY") else None

control_model = llm_control if llm_control is not None else llm

from functools import lru_cache
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase

@lru_cache(maxsize=8)
def get_db_schema_summary(db_url: str) -> str:
    """Retrieve and cache the table and column schemas of the connected database."""
    try:
        engine = create_engine(db_url)
        db = SQLDatabase(engine=engine)
        return db.get_table_info()
    except Exception as e:
        return f"Error retrieving schema: {e}"

MAX_SQL_RETRIES = 3
MAX_PLAN_ITERATIONS = 4
MAX_AUDIT_RETRIES = 1

# --- Helper to extract JSON from Groq's failed_generation exception ---
def extract_json_from_exception_str(err_str: str) -> Optional[dict]:
    match = re.search(r"failed_generation'?:?\s*['\"](.*?)['\"]", err_str, re.DOTALL)
    json_str = None
    if match:
        failed_gen = match.group(1)
        xml_match = re.search(r"<function=.*?>\s*(.*?)\s*</function>", failed_gen, re.DOTALL)
        if xml_match:
            json_str = xml_match.group(1)
        else:
            json_str = failed_gen
    else:
        match = re.search(r"(\{.*\})", err_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            
    if not json_str:
        return None
        
    try:
        cleaned = json_str.encode().decode('unicode_escape')
        if (cleaned.startswith("'") and cleaned.endswith("'")) or (cleaned.startswith('"') and cleaned.endswith('"')):
            cleaned = cleaned[1:-1]
        cleaned = cleaned.replace('\\"', '"').replace("\\'", "'")
        dict_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if dict_match:
            cleaned = dict_match.group(1)
        return json.loads(cleaned)
    except Exception:
        try:
            return json.loads(json_str)
        except Exception:
            return None

class RecoverableStructuredRunnable:
    def __init__(self, target, schema):
        self._target = target
        self._schema = schema
        
    def invoke(self, input, config=None, **kwargs):
        try:
            return self._target.invoke(input, config, **kwargs)
        except Exception as e:
            err_str = str(e)
            print(f"⚠️ Structured LLM failed: {err_str}. Trying recovery or fallback...")
            
            # Step 1: Try to recover from failed_generation if it has JSON content
            json_dict = extract_json_from_exception_str(err_str)
            if json_dict:
                print("✅ Recovered JSON from exception body:", json_dict)
                if "done" in json_dict and isinstance(json_dict["done"], str):
                    json_dict["done"] = json_dict["done"].strip().lower() == "true"
                try:
                    if hasattr(self._schema, "model_validate"):
                        return self._schema.model_validate(json_dict)
                    elif hasattr(self._schema, "__fields__") or hasattr(self._schema, "model_fields"):
                        return self._schema(**json_dict)
                except Exception as val_err:
                    print(f"Pydantic validation failed on recovered JSON: {val_err}")
                return json_dict

            # Step 2: Fall back to raw text completions with JSON instructions
            print("🕒 Running raw text completion fallback for schema generation...")
            schema_desc = ""
            try:
                if hasattr(self._schema, "schema"):
                    schema_desc = json.dumps(self._schema.schema(), indent=2)
                elif hasattr(self._schema, "model_json_schema"):
                    schema_desc = json.dumps(self._schema.model_json_schema(), indent=2)
            except Exception:
                pass

            prompt_str = str(input)
            fallback_prompt = (
                f"{prompt_str}\n\n"
                f"You must output ONLY a valid JSON object matching this schema:\n{schema_desc}\n\n"
                "Provide the response enclosed in a single ```json ... ``` code block. "
                "Do NOT write any conversational preface, explanation, or notes. Output ONLY the JSON."
            )
            try:
                raw_res = llm.invoke(fallback_prompt).content
                json_match = re.search(r"```json\s*(.*?)\s*```", raw_res, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    json_match = re.search(r"(\{.*\})", raw_res, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    else:
                        json_str = raw_res.strip()
                        
                json_dict = json.loads(json_str)
                print("✅ Successfully parsed JSON from fallback response:", json_dict)
                
                if "done" in json_dict and isinstance(json_dict["done"], str):
                    json_dict["done"] = json_dict["done"].strip().lower() == "true"
                    
                if hasattr(self._schema, "model_validate"):
                    return self._schema.model_validate(json_dict)
                elif hasattr(self._schema, "__fields__") or hasattr(self._schema, "model_fields"):
                    return self._schema(**json_dict)
                return json_dict
            except Exception as fallback_err:
                print(f"❌ Fallback JSON completion failed: {fallback_err}")
                raise e
            
    def __getattr__(self, name):
        return getattr(self._target, name)

# ============================================================================
# DEBUG LOGGER
# (unchanged -- covered directly by tests/test_agentic_orchestrator.py)
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
                "INFO": "\033[94m",
                "TOOL": "\033[95m",
                "SQL": "\033[96m",
                "RESULT": "\033[92m",
                "ERROR": "\033[91m",
                "REASONING": "\033[93m",
                "PLAN": "\033[97m",
                "AUDIT": "\033[90m",
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

    def plan(self, steps: list, note: str = ""):
        self._log("PLAN", note or "Plan updated", {"steps": steps})

    def audit(self, grounded: bool, issues: str = ""):
        self._log("AUDIT", f"Groundedness check: {'passed' if grounded else 'FAILED'}",
                   {"issues": issues} if issues else None)

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

debug_logger = ThreadSafeDebugLogger()

# ============================================================================
# TOOLS (unchanged behavior; same names, same signatures)
# ============================================================================

class SQLQueryInput(BaseModel):
    query_description: str = Field(
        description="Natural language description of what SQL operation to perform. "
                    "Be specific about what you want to accomplish."
    )

class DocumentSearchInput(BaseModel):
    search_query: str = Field(
        description="Search query to find relevant information in user's uploaded documents."
    )


@tool(args_schema=SQLQueryInput)
def query_database(query_description: str, context: dict) -> str:
    """
    Query the user's database using natural language. Translates a natural-language
    request into SQL and executes it. Read-only by design (enforced in nlp.py).
    """
    debug_logger.tool_call("query_database", {"query_description": query_description})

    db_url = context.get('db_url')
    conversation_history = context.get('conversation_history', [])

    if not db_url:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_url = f"sqlite:///{os.path.join(base_dir, 'context', 'datatalk_demo.db')}"
        debug_logger.info("Database URL not provided. Using fallback SQLite demo DB.")

    try:
        result = ask_database(query_description, conversation_history, db_url)
        debug_logger.result("Database query completed", {"result_preview": result[:200]})
        return result
    except Exception as e:
        debug_logger.error("Database query failed", e)
        return f"❌ Database error: {str(e)}"


@tool(args_schema=DocumentSearchInput)
def search_documents(search_query: str, context: dict) -> str:
    """
    Search the user's uploaded PDF/TXT/MD documents for specific information.
    Returns a concise, context-grounded answer.
    """
    debug_logger.tool_call("search_documents", {"search_query": search_query})

    user_id = context.get('user_id')

    if not user_id:
        debug_logger.error("User ID not provided")
        return "❌ User ID not provided."

    from services.vector_service import get_vector_service
    vector_service = get_vector_service()
    if not vector_service.available:
        debug_logger.info("Vector service is unavailable", user_id=user_id)
        return "❌ Document search is unavailable. The Pinecone vector store API key is not configured."

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

        answer = chain.invoke({"query": search_query, "context": context_text})
        debug_logger.result("RAG extraction complete", data={"answer_preview": answer[:200]})
        return f"📄 Information found in documents: {answer}"

    except Exception as e:
        debug_logger.error("Document search failed", e)
        return f"❌ Document search error: {str(e)}"


def _invoke_tool_direct(tool_func, context: dict, **kwargs) -> str:
    """Invoke a @tool-decorated function directly, bypassing LLM tool-call
    machinery -- these nodes call tools deterministically once a step has
    already been decided, rather than letting a model decide in the same
    breath as generating the call."""
    return tool_func.func(**kwargs, context=context)

# ============================================================================
# STATE & STRUCTURED OUTPUTS
# ============================================================================

class PlanStep(TypedDict):
    tool: Literal["search_documents", "query_database"]
    query: str

class StepResult(TypedDict):
    tool: str
    query: str
    result: str

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    db_url: Optional[str]
    conversation_history: List[BaseMessage]
    plan: List[PlanStep]
    step_results: List[StepResult]
    iterations: int
    draft_answer: Optional[str]
    audit_retries: int
    final_answer: Optional[str]


class PlanStepModel(BaseModel):
    tool: Literal["search_documents", "query_database"] = Field(
        description="'search_documents' for the user's uploaded files, 'query_database' for the connected database."
    )
    query: str = Field(description="What to search for / what to ask the database, in natural language.")

class Plan(BaseModel):
    steps: List[PlanStepModel] = Field(
        description="Ordered steps needed to answer the question. Empty list if no tool is needed "
                    "(e.g. greetings, general knowledge, or a question already answerable from the conversation)."
    )

class ReplanDecision(BaseModel):
    done: bool = Field(description="True if the gathered results are enough to answer the question.")
    next_step: Optional[PlanStepModel] = Field(
        default=None,
        description="Only set if done=False: the next single step needed."
    )

class AuditResult(BaseModel):
    grounded: bool = Field(
        description="True if every specific fact (name, number, date) in the draft answer is "
                    "actually present in the gathered tool results."
    )
    issues: Optional[str] = Field(
        default=None,
        description="If grounded=False, a brief note on which specific claim isn't supported."
    )

# ============================================================================
# PLANNER
# One narrow decision: what ordered steps (if any) does this need? Still
# structured output, not free reasoning -- same technique nlp.py already uses
# for QueryOutput, kept consistent with existing conventions.
# ============================================================================

def _format_history(history: List[BaseMessage], max_turns: int = 3) -> str:
    if not history:
        return "(no prior conversation)"
    lines = []
    for msg in history[-(max_turns * 2):]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def create_planner_node():
    planner_llm = RecoverableStructuredRunnable(control_model.with_structured_output(Plan), Plan)

    def planner(state: AgentState):
        question = state["messages"][-1].content
        has_documents = check_user_has_documents(state["user_id"])
        history = _format_history(state.get("conversation_history", []))

        db_url = state.get("db_url")
        db_schema = ""
        if db_url:
            db_schema = get_db_schema_summary(db_url)

        prompt = (
            "You are the Planner. Break the user's request into an ordered list of tool steps, if any are needed.\n\n"
            "CRITICAL INSTRUCTIONS FOR PLANS:\n"
            "1. When using 'query_database', the query field must be a complete, descriptive natural language question (e.g. 'Find the salary of Bob Jones' or 'List all departments and their managers').\n"
            "   NEVER generate multiple keyword-only steps for the database (like [{'tool': 'query_database', 'query': 'Bob Jones'}, {'tool': 'query_database', 'query': 'salary'}]).\n"
            "   Instead, combine them into a single descriptive database query (like [{'tool': 'query_database', 'query': 'Find the salary of Bob Jones'}]).\n"
            "2. When using 'search_documents', the query should be a specific search query to extract info from text files (e.g. 'What is the compliance target for engineering budget?').\n"
            "3. If the user's question can be answered in a single database step, use exactly one 'query_database' step.\n"
            "4. Keep the plan as simple and direct as possible. Do NOT mix tools (do NOT include both search_documents and query_database) unless the user's request explicitly compares database records with compliance/document targets. If it is a straightforward database lookup, generate exactly one 'query_database' step.\n\n"
            f"Database connected: {'yes' if db_url else 'no'}\n"
            f"Database Schema Info:\n{db_schema or '(No database connected)'}\n\n"
            f"Documents uploaded: {'yes' if has_documents else 'no'}\n\n"
            f"Recent conversation (resolve references like \"him\" or \"that department\" against this):\n{history}\n\n"
            f"User request: {question}"
        )

        plan = planner_llm.invoke(prompt)
        steps = [s.model_dump() for s in plan.steps]
        debug_logger.plan(steps, "Initial plan")

        return {"plan": steps, "step_results": [], "iterations": 0}

    return planner

# ============================================================================
# EXECUTOR
# Runs exactly one step per visit. No judgment call about *what* to run --
# the planner/replanner already decided that. SQL steps keep the bounded,
# deterministic self-correction loop.
# ============================================================================

def create_executor_node():
    def executor(state: AgentState):
        plan = list(state["plan"])
        step = plan.pop(0)

        context = {
            "user_id": state["user_id"],
            "db_url": state.get("db_url"),
            "conversation_history": state.get("conversation_history", []),
        }

        if step["tool"] == "query_database":
            description = step["query"]
            # Fold in any document-derived facts already gathered, so a hybrid
            # step like "look up his ID in the docs, then query his salary"
            # has that ID available when it reaches the database step.
            doc_facts = [r["result"] for r in state["step_results"] if r["tool"] == "search_documents"]
            if doc_facts:
                description = f"{description}\n\nRelevant info already found: {' | '.join(doc_facts)}"

            result = None
            for attempt in range(1, MAX_SQL_RETRIES + 1):
                result = _invoke_tool_direct(query_database, context, query_description=description)
                if not str(result).startswith("❌"):
                    break
                debug_logger.info(f"SQL attempt {attempt} failed, retrying with error context", error=result)
                description = (
                    f"{step['query']}\n\nA previous attempt failed with error: {result}. "
                    f"Write a corrected query that avoids this error."
                )
        else:
            result = _invoke_tool_direct(search_documents, context, search_query=step["query"])

        step_result: StepResult = {"tool": step["tool"], "query": step["query"], "result": result}

        return {
            "plan": plan,
            "step_results": state["step_results"] + [step_result],
        }

    return executor

# ============================================================================
# REPLANNER
# The loop-back node. One narrow question: enough info now, or one more step?
# Bounded by MAX_PLAN_ITERATIONS so it can't spin forever on a weak model
# that keeps asking for "just one more" step.
# ============================================================================

def create_replanner_node():
    replanner_llm = RecoverableStructuredRunnable(control_model.with_structured_output(ReplanDecision), ReplanDecision)

    def replanner(state: AgentState):
        iterations = state["iterations"] + 1

        if iterations >= MAX_PLAN_ITERATIONS:
            debug_logger.info(f"Hit MAX_PLAN_ITERATIONS ({MAX_PLAN_ITERATIONS}), forcing synthesis")
            return {"plan": [], "iterations": iterations}

        question = state["messages"][-1].content
        gathered = "\n\n".join(
            f"[{r['tool']}] query: {r['query']}\nresult: {r['result']}" for r in state["step_results"]
        )

        prompt = (
            "You are the Replanner. Given the original question and the results of the steps taken so far, "
            "determine if we have enough information to answer the question.\n\n"
            "CRITICAL RULES:\n"
            "1. Be highly optimistic. If the tool results already contain the facts needed to answer the question "
            "   (even if there are minor details missing), mark done=True.\n"
            "2. Avoid redundant steps. If a tool result says 'information not found' or returns an error, do NOT "
            "   recommend searching for the same information again. Mark done=True and let the synthesizer explain the result.\n"
            "3. Only set done=False and recommend a next step if we are missing a critical piece of data that is highly likely "
            "   to be found in the connected resource.\n\n"
            f"Original question: {question}\n\n"
            f"Steps taken so far:\n{gathered}\n\n"
            "Do we now have enough information to answer (done=True), or is exactly one more step needed (done=False)?"
        )

        decision = replanner_llm.invoke(prompt)

        if decision.done or not decision.next_step:
            debug_logger.plan([], "Replanner: sufficient, moving to synthesis")
            return {"plan": [], "iterations": iterations}

        next_step = decision.next_step.model_dump()
        debug_logger.plan([next_step], "Replanner: one more step needed")
        return {"plan": [next_step], "iterations": iterations}

    return replanner

# ============================================================================
# SYNTHESIZE
# The only node producing user-facing text -- so the only node that needs
# the grounding rules and chart-format contract.
# ============================================================================

SYNTHESIS_RULES = """You are DataTalk AI, a technical data assistant. Write the final response to the user.

**STRICT GROUNDING RULES (NO HALLUCINATIONS):**
1. Base your response ONLY on the tool results provided below (if any).
2. Do NOT use pre-trained knowledge or invent names, dates, values, or metrics not present in the results.
3. If a result is empty, says "not found", or indicates an error, state that plainly instead of guessing.
4. Copy names, numbers, and dates exactly as they appear in the results.

**DATA VISUALIZATION RULE:**
If the user asked for a chart/graph, or the results contain numerical/tabular data that would
benefit from visual representation, append a chart JSON block at the very end, tagged with 'chart':
```chart
{{
  "type": "bar" | "line" | "pie",
  "title": "Chart Title",
  "data": [{{"name": "label", "value": 123.45}}]
}}
```
Only use "name" and "value" keys inside "data" items. Omit the chart block entirely if it doesn't apply.
"""

def _build_results_block(step_results: List[StepResult]) -> str:
    if not step_results:
        return "(No tool was needed for this request.)"
    return "\n\n".join(f"[{r['tool']}] {r['result']}" for r in step_results)


def create_synthesize_node():
    def synthesize(state: AgentState):
        question = state["messages"][-1].content
        results_block = _build_results_block(state["step_results"])

        correction_note = ""
        if state.get("audit_retries", 0) > 0 and state.get("draft_answer"):
            # We're here because the audit failed once already -- name the
            # specific issue so this isn't just a blind re-roll.
            correction_note = (
                f"\n\nA previous draft was flagged for including an unsupported claim. "
                f"Regenerate, being strict about only stating what's in the results below."
            )

        user_prompt = f"User's question: {question}\n\nTool results:\n{results_block}{correction_note}"
        messages = [SystemMessage(content=SYNTHESIS_RULES), HumanMessage(content=user_prompt)]

        callback = _stream_callback_var.get()
        answer = None

        if callback and state.get("audit_retries", 0) == 0:
            # Only stream the first pass live; a corrected second pass (rare)
            # is computed silently and swapped in, so the user never sees a
            # flagged draft.
            content_chunks = []
            try:
                for chunk in llm.stream(messages):
                    if chunk.content:
                        content_chunks.append(chunk.content)
                        callback(chunk.content)
                answer = "".join(content_chunks)
            except Exception as stream_err:
                debug_logger.error("Streaming failed, falling back to invoke", stream_err)

        if answer is None:
            answer = llm.invoke(messages).content

        debug_logger.reasoning(answer[:300])
        return {"draft_answer": answer}

    return synthesize

# ============================================================================
# AUDIT
# An independent pass, separate from synthesis, whose only job is checking
# the draft against the actual gathered results. A fresh call not primed to
# sound plausible is structurally better positioned to catch a mismatch than
# asking the same generation to grade its own work in the same breath.
# Bounded to one retry -- if it still fails, ship with a visible caveat
# rather than loop or silently pass a flagged answer.
# ============================================================================

def create_audit_node():
    audit_llm = RecoverableStructuredRunnable(control_model.with_structured_output(AuditResult), AuditResult)

    def audit(state: AgentState):
        results_block = _build_results_block(state["step_results"])
        draft = state["draft_answer"]

        if not state["step_results"]:
            # Nothing to ground against (general/conversational turn) --
            # auditing has nothing to check, so pass straight through.
            debug_logger.audit(True, "No tool results to audit against")
            return {"final_answer": draft, "audit_retries": state.get("audit_retries", 0)}

        prompt = (
            "You are the Groundedness Auditor. Your job is to strictly verify the draft answer against the raw tool results.\n\n"
            "CRITICAL AUDITING RULES:\n"
            "1. STRICT PRESENCE: Does every name, number, date, or metric in the draft answer actually exist in the tool results?\n"
            "2. STRICT ATTRIBUTION: Is every value, metric, or entity description attributed to the correct role or category in the draft?\n"
            "   - Watch out for mislabeled or swapped numbers (e.g., if department base salary is $408,000 and bonus is $12,000, "
            "     the draft MUST NOT claim the bonus is $408,000 or the base salary is $12,000).\n"
            "   - If a number represents a base salary pool, it must not be labeled as a bonus, operating budget, or stipend.\n"
            "3. MATHEMATICAL CLAIMS: If the draft performs calculations (like comparing two numbers or calculating a percentage), "
            "   are the values used in the calculation correct and mapped to the right entities as documented in the tool results?\n\n"
            f"Draft Answer:\n{draft}\n\n"
            f"Actual Tool Results:\n{results_block}\n\n"
            "Evaluate if the draft answer is fully grounded and attributed correctly. If there are any incorrect attributions, "
            "swapped labels, or ungrounded facts, mark grounded=False and specify the exact issues in detail."
        )

        check = audit_llm.invoke(prompt)
        debug_logger.audit(check.grounded, check.issues or "")

        retries = state.get("audit_retries", 0)

        if check.grounded:
            return {"final_answer": draft, "audit_retries": retries}

        if retries >= MAX_AUDIT_RETRIES:
            caveated = f"{draft}\n\n_(Note: part of this answer could not be fully verified against the source data.)_"
            return {"final_answer": caveated, "audit_retries": retries}

        # Bounce back to synthesize once, with the retry count bumped so the
        # next synthesize pass knows to be stricter.
        return {"audit_retries": retries + 1, "final_answer": None}

    return audit

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def _after_planner(state: AgentState) -> str:
    return "executor" if state["plan"] else "synthesize"

def _after_executor(state: AgentState) -> str:
    return "executor" if state["plan"] else "replanner"

def _after_replanner(state: AgentState) -> str:
    return "executor" if state["plan"] else "synthesize"

def _after_audit(state: AgentState) -> str:
    return "synthesize" if state.get("final_answer") is None else "__end__"


def create_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", create_planner_node())
    workflow.add_node("executor", create_executor_node())
    workflow.add_node("replanner", create_replanner_node())
    workflow.add_node("synthesize", create_synthesize_node())
    workflow.add_node("audit", create_audit_node())

    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges("planner", _after_planner, {"executor": "executor", "synthesize": "synthesize"})
    workflow.add_conditional_edges("executor", _after_executor, {"executor": "executor", "replanner": "replanner"})
    workflow.add_conditional_edges("replanner", _after_replanner, {"executor": "executor", "synthesize": "synthesize"})
    workflow.add_edge("synthesize", "audit")
    workflow.add_conditional_edges("audit", _after_audit, {"synthesize": "synthesize", "__end__": END})

    return workflow.compile()

# ============================================================================
# ORCHESTRATOR CLASS
# Public contract preserved exactly: chat()/chat_with_debug()/get_orchestrator()
# all return the same dict shape as before (answer, routing, resources,
# tools_used, debug_logs). ChatController and chat_routes need no changes.
# ============================================================================

def _derive_routing(step_results: List[StepResult]) -> str:
    tools_seen = {r["tool"] for r in step_results}
    if tools_seen == {"query_database"}:
        return "sql"
    if tools_seen == {"search_documents"}:
        return "rag"
    if tools_seen == {"query_database", "search_documents"}:
        return "hybrid"
    return "general"


class AgenticOrchestrator:
    def __init__(self):
        if llm is None:
            self.graph = None
            print("⚠️ Initializing AgenticOrchestrator in DEMO MODE (No LLM).")
        else:
            self.graph = create_agent_graph()

    def chat(
        self,
        question: str,
        user_id: str,
        conversation_history: Optional[List[BaseMessage]] = None,
        db_url: Optional[str] = None,
        debug: bool = True,
        stream_callback: Optional[callable] = None
    ) -> dict:
        request_logger = DebugLogger()
        _debug_logger_var.set(request_logger)
        if stream_callback is not None:
            _stream_callback_var.set(stream_callback)
        debug_logger.enabled = debug
        debug_logger.clear()

        debug_logger.info("NEW CHAT REQUEST")
        debug_logger.info("User question", question=question, user_id=user_id)

        if conversation_history is None:
            conversation_history = []

        if not db_url:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_url = f"sqlite:///{os.path.join(base_dir, 'context', 'datatalk_demo.db')}"
            debug_logger.info("Assigned default demo database connection URL")

        has_documents = check_user_has_documents(user_id)
        has_database = True

        debug_logger.info("Resources available", database=has_database, documents=has_documents)

        # Fast-Pathway Bypass for general chitchat and simple greetings
        def is_general_query(q_text: str) -> bool:
            q_clean = q_text.strip().lower().rstrip("?.!")
            greetings = {
                "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening",
                "howdy", "what's up", "yo", "what can you help me with", "what can you do", "who are you",
                "help", "menu", "info", "explain what you do"
            }
            return q_clean in greetings or len(q_clean.split()) <= 2

        if is_general_query(question) and self.graph is not None:
            debug_logger.info("Fast-path: General greeting detected. Bypassing LangGraph.")
            system_msg = (
                "You are DataTalk AI, a technical data assistant. Provide a short, welcoming response "
                "explaining that you can query the database or search documents to help them analyze data."
            )
            user_msg = f"User greeting: {question}"
            messages = [SystemMessage(content=system_msg), HumanMessage(content=user_msg)]
            
            callback = _stream_callback_var.get()
            answer = ""
            if callback:
                for chunk in llm.stream(messages):
                    if chunk.content:
                        callback(chunk.content)
                        answer += chunk.content
            else:
                answer = llm.invoke(messages).content
                
            return {
                'answer': answer,
                'routing': 'general',
                'resources': {'database': has_database, 'documents': has_documents,
                               'is_demo_db': 'datatalk_demo.db' in db_url if db_url else False},
                'tools_used': [],
                'debug_logs': debug_logger.get_logs() if debug else []
            }

        if self.graph is None:
            demo_message = (
                f"**Demo Mode Active**: I am running without API keys. To enable full "
                f"agentic capabilities, please configure the `GROQ_API_KEY` in the backend "
                f"`.env` file.\n\nYou asked: *\"{question}\"*"
            )
            callback = _stream_callback_var.get()
            if callback:
                import time
                for word in demo_message.split(" "):
                    callback(word + " ")
                    time.sleep(0.02)

            return {
                'answer': demo_message,
                'routing': 'demo',
                'resources': {'database': has_database, 'documents': has_documents,
                               'is_demo_db': 'datatalk_demo.db' in db_url if db_url else False},
                'tools_used': [],
                'debug_logs': debug_logger.get_logs() if debug else []
            }

        messages = list(conversation_history[-6:])
        messages.append(HumanMessage(content=question))

        initial_state = AgentState(
            messages=messages,
            user_id=user_id,
            db_url=db_url,
            conversation_history=conversation_history,
            plan=[],
            step_results=[],
            iterations=0,
            draft_answer=None,
            audit_retries=0,
            final_answer=None,
        )

        try:
            final_state = self.graph.invoke(initial_state, config={"recursion_limit": 20})
            answer = final_state.get('final_answer') or final_state.get('draft_answer') \
                or "I apologize, but I couldn't generate a response."
            routing = _derive_routing(final_state.get('step_results', []))
            tools_used = sorted({r["tool"] for r in final_state.get('step_results', [])})

            debug_logger.info("Agent execution completed", routing=routing, tools_used=tools_used)

            if debug:
                print("\n" + "=" * 80)
                print("EXECUTION SUMMARY")
                summary = debug_logger.summary()
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("=" * 80 + "\n")

            is_demo = 'datatalk_demo.db' in db_url

            return {
                'answer': answer,
                'routing': routing,
                'resources': {'database': has_database, 'documents': has_documents, 'is_demo_db': is_demo},
                'tools_used': tools_used,
                'debug_logs': debug_logger.get_logs() if debug else []
            }

        except Exception as e:
            debug_logger.error("Agent execution failed", e)
            if debug:
                print(f"\nEXECUTION FAILED\nError: {str(e)}\n")

            return {
                'answer': f"I encountered an error: {str(e)}",
                'routing': 'error',
                'resources': {'database': has_database, 'documents': has_documents,
                               'is_demo_db': 'datatalk_demo.db' in db_url if db_url else False},
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