import asyncio
from app.database.supabase_service import SupabaseService

def test():
    supabase = SupabaseService().get_admin_client()
    res = supabase.table("documents").select("*, knowledge_bases(name)").eq("is_deleted", False).execute()
    print("Documents:", res.data)
    
    kbs = supabase.table("knowledge_bases").select("name").execute()
    print("KBs:", kbs.data)

test()
