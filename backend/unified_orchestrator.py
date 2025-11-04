"""
Unified Orchestrator - Intelligent routing between SQL and RAG systems
Decides whether to use nlp.py (SQL), rag.py (documents), or both
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional
from dotenv import load_dotenv

# Import your existing systems
from nlp import ask_database  # SQL querying
from utils.retriever_helper import get_user_retriever, check_user_has_documents

load_dotenv()

# LLM for routing and synthesis
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


class UnifiedOrchestrator:
    """
    Smart orchestrator that routes queries intelligently:
    - SQL queries → nlp.py (database querying)
    - Document queries → RAG system (vectorized documents)
    - Hybrid queries → Both systems with synthesis
    """
    
    def __init__(self):
        self.llm = llm
    
    def _classify_intent(
        self, 
        question: str, 
        has_documents: bool, 
        has_database: bool,
        conversation_history: List[BaseMessage]
    ) -> str:
        """
        Classify the user's intent to determine routing.
        
        Returns: 'sql', 'rag', 'hybrid', or 'general'
        """
        # No resources available
        if not has_documents and not has_database:
            return 'general'
        
        # Only one resource available
        if has_documents and not has_database:
            return 'rag'
        if has_database and not has_documents:
            return 'sql'
        
        # Both available - need to classify
        # Get recent context
        recent_context = ""
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 2 exchanges
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                recent_context += f"{role}: {msg.content}\n"
        
        classification_prompt = f"""You are a query router for a data analysis system. Analyze the user's question and classify it.

**AVAILABLE RESOURCES:**
- SQL Database: Structured data (employees, transactions, records, etc.)
- Document Store: PDF documents uploaded by the user

**CLASSIFICATION RULES:**

1. **SQL** - Use for questions about:
   - Structured data queries (counts, sums, averages, filtering)
   - Database records (employees, customers, orders, etc.)
   - Comparisons, rankings, aggregations
   - Keywords: "how many", "total", "average", "list all", "find", "who", "when"
   - Examples: "How many employees?", "Average salary?", "List departments"
   - to execute DDL AND DML queries

2. **RAG** - Use for questions about:
   - Document content, explanations, concepts
   - Information from uploaded PDFs
   - Policies, procedures, definitions
   - Keywords: "what does document say", "according to", "explain", "describe"
   - Examples: "What is the company policy?", "Explain the procedure"

3. **HYBRID** - Use when question needs BOTH:
   - Combining database data with document context
   - Verifying data against documentation
   - Complex analysis requiring both sources
   - Examples: "Do employee salaries match the policy?", "Compare actual vs documented"

4. **GENERAL** - Use for:
   - Greetings, small talk
   - Questions about capabilities
   - Unclear or ambiguous questions

**RECENT CONVERSATION:**
{recent_context}

**CURRENT QUESTION:**
{question}

