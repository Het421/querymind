from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState
from backend.agent.nodes import (
    intent_router,
    schema_injector,
    sql_generator,
    sql_validator,
    explainer
)


def should_retry_or_end(state: AgentState) -> str:
    """
    Conditional edge function — called after the validator runs.
    Decides whether to retry generation or move to explainer.

    Returns the name of the next node to run.
    """

    # If SQL is valid — move to explainer
    if state.get("is_valid"):
        return "explainer"

    # If validation failed but we haven't hit retry limit — retry
    if state.get("retry_count", 0) < 2:
        return "sql_generator"

    # Retry limit hit — move on anyway with whatever we have
    # Better to return something than nothing
    return "explainer"


def build_agent() -> StateGraph:
    """
    Builds and compiles the LangGraph agent.
    Returns a compiled graph ready to invoke.
    """

    # Create the graph with our state definition
    graph = StateGraph(AgentState)

    # Add all nodes to the graph
    graph.add_node("intent_router", intent_router)
    graph.add_node("schema_injector", schema_injector)
    graph.add_node("sql_generator", sql_generator)
    graph.add_node("sql_validator", sql_validator)
    graph.add_node("explainer", explainer)

    # Define the flow — set entry point
    graph.set_entry_point("intent_router")

    # Fixed edges — always go from A to B
    graph.add_edge("intent_router", "schema_injector")
    graph.add_edge("schema_injector", "sql_generator")
    graph.add_edge("sql_generator", "sql_validator")

    # Conditional edge — after validator, decide what to do next
    graph.add_conditional_edges(
        "sql_validator",       # from this node
        should_retry_or_end,   # call this function to decide
        {
            "sql_generator": "sql_generator",  # retry path
            "explainer": "explainer"           # success path
        }
    )

    # Explainer is always the last node
    graph.add_edge("explainer", END)

    # Compile and return
    return graph.compile()


# Single compiled agent instance
# Everyone imports this — we don't rebuild the graph on every request
agent = build_agent()