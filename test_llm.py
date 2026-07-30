from config import llm

response = llm.invoke("Say Hello")

print(response.content)