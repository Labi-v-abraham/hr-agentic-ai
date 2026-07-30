import streamlit as st
import os

# 1. Page Config FIRST
st.set_page_config(
    page_title="HR Agentic AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Dependency Injection
from app.utils.dependencies import get_session_manager, get_auth_service, get_authorization_service
from app.utils.config import get_llm
from app.agents.rag.retriever import get_retriever, get_embeddings
from app.agents.graph.workflow import get_graph

@st.cache_resource
def load_ai_resources():
    try:
        get_llm()
        get_embeddings()
        get_retriever()
        get_graph()
    except Exception as e:
        pass # Ignore API key errors if not set

load_ai_resources()

# 3. Setup Navigation
login_page = st.Page("app/pages/login.py", title="Log in", icon=":material/login:")
chat_page = st.Page("app/pages/chat.py", title="HR Agent", icon=":material/chat:", default=True)
admin_page = st.Page("app/pages/admin.py", title="Admin Dashboard", icon=":material/settings:")

session_manager = get_session_manager()
auth_service = get_auth_service()
authz = get_authorization_service()

current_profile = session_manager.get_current_profile()

if not current_profile:
    pg = st.navigation([login_page])
else:
    role = current_profile.role.value
    name = current_profile.name
    
    st.sidebar.markdown(f"### 👋 Welcome, {name}")
    st.sidebar.markdown(f"**Role:** `{role}`")
    
    if st.sidebar.button("Logout"):
        auth_service.logout()
        st.rerun()
        
    st.sidebar.divider()
    
    pages = [chat_page]
    
    # Hide admin dashboard if not admin
    if authz.can_manage_users():
        pages.append(admin_page)
        
    pg = st.navigation(pages)

pg.run()
