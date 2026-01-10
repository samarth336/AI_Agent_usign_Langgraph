from agents.state import AgentState
from src.LLM.llmService import LLMService
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, cast

llm = LLMService()

# -------------------------
# Prompt (FINAL ANSWER ONLY)
# -------------------------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a conversational assistant with memory.

        You are given the full conversation history.
        If a fact (such as the user's name) appears earlier,
        you MUST reuse it to answer follow-up questions.

        Do NOT mention tools.
        Do NOT say you searched the web.
        Answer naturally and concisely.
        """
    ),
    (
        "human",
        """
        Conversation history:
        {conversation}

        Tool input:
        {tool_input}

        Tool output:
        {tool_output}
        """
    )
])


# -------------------------
# Response generator node
# -------------------------
def response_generator(state: AgentState) -> AgentState:
    """
    Generates the final user-facing answer using conversation memory
    and tool output if available.
    """

    # Build readable conversation history
    conversation = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in state["messages"]
    )
    print("Conversation History (response_generator):\n", conversation)

    # Convert prompt → STRING (critical for OpenAI Responses API)
    final_prompt: str = prompt.format(
        conversation=conversation,
        tool_input=state["tool_input"][-1] if state["tool_input"] else "N/A",
        tool_output=state["tool_output"][-1] if state["tool_output"] else "N/A",
    )
    response_text = llm.invoke(str(final_prompt))
    assistant_reply = {"role": "assistant", "content": response_text}

    # Append assistant reply to memory (cast to Any to satisfy static type checkers)
    state["messages"].append(cast(Any, assistant_reply))
    state["output"] = response_text
    state["llm_calls"] += 1
    return state