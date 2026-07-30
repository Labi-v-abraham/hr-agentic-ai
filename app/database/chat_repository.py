import logging
from typing import List, Dict
from app.database.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, supabase_service: SupabaseService):
        self.supabase_service = supabase_service
        self.client = supabase_service.get_client()

    def save_message(self, user_id: str, question: str, response: str, agent_used: str, llm_used: str):
        try:
            self.client.table("chat_history").insert({
                "user_id": user_id,
                "question": question,
                "response": response,
                "agent_used": agent_used,
                "llm_used": llm_used
            }).execute()
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")

    def get_history(self, user_id: str) -> List[Dict]:
        try:
            response = self.client.table("chat_history").select("*").eq("user_id", user_id).order("timestamp", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching chat history for user {user_id}: {e}")
            return []
