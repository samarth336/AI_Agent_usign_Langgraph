from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState


def extract_memory_text(state: AgentState) -> str:
    print("Chat history messages:", state["messages"])
    lines = []
    for msg in state["messages"]:
        lines.append(f"{msg.type}: {msg.content}")
    return "\n".join(lines)

def planner_prompt(state: AgentState):

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a planner agent.

            You are given the FULL conversation history.
            Use it to understand context, follow-up questions,
            and previously mentioned information.

            AVAILABLE TOOL (ONLY ONE):

            1. search
               - Use search when the user asks for:
                 - factual or real-world information
                 - definitions, explanations, lists, history
                 - current events or news
                 - web-based information
                 - images, photos, pictures, or visual content
                 - videos or multimedia content

               - search can:
                 - search the web
                 - return text results with relevant information
                 - find image URLs and links

            DECISION RULES:

            - If you can answer directly using:
              - conversation history OR
              - general knowledge
              then:
                - tool = "none"
                - answer = final answer
                - tool_input = null

            - If the answer requires external information:
                - tool = "search"
                - answer = null
                - tool_input = a concise query suitable for web search

            - If user asks for images/photos/pictures:
                - tool = "search"
                - answer = null
                - tool_input = "[subject] image" or "[subject] photo"
                Example: "moon image", "apple photo", "IPL 2024 images"

            IMPORTANT RULES:

            - If the user refers to something mentioned earlier,
              you MUST reuse that information.
            - NEVER invent search results or image URLs.
            - NEVER choose a non-existent tool.
            - search is the ONLY tool you may choose.
            - For image requests, append "image" or "photo" to the search query.
            - Follow the output schema strictly.
            OUTPUT SCHEMA:
            tool: one of ["search", "none"]
            answer: string or null 
            tool_input: string or null
            """
        ),
        (
            "human",
            """
            Conversation history:
            {memory_text}

            Current user question:
            {latest_question}
            """
        )
    ])

    memory_text = extract_memory_text(state)
    latest_question = state["task"]

    return prompt.format_messages(
        memory_text=memory_text or "None",
        latest_question=latest_question
    )


def response_generator_prompt(state: AgentState) -> str:

    has_images = bool(state.get("images"))

    system_prompt = """
    You are a conversational assistant with memory.

    You are given the full conversation history.
    If a fact (such as the user's name) appears earlier,
    you MUST reuse it to answer follow-up questions.

    Do NOT mention tools.
    Do NOT say you searched the web.
    Answer naturally and concisely.
    
    IMPORTANT - IMAGE FORMATTING:
    - If the tool output contains image URLs (from IMAGE_SEARCH results),
      format them as HTML img tags: <img src="URL" alt="description" style="max-width:100%; height:auto;">
    - Extract any URLs that look like image links (ending in .jpg, .png, .gif, .jpeg, .webp)
    - Present images in HTML format so they display properly
    - You can also use markdown format: ![alt text](image_url)
    """

    # Only mention images IF they exist
    if has_images:
        system_prompt += """
        Some tools may provide image references.
        If images are provided, use them as additional context
        when they are relevant to the task.
        """

    human_prompt = """
    Conversation history:
    {conversation}

    Current task:
    {task}

    Tool input:
    {tool_input}

    Tool output:
    {tool_output}
    """

    # Only inject image section IF images exist
    if has_images:
        human_prompt += """
        Images (from tools):
        {images}
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])

    conversation_text = extract_memory_text(state)

    format_kwargs = {
        "conversation": conversation_text or "None",
        "task": state["task"],
        "tool_input": state["tool_input"][-1] if state["tool_input"] else "N/A",
        "tool_output": state["tool_output"][-1] if state["tool_output"] else "N/A",
    }

    if has_images:
        format_kwargs["images"] = "\n".join(state["images"])

    return prompt.format(**format_kwargs)
