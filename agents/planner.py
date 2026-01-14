import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from typing import Literal, Any, cast
from src.LLM.llmService import PlannerLLMServiceHF

from agents.state import AgentState
from agents.prompts import planner_prompt

# -------------------------
# Load environment variables
# -------------------------
# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise RuntimeError("GEMINI_API_KEY not found in .env file")


# -------------------------
# Initialize Gemini model
# -------------------------
# model = init_chat_model(
#     "google_genai:gemini-2.5-flash",
#     api_key=GEMINI_API_KEY,
#     temperature=0
# )

model = PlannerLLMServiceHF()

# -------------------------
# Structured output schema
# -------------------------
# class PlannerDecision(BaseModel):
#     tool: Literal["search", "calculator", "none"]
#     answer: str | None
#     tool_input: str | None


# # Bind structured output
# planner_model = model.with_structured_output(PlannerDecision)

# -------------------------
# Planner node (WITH MEMORY)
# -------------------------
def planner(state: AgentState) -> AgentState:
    """
    Planner that uses short-term conversational memory.
    """

    # Build conversation history role-aware
    prompt=planner_prompt(state)
    result = model.invoke(prompt)
    
    # Parse the result to extract tool, answer, and tool_input
    lines = result.split('\n') if result else []
    parsed = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            # Convert 'null' string to None
            if value.lower() == 'null':
                value = None
            parsed[key] = value
    
    # Set state fields
    state["tool"] = parsed.get("tool", "none")
    
    # Handle answer - only set if tool is none
    answer = parsed.get("answer")
    if answer and state["tool"] == "none":
        state["output"] = answer
    
    # Handle tool_input - only set if tool is not none
    tool_input = parsed.get("tool_input")
    if tool_input and state["tool"] != "none":
        # Append to tool_input instead of overwriting
        if "tool_input" not in state or not state["tool_input"]:
            state["tool_input"] = []
        state["tool_input"].append(tool_input)
    
    print(f"Planner decision: tool={state['tool']}, tool_input={tool_input}, answer={answer}")
    
    return state
