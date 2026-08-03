import logging
from typing import List, Dict
from app.database.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, supabase_service: SupabaseService):
        self.supabase_service = supabase_service
        self.client = supabase_service.get_client()

    def save_message(self, user_id: str, session_id: str, question: str, response: str, agent_used: str, llm_used: str):
        try:
            self.client.table("chat_history").insert({
                "user_id": user_id,
                "session_id": session_id,
                "question": question,
                "response": response,
                "agent_used": agent_used,
                "llm_used": llm_used
            }).execute()
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")

    def get_history(self, user_id: str, session_id: str = None) -> List[Dict]:
        try:
            query = self.client.table("chat_history").select("*").eq("user_id", user_id)
            if session_id:
                query = query.eq("session_id", session_id)
            response = query.order("created_at", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching chat history for user {user_id}: {e}")
            return []

    def get_sessions(self, user_id: str) -> List[Dict]:
        """Fetch distinct sessions with their latest message created_at, or just fetch all and group by session_id"""
        try:
            # We can't do distinct natively in basic PostgREST select easily, so we fetch and deduplicate
            # Or fetch ordered by created_at desc to get latest sessions first
            response = self.client.table("chat_history").select("session_id, created_at, question").eq("user_id", user_id).order("created_at", desc=True).execute()
            sessions = []
            seen = set()
            for row in response.data:
                sid = row.get("session_id")
                if sid not in seen:
                    seen.add(sid)
                    sessions.append(row)
            return sessions
        except Exception as e:
            logger.error(f"Error fetching chat sessions for user {user_id}: {e}")
            return []
