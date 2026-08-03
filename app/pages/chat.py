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
from app.agents.rag.retriever import (
    get_retriever,
    get_vectorstore,
)
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
import uuid
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())

session_key = f"messages_{profile.id}_{st.session_state.current_session_id}"

if session_key not in st.session_state:
    # Load history from Supabase
    db_history = chat_repo.get_history(profile.id, st.session_state.current_session_id)
    st.session_state[session_key] = []
    for msg in db_history:
        st.session_state[session_key].append({"role": "user", "content": msg.get("question")})
        st.session_state[session_key].append({"role": "assistant", "content": msg.get("response")})

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "current_role" not in st.session_state:
    st.session_state.current_role = None

if "pending_resume" not in st.session_state:
    st.session_state.pending_resume = False

# ==================================================
# Sidebar: Chat History
# ==================================================
with st.sidebar:
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.rerun()
        
    st.divider()
    st.markdown("### Recent Conversations")
    
    sessions = chat_repo.get_sessions(profile.id)
    
    if sessions:
        for sess in sessions:
            sid = sess.get("session_id")
            if not sid:
                continue
            question = sess.get("question") or "Empty Chat"
            title = question[:25] + ("..." if len(question) > 25 else "")
            
            # Highlight active conversation
            btn_type = "primary" if sid == st.session_state.current_session_id else "secondary"
            if st.button(f"💬 {title}", key=f"sess_{sid}", use_container_width=True, type=btn_type):
                st.session_state.current_session_id = sid
                st.rerun()
    else:
        st.info("No previous conversations.")

    st.divider()
    if st.button("🗑 Clear Current Chat", use_container_width=True):
        st.session_state[session_key] = []
        st.rerun()

# ==================================================
# Display Chat History
# ==================================================
for message in st.session_state[session_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==================================================
# Role Badge & Pending Resume
# ==================================================
if st.session_state.current_role:
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.info(f"**Current Role:** {st.session_state.current_role}")
    with c2:
        if st.button("❌ Clear", key="clear_role_badge"):
            st.session_state.current_role = None
            st.rerun()

if st.session_state.pending_resume:
    with st.container(border=True):
        st.warning("Resume detected. Please choose the role you want to evaluate this candidate for.")
        roles = ["Software Engineer", "React Developer", "Python Developer", "QA Engineer", "DevOps Engineer"]
        selected = st.selectbox("Select Role", roles + ["Create New Role"])
        if selected == "Create New Role":
            selected = st.text_input("Enter new role name:")
        if st.button("Analyze"):
            st.session_state.current_role = selected
            st.session_state.pending_resume = False
            # Simulate a query to trigger evaluation
            query = f"Evaluate this candidate for {selected}"
            st.rerun()

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
    
    # Classify document
    from app.utils.config import get_llm
    llm = get_llm()
    class_prompt = f"Analyze the following text from an uploaded document. Classify it EXACTLY as one of the following: 'Resume', 'Job Description', 'HR Policy', 'Employee Handbook', or 'Unknown PDF'. Return ONLY the classification name.\n\nText: {st.session_state.resume_text[:2000]}"
    try:
        doc_type = llm.invoke(class_prompt).content.strip()
    except:
        doc_type = "Unknown PDF"
        
    if "Resume" in doc_type:
        if not st.session_state.current_role:
            st.session_state.pending_resume = True
            st.rerun()
        else:
            st.success(f"✅ Resume detected. Evaluating for {st.session_state.current_role}...")
            st.session_state.simulated_query = f"Evaluate this candidate for {st.session_state.current_role}"
            st.rerun()
    elif "Job Description" in doc_type:
        st.session_state[session_key].append({"role": "assistant", "content": "Job Description detected. Please specify which knowledge base it belongs to by using the `/knowledge` command."})
    elif "Employee Handbook" in doc_type or "HR Policy" in doc_type:
        st.session_state[session_key].append({"role": "assistant", "content": f"{doc_type} detected. Suggest adding to General HR knowledge base via the `/knowledge` command."})
    else:
        st.session_state[session_key].append({"role": "assistant", "content": "Unknown PDF detected. What would you like to do with it? (Consider adding it via `/knowledge`)"})
        
    st.rerun()

query = prompt.text if prompt else None

# Handle simulated query from pending resume action if available in session but missing in prompt
if not query and "simulated_query" in st.session_state:
    query = st.session_state.simulated_query
    del st.session_state.simulated_query

if query:
    if query.startswith("/"):
        cmd = query.split()[0].lower()
        if cmd == "/role":
            st.session_state["show_role_selector"] = True
            st.session_state[session_key].append({"role": "assistant", "content": "Please select a role from the UI above."})
            st.rerun()
        elif cmd == "/clear":
            st.session_state.current_role = None
            st.session_state[session_key].append({"role": "assistant", "content": "Cleared current role context."})
            st.rerun()
        elif cmd == "/knowledge":
            st.session_state["show_kb_manager"] = True
            st.session_state[session_key].append({"role": "assistant", "content": "Opened Knowledge Base Manager in sidebar/dialog."})
            st.rerun()
        elif cmd == "/collections":
            from app.utils.dependencies import get_knowledge_base_service
            docs = get_knowledge_base_service().list_documents()
            kbs = set(d.get('kb_name', 'General HR') for d in docs)
            st.session_state[session_key].append({"role": "assistant", "content": f"Available Knowledge Bases:\n- " + "\n- ".join(kbs)})
            st.rerun()
        else:
            st.session_state[session_key].append({"role": "assistant", "content": f"Unknown command: {cmd}"})
            st.rerun()

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

    active_kbs = ["General HR"]
    if st.session_state.current_role:
        active_kbs.append(st.session_state.current_role)
        
    state = {
        "query": query,
        "resume_text": st.session_state.resume_text,
        "current_role": st.session_state.current_role,
        "active_kbs": active_kbs,
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
        session_id=st.session_state.current_session_id,
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
