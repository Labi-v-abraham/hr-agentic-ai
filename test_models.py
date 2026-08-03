from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print("API Key:", api_key[:10] + "..." if api_key else "Not Found")

client = genai.Client(api_key=api_key)

for model in client.models.list():
    print(model.name)