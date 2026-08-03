from app.database.supabase_service import SupabaseService

service = SupabaseService()
client = service.get_admin_client()
res = client.table("knowledge_bases").select("*").limit(1).execute()
print(res.data)
