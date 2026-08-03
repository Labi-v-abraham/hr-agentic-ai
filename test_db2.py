import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Accept": "application/json"
}

# Query information_schema is not allowed via PostgREST, but we can just do a GET /rest/v1/chat_history?limit=1
res = requests.get(f"{url}/rest/v1/chat_history?limit=1", headers=headers)
print("chat_history columns:", res.json())
