from agents.state import AgentState
from src.LLM.llmService import LLMService
from agents.prompts import response_generator_prompt
from typing import Any, cast

llm = LLMService()

# -------------------------
# Response generator node
# -------------------------
def response_generator(state: AgentState) -> AgentState:
    """
    Generates the final user-facing answer using conversation memory
    and tool output if available.
    """
    final_prompt=response_generator_prompt(state)
    response_text = llm.invoke(str(final_prompt))

    state["output"] = response_text
    print(f"\nResponse Generator output: {response_text}")
    # Safely increment llm_calls
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    return state