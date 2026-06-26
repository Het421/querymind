from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    """
    The shared state that travels through every node
    in the LangGraph agent.

    Every node reads from this and writes back to it.
    Think of it as the clipboard passed along the assembly line.
    """

    # --- Input fields (set before the graph runs) ---

    # The question the user typed
    user_question: str

    # Which SQL platform the user is working on
    # e.g. "postgresql", "mysql", "sqlite", "sqlserver"
    platform: str

    # The raw schema DDL text of the active schema
    schema_content: str

    # Recent chat history for context
    # List of dicts like [{"role": "user", "message": "..."}]
    chat_history: List[dict]

    # --- Intermediate fields (filled by nodes as they run) ---

    # What kind of task this is
    # "generate" / "explain" / "optimise" / "convert" / "general"
    intent: Optional[str]

    # The relevant parts of schema extracted for this question
    # On large schemas we don't inject everything — just relevant tables
    relevant_schema: Optional[str]

    # The raw SQL output from the LLM
    generated_sql: Optional[str]

    # Whether the SQL passed validation
    is_valid: Optional[bool]

    # Error message if validation failed
    validation_error: Optional[str]

    # How many times we have retried generation
    # We stop retrying after 2 attempts to avoid infinite loops
    retry_count: int

    # Plain English explanation of the SQL
    explanation: Optional[str]

    # --- Output fields (filled by the last node) ---

    # The final SQL to return to the user
    final_sql: Optional[str]

    # The final explanation to return to the user
    final_explanation: Optional[str]

    # Final response for non-SQL answers (general questions)
    final_response: Optional[str]