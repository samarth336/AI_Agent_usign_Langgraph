import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Literal, Any, cast

from agents.state import AgentState


# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env file")


# -------------------------
# Initialize Gemini model
# -------------------------
model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    temperature=0
)


# -------------------------
# Structured output schema
# -------------------------
class PlannerDecision(BaseModel):
    tool: Literal["search", "calculator", "none"]
    answer: str | None
    tool_input: str | None


# Bind structured output
planner_model = model.with_structured_output(PlannerDecision)


# -------------------------
# Prompt (MEMORY AWARE)
# -------------------------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a planner agent.

        You are given the FULL conversation history.
        Use it to understand context and follow-up questions.

        AVAILABLE TOOLS:

        1. search
           - Use when the query needs factual, external, or real-world information.
           - Input: A search query string.

        DECISION RULES:

        - If you can answer directly from the conversation history or general knowledge:
          - tool = "none"
          - answer = final answer
          - tool_input = null

        - If a tool is required:
          - tool = "search"
          - answer = null
          - tool_input = input string for the tool

        IMPORTANT:
        - If the user asks something already mentioned earlier, you MUST use that information.
        - Follow the schema strictly.
        """
    ),
    (
        "human",
        """
        Conversation history:
        {conversation}

        Current user question:
        {latest_question}
        """
    )
])


# -------------------------
# Planner node (WITH MEMORY)
# -------------------------
def planner(state: AgentState) -> AgentState:
    """
    Planner that uses short-term conversational memory.
    """

    # Build conversation history (role-aware)
    conversation = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in state["messages"]
    )
    
    print("Conversation History (planner):\n", conversation)
    
    latest_question = state["messages"][-1]["content"]

    result = planner_model.invoke(
        prompt.format_messages(
            conversation=conversation,
            latest_question=latest_question
        )
    )

    # Normalize result to PlannerDecision regardless of whether the model returns a dict or a pydantic BaseModel
    if isinstance(result, PlannerDecision):
        decision = result
    elif isinstance(result, BaseModel):
        decision = PlannerDecision.parse_obj(result.dict())
    elif isinstance(result, dict):
        decision = PlannerDecision.parse_obj(result)
    else:
        raise RuntimeError(f"Unexpected planner model output type: {type(result)!r}")
    
    assistant_reply = {"role": "assistant", "content": decision.answer or "Using tool: " + decision.tool}
    state["messages"].append(cast(Any, assistant_reply))
    
    state["tool"] = decision.tool
    state["tool_input"] = [decision.tool_input] if decision.tool_input else []
    state["output"] = decision.answer or ""
    state["llm_calls"] = state.get("llm_calls", 0) + 1

    return state
