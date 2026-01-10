from agents.graph import build_agent
from agents.state import AgentState
from typing import Dict, Any

agent = build_agent()

STATE_FILE = "data/conversation_history/conversation_state.txt"

def store_agent_state(state: Dict[str, Any], thread_id: str) -> None:
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"THREAD ID: {thread_id}\n")
        f.write("=" * 60 + "\n")

        # Messages
        f.write("\nMESSAGES:\n")
        for i, msg in enumerate(state.get("messages", []), start=1):
            f.write(f"  {i}. {msg['role'].upper()}: {msg['content']}\n")

        # Planner / tool info
        f.write("\nPLANNER / TOOL:\n")
        f.write(f"  tool       : {state.get('tool')}\n")

        # Tool inputs
        f.write("\nTOOL INPUT:\n")
        for i, ti in enumerate(state.get("tool_input", []), start=1):
            f.write(f"  {i}. {ti}\n")

        # Tool outputs
        f.write("\nTOOL OUTPUT:\n")
        for i, to in enumerate(state.get("tool_output", []), start=1):
            f.write(f"  {i}. {to}\n")

        # Final output
        f.write("\nFINAL OUTPUT:\n")
        f.write(f"  {state.get('output')}\n")

        # Diagnostics
        f.write("\nDIAGNOSTICS:\n")
        f.write(f"  llm_calls  : {state.get('llm_calls')}\n")

        f.write("\n" + "=" * 60 + "\n")


def run_agent(user_input: str, thread_id: str = "default") -> str:
    initial_state: AgentState = {
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "tool": "",
        "output": "",
        "llm_calls": 0,
        "tool_input": [],
        "tool_output": []
    }

    result = agent.invoke(
        initial_state,
        {"configurable": {"thread_id": thread_id}}
    )

    store_agent_state(result, thread_id)
    return result["output"]
