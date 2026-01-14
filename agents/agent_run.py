from agents.graph import build_agent
from agents.state import AgentState
from typing import Dict, Any
from langchain_core.messages import HumanMessage

agent = build_agent()

# STATE_FILE = "data/conversation_history/conversation_state.txt"


def run_agent(task: str, thread_id: str = "default") -> dict:
    
    config={"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {
            "task": task,
            "messages": [HumanMessage(content=task)],
            "tool": "none",
            "output": "",
            "llm_calls": 0,
            "tool_input": [],
            "tool_output": [],
            "images": []
        },
        config
    )
    return {
        "output": result["output"],
        "images": result.get("images", [])
    }
