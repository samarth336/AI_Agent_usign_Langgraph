from agents.graph import build_agent
from agents.state import AgentState
from typing import Dict, Any, Iterator, cast
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

agent = build_agent()

# STATE_FILE = "data/conversation_history/conversation_state.txt"


def run_agent(task: str, thread_id: str = "default") -> dict:
    
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
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


def run_agent_stream(task: str, thread_id: str = "default") -> Iterator[dict]:
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    initial_state = cast(AgentState, {
        "task": task,
        "messages": [HumanMessage(content=task)],
        "tool": "none",
        "output": "",
        "llm_calls": 0,
        "tool_input": [],
        "tool_output": [],
        "images": []
    })

    for chunk in agent.stream(initial_state, config, stream_mode="updates"):
        for node_name, state_update in chunk.items():
            yield {
                "node": node_name,
                "state": state_update,
            }
