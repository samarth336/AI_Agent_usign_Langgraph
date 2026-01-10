from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from agents.state import AgentState
from agents.planner import planner
from agents.tools import search_tool
from agents.response_generator import response_generator


def route_from_planner(state: AgentState) -> str:
    if state["tool"] == "search":
        return "search"
    return END


def build_agent():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner)
    builder.add_node("search", search_tool)
    builder.add_node("response_generator", response_generator)

    builder.set_entry_point("planner")

    builder.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "search": "search",
            END: END
        }
    )

    builder.add_edge("search", "response_generator")
    builder.add_edge("response_generator", END)

    # SHORT-TERM MEMORY (LangGraph way)
    checkpointer = InMemorySaver()

    agent = builder.compile(checkpointer=checkpointer)

    print(agent.get_graph().draw_ascii())
    return agent
