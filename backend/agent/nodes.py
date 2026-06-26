from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from backend.agent.state import AgentState
from backend.config import settings
from backend.prompts.sql_prompt import (
    build_system_prompt,
    INTENT_PROMPT,
    SCHEMA_EXTRACTION_PROMPT,
    EXPLAINER_PROMPT
)
import sqlparse


# Initialise the LLM once — reused across all nodes
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)


# ── NODE 1: Intent Router ──────────────────────────────────────────

def intent_router(state: AgentState) -> AgentState:
    """
    Classifies the user question into one of five intent categories.
    Uses the dedicated intent prompt for consistent classification.
    """
    messages = [
        SystemMessage(content=INTENT_PROMPT),
        HumanMessage(content=state["user_question"])
    ]

    result = llm.invoke(messages)
    intent = result.content.strip().lower()

    valid_intents = ["generate", "explain", "optimise", "convert", "general"]
    if intent not in valid_intents:
        intent = "generate"

    return {**state, "intent": intent}


# ── NODE 2: Schema Injector ────────────────────────────────────────

def schema_injector(state: AgentState) -> AgentState:
    """
    Injects the relevant schema into state.
    For small schemas uses everything.
    For large schemas extracts only relevant tables.
    """
    schema_content = state.get("schema_content", "")
    user_question = state["user_question"]

    # Small schema — use it all
    if len(schema_content) <= 4000:
        return {**state, "relevant_schema": schema_content}

    # Large schema — extract relevant tables only
    messages = [
        SystemMessage(content=SCHEMA_EXTRACTION_PROMPT),
        HumanMessage(content=f"Schema:\n{schema_content}\n\nQuestion: {user_question}")
    ]

    result = llm.invoke(messages)
    return {**state, "relevant_schema": result.content.strip()}


# ── NODE 3: SQL Generator ──────────────────────────────────────────

def sql_generator(state: AgentState) -> AgentState:
    """
    Core node — generates SQL using the improved dialect-aware prompt.
    Includes chat history for context and retry instructions if needed.
    """

    # Build chat history context
    history_text = ""
    if state.get("chat_history"):
        history_lines = []
        for msg in state["chat_history"]:
            role = msg.get("role", "user").capitalize()
            message = msg.get("message", "")
            history_lines.append(f"{role}: {message}")
        history_text = "\n".join(history_lines)
    else:
        history_text = "No previous conversation."

    # Build retry context if this is a retry
    retry_context = ""
    if state.get("retry_count", 0) > 0:
        retry_context = f"""
IMPORTANT — Your previous attempt had invalid SQL:
{state.get('validation_error', '')}
Please carefully fix this error in your new response.
"""

    # Build the system prompt with dialect rules injected
    system_prompt = build_system_prompt(state["platform"]).format(
        schema=state.get("relevant_schema", state.get("schema_content", "")),
        retry_context=retry_context
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""Previous conversation:
{history_text}

Current question: {state["user_question"]}""")
    ]

    result = llm.invoke(messages)
    raw_response = result.content.strip()

    # Parse SQL from code block
    generated_sql = None
    explanation = None

    if "```sql" in raw_response:
        sql_start = raw_response.find("```sql") + 6
        sql_end = raw_response.find("```", sql_start)
        generated_sql = raw_response[sql_start:sql_end].strip()

    # Parse explanation
    if "EXPLANATION:" in raw_response:
        explanation_start = raw_response.find("EXPLANATION:") + 12
        explanation = raw_response[explanation_start:].strip()
    elif generated_sql:
        after_sql = raw_response[raw_response.rfind("```") + 3:].strip()
        if after_sql:
            explanation = after_sql

    # No SQL found — general response
    if not generated_sql:
        return {
            **state,
            "generated_sql": None,
            "explanation": None,
            "final_sql": None,
            "final_explanation": None,
            "final_response": raw_response,
            "is_valid": True
        }

    return {
        **state,
        "generated_sql": generated_sql,
        "explanation": explanation,
        "final_response": None
    }


# ── NODE 4: SQL Validator ──────────────────────────────────────────

def sql_validator(state: AgentState) -> AgentState:
    """
    Validates SQL syntax using sqlparse.
    Triggers retry if invalid, up to 2 attempts.
    """

    if not state.get("generated_sql"):
        return {**state, "is_valid": True}

    sql = state["generated_sql"]

    try:
        parsed = sqlparse.parse(sql)

        if not parsed or not parsed[0].tokens:
            return {
                **state,
                "is_valid": False,
                "validation_error": "Could not parse SQL — empty or invalid statement.",
                "retry_count": state.get("retry_count", 0) + 1
            }

        if not str(parsed[0]).strip():
            return {
                **state,
                "is_valid": False,
                "validation_error": "Generated SQL is empty.",
                "retry_count": state.get("retry_count", 0) + 1
            }

        return {
            **state,
            "is_valid": True,
            "validation_error": None,
            "final_sql": sql,
            "final_explanation": state.get("explanation")
        }

    except Exception as e:
        return {
            **state,
            "is_valid": False,
            "validation_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }


# ── NODE 5: Explainer ──────────────────────────────────────────────

def explainer(state: AgentState) -> AgentState:
    """
    Enhances the explanation if one wasn't already generated.
    Uses the dedicated explainer prompt for clear breakdowns.
    """

    if not state.get("final_sql"):
        return state

    # Already have a good explanation — keep it
    if state.get("final_explanation"):
        return state

    messages = [
        SystemMessage(content=EXPLAINER_PROMPT),
        HumanMessage(content=f"SQL:\n{state['final_sql']}\n\nPlatform: {state['platform']}")
    ]

    result = llm.invoke(messages)
    return {**state, "final_explanation": result.content.strip()}