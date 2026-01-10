from agents.state import AgentState
from langchain_community.tools import DuckDuckGoSearchRun


# -------------------------
# Web search helper
# -------------------------
def web_search(query: str) -> str:
    search = DuckDuckGoSearchRun()
    return search.run(query)


# -------------------------
# Search tool node
# -------------------------
def search_tool(state: AgentState) -> AgentState:
    """
    Executes web search using the user's last query.
    """
    query = state["tool_input"][-1]

    result = web_search(query)

    state["tool_output"] = [f"{query}':\n{result}"]
    return state
