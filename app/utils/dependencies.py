"""
Dependency Injection Container.
Implements a separated architecture for cached backend services and uncached frontend services.
"""
import streamlit as st

# Backend Services
from app.database.supabase_service import SupabaseService
from app.database.profile_repository import ProfileRepository
from app.database.chat_repository import ChatRepository
from app.services.user_service import UserService

# Frontend Services
from app.auth.session_manager import SessionManager
from app.auth.auth_service import AuthService
from app.auth.authorization import AuthorizationService

@st.cache_resource
def get_backend_container():
    """
    Returns a dictionary of singleton backend service instances.
    CACHED: Runs exactly once per server start.
    Contains: Databases, Repositories, AI Configurations.
    """
    print("DEBUG: Starting get_backend_container...")
    # 1. Base Service
    supabase_service = SupabaseService()
    print("DEBUG: SupabaseService initialized.")

    # 2. Repositories
    profile_repo = ProfileRepository(supabase_service)
    chat_repo = ChatRepository(supabase_service)
    print("DEBUG: Repositories initialized.")

    # 3. Backend Business Services
    user_service = UserService(supabase_service, profile_repo)
    print("DEBUG: UserService initialized.")
    
    # 4. AI & Knowledge Base
    print("DEBUG: Importing RAG components...")
    from app.agents.rag.retriever import get_embeddings
    from app.services.knowledge_base import KnowledgeBaseService

    print("DEBUG: Calling get_embeddings()...")
    embeddings = get_embeddings()
    print("DEBUG: Embeddings initialized.")

    print("DEBUG: Initializing KnowledgeBaseService...")
    knowledge_base = KnowledgeBaseService(supabase_service, embeddings)
    print("DEBUG: KnowledgeBaseService initialized.")
    print("DEBUG: get_backend_container finished successfully.")
    return {
        "supabase_service": supabase_service,
        "profile_repo": profile_repo,
        "chat_repo": chat_repo,
        "user_service": user_service,
        "knowledge_base": knowledge_base
    }


def get_frontend_factory():
    """
    Returns a dictionary of frontend service instances.
    UNCACHED: Runs on every UI script reload.
    Contains: SessionManager, Auth Middlewares.
    """
    backend = get_backend_container()
    
    # Core Auth & Session (No cookies)
    session_manager = SessionManager(
        profile_repository=backend["profile_repo"], 
        supabase_service=backend["supabase_service"]
    )
    
    auth_service = AuthService(backend["supabase_service"], session_manager)
    authorization_service = AuthorizationService(session_manager)

    return {
        "session_manager": session_manager,
        "auth_service": auth_service,
        "authorization_service": authorization_service
    }


# ==========================================
# Frontend Getters (Used directly in UI pages)
# ==========================================

def get_auth_service() -> AuthService:
    return get_frontend_factory()["auth_service"]

def get_session_manager() -> SessionManager:
    return get_frontend_factory()["session_manager"]

def get_authorization_service() -> AuthorizationService:
    return get_frontend_factory()["authorization_service"]

# ==========================================
# Backend Getters
# ==========================================

def get_user_service() -> UserService:
    return get_backend_container()["user_service"]

def get_chat_repo() -> ChatRepository:
    return get_backend_container()["chat_repo"]

def get_knowledge_base_service():
    from app.services.knowledge_base import KnowledgeBaseService
    return get_backend_container()["knowledge_base"]
