import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

try:
    res = supabase.table("chat_history").select("*").limit(1).execute()
    print("Chat History Schema:", res.data[0].keys() if res.data else "empty")
except Exception as e:
    print("Error:", e)
