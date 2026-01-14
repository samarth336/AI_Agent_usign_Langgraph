import streamlit as st
import sys
from pathlib import Path
import uuid
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.agent_run import run_agent

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
        with st.spinner("Thinking..."):
            print("Query:", user_input)
            result = run_agent(
                user_input,
                thread_id=st.session_state.current_thread
            )
            response = result["output"]
            images = result.get("images", [])
            
            # Extract image URLs from markdown format in response
            import re
            markdown_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', response)
            
            # Remove markdown image syntax from text for cleaner display
            text_without_images = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', response)
            
            # Display text response with HTML support for img tags
            st.markdown(text_without_images.strip(), unsafe_allow_html=True)
            
            # Display images from state
            if images:
                for img_url in images:
                    if img_url:
                        try:
                            st.image(img_url, width='stretch')
                        except Exception as e:
                            st.warning(f"Could not load image: {img_url}")
            
            # Display images extracted from markdown links
            if markdown_images:
                for alt_text, img_url in markdown_images:
                    if img_url:
                        try:
                            st.image(img_url, caption=alt_text if alt_text else None, width='stretch')
                        except Exception as e:
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
