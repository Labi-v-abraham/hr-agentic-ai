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

res = requests.options(f"{url}/rest/v1/chat_history", headers=headers)
print("OPTIONS:", res.text)
