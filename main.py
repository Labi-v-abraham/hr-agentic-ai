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
chat_page = st.Page("app/pages/chat.py", title="💬 Chat", default=True)
kb_page = st.Page("app/pages/knowledge_base.py", title="📚 Knowledge Base")
kb_types_page = st.Page("app/pages/knowledge_base_types.py", title="📑 Knowledge Base Types")
admin_page = st.Page("app/pages/admin.py", title="⚙️ Admin Dashboard")

session_manager = get_session_manager()
auth_service = get_auth_service()
authz = get_authorization_service()

current_profile = session_manager.get_current_profile()

if not current_profile:
    pg = st.navigation([login_page])
else:
    role = current_profile.role.value
    name = current_profile.name
    
    # Profile card
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    role_colors = {
        "HR_ADMIN": "violet",
        "HR_MANAGER": "blue",
        "EMPLOYEE": "green",
    }
    badge_color = role_colors.get(role, "gray")
    st.sidebar.markdown(
        f"""<div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem 0 0.75rem 0;">
            <div style="width:40px;height:40px;border-radius:50%;background:#6366F1;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:0.95rem;color:#fff;flex-shrink:0;">{initials}</div>
            <div style="min-width:0;">
                <div style="font-weight:600;font-size:0.95rem;color:#e8eaed;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.sidebar.badge(role, icon=":material/badge:", color=badge_color)
    
    pages = [chat_page]
    
    # Hide admin dashboard and knowledge base if not admin/allowed
    if authz.can_upload_documents():
        pages.append(kb_page)
    if authz.can_manage_users():
        pages.append(kb_types_page)
        pages.append(admin_page)
        
    pg = st.navigation(pages)

pg.run()

if current_profile:
    st.sidebar.markdown('<div class="sidebar-fixed-footer">', unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="logout_bottom", icon=":material/logout:", use_container_width=True):
        auth_service.logout()
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
