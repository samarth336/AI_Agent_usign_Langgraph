from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import List, Literal
import operator

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  #  real conversation
    task: str
    tool: str
    output: str
    llm_calls: int
    tool_input: Annotated[List[str], operator.add]
    tool_output: Annotated[List[str], operator.add]
    images: Annotated[List[str], operator.add]