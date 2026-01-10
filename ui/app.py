import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.agent_run import run_agent


st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="centered"
)

st.title("💬 Chat Interface")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "samarth"  # or uuid

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    # Store user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # ---- Bot response (placeholder) ----
    response = run_agent(
    user_input,
    thread_id=st.session_state.thread_id
)

    # Store bot message
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    # Display bot message
    with st.chat_message("assistant"):
        st.markdown(response)
