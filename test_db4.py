import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
payload = {
    "user_id": "9a3e9f68-9812-491b-b7ea-4facbddc137c",
    "question": "test",
    "response": "test",
    "agent_used": "recruitment",
    "llm_used": "gemini"
}
res = requests.post(f"{url}/rest/v1/chat_history", headers=headers, json=payload)
print("Response with recruitment:", res.status_code, res.text)
