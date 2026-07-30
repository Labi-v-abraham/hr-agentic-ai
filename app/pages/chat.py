import os
import tempfile
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader

# Dependency Injection
from app.utils.dependencies import (
    get_authorization_service, 
    get_session_manager, 
    get_chat_repo
)

# Agents imports
from app.agents.graph.workflow import get_graph
from app.agents.rag.build_vectorstore import build_vectorstore
from app.agents.rag.retriever import get_retriever

authz = get_authorization_service()
authz.require_auth()

session_manager = get_session_manager()
chat_repo = get_chat_repo()
profile = session_manager.get_current_profile()

st.title("🤖 HR Agentic AI - Chat")
st.caption(f"Welcome, {profile.name}! (Role: {profile.role.value})")

# ==================================================
# Session State for Chat
# ==================================================
session_key = f"messages_{profile.id}"

if session_key not in st.session_state:
    # Load history from Supabase
    db_history = chat_repo.get_history(profile.id)
    st.session_state[session_key] = []
    for msg in db_history:
        st.session_state[session_key].append({"role": "user", "content": msg.get("question")})
        st.session_state[session_key].append({"role": "assistant", "content": msg.get("response")})

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# ==================================================
# Sidebar
# ==================================================
with st.sidebar:
    st.header("📚 Knowledge Base")

    if authz.can_upload_documents():
        handbook = st.file_uploader("Upload Employee Handbook", type=["pdf"], key="handbook")
        if handbook:
            if st.button("Build Knowledge Base"):
                os.makedirs("data", exist_ok=True)
                handbook_path = os.path.join("data", handbook.name)
                with open(handbook_path, "wb") as f:
                    f.write(handbook.getbuffer())

                with st.spinner("Building Knowledge Base..."):
                    build_vectorstore(handbook_path)
                    get_retriever.clear()
                st.success("✅ Knowledge Base Built Successfully!")
    else:
        st.info("You do not have permission to upload documents.")

    st.divider()

    if st.button("🗑 Clear Chat History"):
        # Note: We aren't deleting from DB here to preserve logs, just clearing local view
        st.session_state[session_key] = []
        st.rerun()

# ==================================================
# Display Chat History
# ==================================================
for message in st.session_state[session_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==================================================
# Chat Input
# ==================================================
accept_file = authz.can_review_resumes()
prompt = st.chat_input("Ask the HR Agent...", accept_file=accept_file, file_type=["pdf"] if accept_file else None)

if prompt and getattr(prompt, 'files', None):
    uploaded_resume = prompt.files[0]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_resume.read())
        pdf_path = temp_pdf.name

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    st.session_state.resume_text = "\n".join(page.page_content for page in pages)
    st.success("✅ Resume uploaded successfully.")

query = prompt.text if prompt else None

if query:
    st.session_state[session_key].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    resume_required = any(word in query.lower() for word in ["resume", "candidate", "screen", "evaluate", "recruitment", "shortlist"])
    if resume_required:
        if not authz.can_review_resumes():
            answer = "⚠️ You do not have permission to perform resume reviews."
            with st.chat_message("assistant"):
                st.error(answer)
            st.session_state[session_key].append({"role": "assistant", "content": answer})
            st.stop()
        elif not st.session_state.resume_text:
            answer = "⚠️ Please upload a resume before requesting candidate evaluation."
            with st.chat_message("assistant"):
                st.warning(answer)
            st.session_state[session_key].append({"role": "assistant", "content": answer})
            st.stop()

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

    with st.spinner("🤖 Thinking..."):
        result = get_graph().invoke(state)

    answer = result["final_answer"]
    
    # Save to Supabase Chat History
    chat_repo.save_message(
        user_id=profile.id,
        question=query,
        response=answer,
        agent_used=result.get("intent", "general"),
        llm_used="gemini-2.5-flash"
    )

    with st.chat_message("assistant"):
        st.markdown(answer)

        if result["intent"] in ["resume", "recruitment"] and authz.can_review_resumes():
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Match Percentage", f'{result["match_percentage"]}%')
            with col2:
                st.metric("Recommendation", result["recommendation"])

            if result["recommendation"].lower() == "selected":
                st.success("✅ Candidate Shortlisted")
            else:
                st.error("❌ Candidate Rejected")

            with st.expander("📋 Candidate Analysis"):
                st.write(result["analysis"])

        if authz.can_view_logs():
            with st.expander("🔍 Agent Execution Log"):
                for step in result["execution_log"]:
                    st.success(step)

    st.session_state[session_key].append({"role": "assistant", "content": answer})
