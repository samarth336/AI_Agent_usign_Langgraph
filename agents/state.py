from typing_extensions import TypedDict, Annotated
from typing import List, Literal
import operator

class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class AgentState(TypedDict):
    messages: Annotated[List[Message], operator.add]  # ✅ real conversation
    tool: str
    output: str
    llm_calls: int
    tool_input: Annotated[List[str], operator.add]
    tool_output: Annotated[List[str], operator.add]
