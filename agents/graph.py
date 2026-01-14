from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os

from agents.state import AgentState
from agents.planner import planner
from agents.tools import search_tool
from agents.response_generator import response_generator


def route_from_planner(state: AgentState) -> str:
    tool = state.get("tool", "none")
    if tool == "search":
        print("Routing to search tool")
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

    # -------------------------
    # SQLITE SHORT-TERM MEMORY
    # -------------------------
    os.makedirs("data/conversation_history", exist_ok=True)

    conn = sqlite3.connect(
        "data/conversation_history/conversation_state.db",
        check_same_thread=False
    )

    # Recommended SQLite settings
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    checkpoint = SqliteSaver(conn)

    agent = builder.compile(checkpointer=checkpoint)

    print(agent.get_graph().draw_ascii())
    return agent
