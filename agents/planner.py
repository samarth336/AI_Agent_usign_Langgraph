import os
import json
import re
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from typing import Literal, Any, cast
from src.LLM.llmService import PlannerLLMServiceHF

from agents.state import AgentState
from agents.prompts import planner_prompt

from langchain_groq import ChatGroq

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


llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))


def _looks_like_browser_request(text: str) -> bool:
    lowered = text.lower()
    return any(
        keyword in lowered
        for keyword in [
            "http://",
            "https://",
            "github.com/",
            "open ",
            "navigate",
            "go to",
            "repo",
            "repository",
            "profile",
        ]
    )


def _looks_like_filesystem_request(text: str) -> bool:
    lowered = text.lower()
    has_windows_path = bool(re.search(r"[a-zA-Z]:\\", text))
    has_unix_path = bool(re.search(r"/[^\s]+", text))
    asks_to_read = any(
        keyword in lowered
        for keyword in ["read this file", "explain it", "explain this file", "read file", "open this file", "what inside it"]
    )
    return (has_windows_path or has_unix_path) and asks_to_read


def _build_browser_tool_input(text: str) -> str:
    return text.strip()


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)

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

    latest_question = state["task"]

    if _looks_like_filesystem_request(latest_question):
        state["tool"] = "filesystem"
        state["tool_input"] = [latest_question]
        state["output"] = ""
        print(f"Planner decision: tool=filesystem, tool_input={state['tool_input'][-1]}, answer=None")
        return state

    if _looks_like_browser_request(latest_question):
        state["tool"] = "browser"
        state["tool_input"] = [
            _build_browser_tool_input(latest_question)
        ]
        state["output"] = ""
        print(f"Planner decision: tool=browser, tool_input={state['tool_input'][-1]}, answer=None")
        return state

    # Build conversation history role-aware
    prompt=planner_prompt(state)
    response = llm.invoke(str(prompt))
    result = _content_to_text(getattr(response, "content", response))
    
    # Parse the result to extract tool, answer, and tool_input
    parsed = {}
    if result:
        try:
            data = json.loads(result)
            if isinstance(data, dict):
                parsed = {str(key).strip().lower(): value for key, value in data.items()}
        except json.JSONDecodeError:
            lines = result.split('\n')
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

    if state["tool"] == "none" and not state.get("output"):
        fallback_answer = result.strip()
        if fallback_answer:
            state["output"] = fallback_answer
    
    # Handle tool_input - only set if tool is not none
    tool_input = parsed.get("tool_input")
    if tool_input and state["tool"] != "none":
        # Append to tool_input instead of overwriting
        if "tool_input" not in state or not state["tool_input"]:
            state["tool_input"] = []
        state["tool_input"].append(tool_input)
    
    print(f"Planner decision: tool={state['tool']}, tool_input={tool_input}, answer={answer}")
    
    return state
