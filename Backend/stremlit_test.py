"""
Streamlit UI for a local Ollama-powered chatbot.

Setup:
    pip install streamlit ollama
    ollama pull llama3.2        # or any model you have pulled
    ollama serve                # if not already running as a service

Run:
    streamlit run streamlit_chatbot.py
"""

import streamlit as st
from ollama import Client

# ---- Config ----
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
DEFAULT_SYSTEM_PROMPT = "You are a helpful, concise AI assistant."

st.set_page_config(page_title="Ollama Chatbot", page_icon="💬", layout="centered")


@st.cache_resource
def get_client(host: str) -> Client:
    return Client(host=host)


@st.cache_data(ttl=30)
def get_available_models(host: str) -> list[str]:
    try:
        client = get_client(host)
        data = client.list()
        return sorted(m["model"] for m in data.get("models", []))
    except Exception:
        return []


def init_session_state(system_prompt: str) -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]


def reset_chat(system_prompt: str) -> None:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]


# ---- Sidebar ----
with st.sidebar:
    st.title("⚙️ Settings")

    host = st.text_input("Ollama host", value=OLLAMA_HOST)
    available_models = get_available_models(host)

    if available_models:
        model_name = st.selectbox(
            "Model",
            options=available_models,
            index=available_models.index(DEFAULT_MODEL)
            if DEFAULT_MODEL in available_models
            else 0,
        )
    else:
        st.warning("Could not reach Ollama — check the host or run `ollama serve`.")
        model_name = st.text_input("Model (manual)", value=DEFAULT_MODEL)

    system_prompt = st.text_area(
        "System prompt", value=DEFAULT_SYSTEM_PROMPT, height=100
    )
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        reset_chat(system_prompt)
        st.rerun()

# ---- Main chat area ----
st.title("💬 Ollama Chatbot")

init_session_state(system_prompt)

# Keep system prompt in sync if the user edits it mid-session
if st.session_state.messages and st.session_state.messages[0]["role"] == "system":
    st.session_state.messages[0]["content"] = system_prompt

# Render existing conversation (skip the system message)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_reply = ""

        try:
            client = get_client(host)
            stream = client.chat(
                model=model_name,
                messages=st.session_state.messages,
                stream=True,
                options={"temperature": temperature},
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                full_reply += token
                placeholder.markdown(full_reply + "▌")
            placeholder.markdown(full_reply)

        except Exception as exc:
            full_reply = f"⚠️ Error contacting Ollama: {exc}"
            placeholder.markdown(full_reply)
            st.session_state.messages.pop()  # drop the failed user turn
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": full_reply})