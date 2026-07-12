import streamlit as st
import sys
from pathlib import Path
import uuid
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.agent_run import run_agent_stream

# ========================== Utilities ==========================

def new_thread_id() -> str:
    return str(uuid.uuid4())

def create_new_chat():
    tid = new_thread_id()
    st.session_state.current_thread = tid
    st.session_state.conversations[tid] = []

def load_thread(tid: str):
    st.session_state.current_thread = tid

# ========================== Session Init ==========================

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_thread" not in st.session_state:
    create_new_chat()

# ========================== Sidebar ==========================

with st.sidebar:
    st.title("🧠 Chats")

    if st.button("➕ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()
    st.subheader("My Conversations")

    if not st.session_state.conversations:
        st.caption("No conversations yet")
    else:
        for tid in reversed(list(st.session_state.conversations.keys())):
            label = tid[:8]
            if st.button(label, key=tid, use_container_width=True):
                load_thread(tid)
                st.rerun()

    st.divider()
    st.subheader("Current Chat")
    st.button(
        st.session_state.current_thread[:8],
        disabled=True,
        use_container_width=True
    )

# ========================== Main Chat ==========================

st.markdown("## 💬 Chat")

messages = st.session_state.conversations[
    st.session_state.current_thread
]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========================== Input ==========================

user_input = st.chat_input("Send a message...")

if user_input:
    # User message
    messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        answer_placeholder = st.empty()
        result = None
        progress_lines = []
        print("Query:", user_input)

        for state in run_agent_stream(
            user_input,
            thread_id=st.session_state.current_thread
        ):
            result = state.get("state", {})
            node = state.get("node", "unknown")
            tool = result.get("tool", "none")
            tool_input = result.get("tool_input", [])
            output_text = result.get("output", "")

            if node == "planner":
                progress_lines.append("- Planner: analyzing the request")
                if tool == "browser":
                    progress_lines.append(
                        f"- Planner: selected browser for {tool_input[-1] if tool_input else 'navigation'}"
                    )
                elif tool == "search":
                    progress_lines.append(
                        f"- Planner: selected search for {tool_input[-1] if tool_input else 'lookup'}"
                    )
                else:
                    progress_lines.append("- Planner: preparing final answer")

            if node == "search":
                progress_lines.append("- Search tool: running web search")

            if node == "browser":
                progress_lines.append("- Browser tool: opening and navigating the page")

            if node == "response_generator":
                progress_lines.append("- Response generator: composing the reply")

            progress_placeholder.markdown("\n".join(progress_lines))

            if output_text:
                answer_placeholder.markdown(output_text, unsafe_allow_html=True)

        response = result.get("output", "") if result else ""
        images = result.get("images", []) if result else []

        import re
        markdown_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', response)
        text_without_images = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', response)

        if text_without_images.strip():
            answer_placeholder.markdown(text_without_images.strip(), unsafe_allow_html=True)

        if images:
            for img_url in images:
                if img_url:
                    try:
                        st.image(img_url, width='stretch')
                    except Exception:
                        st.warning(f"Could not load image: {img_url}")

        if markdown_images:
            for alt_text, img_url in markdown_images:
                if img_url:
                    try:
                        st.image(img_url, caption=alt_text if alt_text else None, width='stretch')
                    except Exception:
                        st.warning(f"Could not load image: {img_url}")

    messages.append(
        {"role": "assistant", "content": response}
    )
    if images:
        for img_url in images:
            if img_url:
                messages.append(
                    {"role": "assistant", "content": f"![image]({img_url})"}
                )