Respond with ONLY ONE WORD: sql, rag, hybrid, or general
Do not include any explanation, just the classification word."""
        
        try:
            response = self.llm.invoke(classification_prompt)
            classification = response.content.strip().lower()
            
            # Validate classification
            valid = ['sql', 'rag', 'hybrid', 'general']
            if classification not in valid:
                # Default based on keywords as fallback
                question_lower = question.lower()
                if any(kw in question_lower for kw in ['how many', 'total', 'average', 'list', 'count']):
                    return 'sql'
                elif any(kw in question_lower for kw in ['document', 'policy', 'explain', 'describe']):
                    return 'rag'
                else:
                    return 'general'
            
            return classification
        except Exception as e:
            print(f"Classification error: {e}")
            return 'general'
    
    def _query_sql(
        self, 
        question: str, 
        conversation_history: List[BaseMessage], 
        db_url: str
    ) -> str:
        """Use nlp.py to query and manipulate the SQL database (DDL and DML queries)"""
        try:
            return ask_database(question, conversation_history, db_url)
        except Exception as e:
            return f"Database query error: {str(e)}"
    
    def _query_rag(
        self, 
        question: str, 
        conversation_history: List[BaseMessage], 
        user_id: str
    ) -> str:
        """Query the RAG system using user's vectorized documents"""
        try:
            # Get user-specific retriever
            retriever = get_user_retriever(user_id, k=4)
            
            # Retrieve relevant documents
            docs = retriever.get_relevant_documents(question)
            
            if not docs:
                return "I couldn't find relevant information in your uploaded documents to answer this question."
            
            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs, 1):
                # Get filename from metadata
                filename = doc.metadata.get('filename', 'Unknown')
                content = doc.page_content[:500]  # Limit chunk size
                context_parts.append(f"[Source: {filename}]\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Format recent conversation history
            history_text = ""
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 3 exchanges
                    role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                    history_text += f"{role}: {msg.content}\n"
            
            # Generate answer using LLM
            rag_prompt = f"""You are a helpful assistant answering questions based on the user's uploaded documents.

**CONVERSATION HISTORY:**
{history_text}

**USER QUESTION:**
{question}

**RELEVANT DOCUMENT EXCERPTS:**
{context}

**INSTRUCTIONS:**
- Answer the question using ONLY the information from the document excerpts above
- Be conversational and natural in your response
- Cite which document (by filename) you're referencing when relevant
- If the excerpts don't contain enough information to answer fully, say so clearly
- Do not make up or assume information not present in the excerpts
- Keep your response clear and concise

**YOUR ANSWER:**"""
            
            response = self.llm.invoke(rag_prompt)
            return response.content
            
        except Exception as e:
            return f"Document search error: {str(e)}"
    
    def _query_hybrid(
        self, 
        question: str, 
        conversation_history: List[BaseMessage],
        db_url: str,
        user_id: str
    ) -> str:
        """Query both SQL and RAG, then synthesize results"""
        
        # Query both systems in parallel-ish
        sql_result = self._query_sql(question, conversation_history, db_url)
        rag_result = self._query_rag(question, conversation_history, user_id)
        
        # Check if both queries returned useful results
        sql_has_data = sql_result and not sql_result.startswith("Database query error")
        rag_has_data = rag_result and not rag_result.startswith("Document search error") and "couldn't find" not in rag_result.lower()
        
        # If only one system returned data, use that
        if sql_has_data and not rag_has_data:
            return sql_result
        if rag_has_data and not sql_has_data:
            return rag_result
        if not sql_has_data and not rag_has_data:
            return "I couldn't find relevant information in either the database or your documents to answer this question."
        
        # Both have data - synthesize
        synthesis_prompt = f"""You are a data analyst synthesizing information from multiple sources.

**USER QUESTION:**
{question}

**DATABASE ANALYSIS:**
{sql_result}

**DOCUMENT INSIGHTS:**
{rag_result}

**TASK:**
Combine both pieces of information into a single, coherent answer that:
1. Addresses the user's question completely
2. Clearly distinguishes between database facts and document information
3. Highlights any interesting connections or discrepancies
4. Maintains a natural, conversational tone
5. Is concise but comprehensive

**SYNTHESIZED ANSWER:**"""
        
        try:
            response = self.llm.invoke(synthesis_prompt)
            return response.content
        except Exception as e:
            # Fallback to returning both separately
            return f"**From Database:**\n{sql_result}\n\n**From Documents:**\n{rag_result}"
    
    def _general_response(
        self, 
        question: str, 
        conversation_history: List[BaseMessage],
        has_documents: bool,
        has_database: bool
    ) -> str:
        """Handle general queries or small talk"""
        
        # Build context about available resources
        resources = []
        if has_database:
            resources.append("a connected database")
        if has_documents:
            resources.append("uploaded documents")
        
        resources_text = " and ".join(resources) if resources else "no data sources yet"
        
        # Recent conversation context
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                history_text += f"{role}: {msg.content}\n"
        
        general_prompt = f"""You are DataTalk AI, a helpful assistant that helps users analyze their data.

**CONVERSATION HISTORY:**
{history_text}

**USER MESSAGE:**
{question}

**AVAILABLE RESOURCES:**
The user currently has: {resources_text}

**YOUR ROLE:**
- Respond naturally and helpfully to the user's message
- If they're asking about capabilities, explain:
  * They can upload PDF documents for Q&A
  * They can connect a database for SQL querying
  * You can answer questions about both sources
- If they're greeting you or making small talk, respond warmly
- Keep responses brief and friendly

**YOUR RESPONSE:**"""
        
        try:
            response = self.llm.invoke(general_prompt)
            return response.content
        except Exception as e:
            return "Hello! I'm DataTalk AI. I can help you analyze data from your database and documents. How can I assist you today?"
    
    def chat(
        self,
        question: str,
        user_id: str,
        conversation_history: Optional[List[BaseMessage]] = None,
        db_url: Optional[str] = None
    ) -> dict:
        """
        Main entry point for chat interactions.
        
        Args:
            question: User's question
            user_id: User's unique identifier
            conversation_history: Previous messages for context
            db_url: Database connection URL (optional)
        
        Returns:
            dict with:
                - answer: The response text
                - routing: Which system(s) were used
                - resources: What resources are available
        """
        if conversation_history is None:
            conversation_history = []
        
        # Check available resources
        has_documents = check_user_has_documents(user_id)
        has_database = db_url is not None and db_url.strip() != ""
        
        # Classify the query intent
        intent = self._classify_intent(
            question, 
            has_documents, 
            has_database, 
            conversation_history
        )
        print("intent: ", intent)
        # Route to appropriate handler
        if intent == 'sql' and has_database:
            answer = self._query_sql(question, conversation_history, db_url)
        elif intent == 'rag' and has_documents:
            answer = self._query_rag(question, conversation_history, user_id)
        elif intent == 'hybrid' and has_database and has_documents:
            answer = self._query_hybrid(question, conversation_history, db_url, user_id)
        else:
            # General response or fallback
            answer = self._general_response(
                question, 
                conversation_history, 
                has_documents, 
                has_database
            )
            intent = 'general'
        
        return {
            'answer': answer,
            'routing': intent,
            'resources': {
                'database': has_database,
                'documents': has_documents
            }
        }


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> UnifiedOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedOrchestrator()
    return _orchestrator_instance


# Convenience function matching your old interface
def chat(
    question: str, 
    conversation_history: List[BaseMessage], 
    db_url: str,
    user_id: str = None
) -> str:
    """
    Backwards compatible interface.
    
    Args:
        question: User's question
        conversation_history: Previous messages
        db_url: Database URL
        user_id: User ID (required for RAG)
    
    Returns:
        Answer string
    """
    if user_id is None:
        raise ValueError("user_id is required for unified orchestrator")
    
    orchestrator = get_orchestrator()
    result = orchestrator.chat(question, user_id, conversation_history, db_url)
    return result['answer']