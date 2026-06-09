from __future__ import annotations

import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise Knowledge Copilot", layout="wide")
st.title("Enterprise Knowledge Copilot")

with st.sidebar:
    st.header("Knowledge Base")
    uploaded = st.file_uploader("Upload enterprise document", type=["pdf", "docx", "txt", "csv"])
    if uploaded and st.button("Index document"):
        response = requests.post(
            f"{API_BASE_URL}/ingest",
            files={"file": (uploaded.name, uploaded.getvalue())},
            data={"tenant_id": "demo", "user_id": "interviewer"},
            timeout=120,
        )
        st.session_state["last_ingest"] = response.json()
    if "last_ingest" in st.session_state:
        st.success(f"Indexed {st.session_state['last_ingest']['chunks_indexed']} chunks")

left, right = st.columns([0.64, 0.36])

with left:
    st.subheader("Chat")
    question = st.chat_input("Ask about the uploaded knowledge base")
    if question:
        st.chat_message("user").write(question)
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "question": question,
                "session_id": "demo-session",
                "tenant_id": "demo",
                "user_id": "interviewer",
            },
            timeout=120,
        )
        st.session_state["last_chat"] = response.json()
    if "last_chat" in st.session_state:
        chat = st.session_state["last_chat"]
        st.chat_message("assistant").write(chat["answer"])
        rating = st.slider("Rate this answer", 1, 5, 4)
        comment = st.text_input("Feedback comment")
        if st.button("Send feedback"):
            requests.post(
                f"{API_BASE_URL}/feedback",
                json={
                    "session_id": chat["session_id"],
                    "question": question or "",
                    "answer": chat["answer"],
                    "rating": rating,
                    "comment": comment,
                },
                timeout=30,
            )
            st.success("Feedback recorded")

with right:
    st.subheader("Citations")
    for citation in st.session_state.get("last_chat", {}).get("citations", []):
        st.metric(citation["source"], f"{citation['score']:.2f}")
        st.caption(citation["chunk_id"])
    st.subheader("Graph Context")
    for edge in st.session_state.get("last_chat", {}).get("graph_context", []):
        st.write(f"{edge['source']} -> {edge['relation']} -> {edge['target']}")

