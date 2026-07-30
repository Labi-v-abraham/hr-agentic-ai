import os
import tempfile

import streamlit as st
from langchain_community.document_loaders import PyPDFLoader

from graph.workflow import get_graph
from rag.build_vectorstore import build_vectorstore
from config import get_llm
from rag.retriever import get_retriever, get_embeddings


# ==================================================
# Page Configuration
# ==================================================

st.set_page_config(
    page_title="HR Agentic AI",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 HR Agentic AI")
st.caption("AI-powered HR Assistant using LangGraph")

# ==================================================
# Preload Resources
# ==================================================
get_llm()
get_embeddings()
get_retriever()
get_graph()


# ==================================================
# Session State
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""


# ==================================================
# Sidebar
# ==================================================

with st.sidebar:

    st.header("📚 Knowledge Base")

    handbook = st.file_uploader(
        "Upload Employee Handbook",
        type=["pdf"],
        key="handbook"
    )

    if handbook:

        if st.button("Build Knowledge Base"):

            os.makedirs("data", exist_ok=True)

            handbook_path = os.path.join(
                "data",
                handbook.name
            )

            with open(handbook_path, "wb") as f:
                f.write(handbook.getbuffer())

            with st.spinner("Building Knowledge Base..."):

                build_vectorstore(handbook_path)
                
                # Clear retriever cache so new handbook is loaded
                get_retriever.clear()

            st.success("✅ Knowledge Base Built Successfully!")

    st.divider()

    if st.button("🗑 Clear Chat"):

        st.session_state.messages = []

        st.rerun()


# ==================================================
# Display Chat History
# ==================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==================================================
# Chat Input
# ==================================================

prompt = st.chat_input("Ask the HR Agent...", accept_file=True, file_type=["pdf"])

if prompt and prompt.files:
    uploaded_resume = prompt.files[0]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_resume.read())
        pdf_path = temp_pdf.name

    loader = PyPDFLoader(pdf_path)

    pages = loader.load()

    st.session_state.resume_text = "\n".join(
        page.page_content
        for page in pages
    )

    st.success("✅ Resume uploaded successfully.")

query = prompt.text if prompt else None

if query:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    # ----------------------------------------------
    # Validate Resume Upload
    # ----------------------------------------------

    resume_required = any(
        word in query.lower()
        for word in [
            "resume",
            "candidate",
            "screen",
            "evaluate",
            "recruitment",
            "shortlist",
        ]
    )

    if resume_required and not st.session_state.resume_text:

        answer = "⚠️ Please upload a resume before requesting candidate evaluation."

        with st.chat_message("assistant"):
            st.warning(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.stop()

    # ----------------------------------------------
    # Build State
    # ----------------------------------------------

    state = {
        "query": query,
        "resume_text": st.session_state.resume_text,
        "intent": "",
        "next_node": "",
        "match_percentage": 0,
        "recommendation": "",
        "analysis": "",
        "email": "",
        "policy": "",
        "final_answer": "",
        "execution_log": [],
    }

    # ----------------------------------------------
    # Invoke Graph
    # ----------------------------------------------

    with st.spinner("🤖 Thinking..."):

        result = get_graph().invoke(state)

    answer = result["final_answer"]

    # ----------------------------------------------
    # Assistant Response
    # ----------------------------------------------

    with st.chat_message("assistant"):

        st.markdown(answer)

        # Recruitment Dashboard
        if result["intent"] in ["resume", "recruitment"]:

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Match Percentage",
                    f'{result["match_percentage"]}%'
                )

            with col2:
                st.metric(
                    "Recommendation",
                    result["recommendation"]
                )

            if result["recommendation"].lower() == "selected":
                st.success("✅ Candidate Shortlisted")
            else:
                st.error("❌ Candidate Rejected")

            with st.expander("📋 Candidate Analysis"):

                st.write(result["analysis"])

        # Execution Log
        with st.expander("🔍 Agent Execution Log"):

            for step in result["execution_log"]:
                st.success(step)

    # ----------------------------------------------
    # Save Assistant Message
    # ----------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )