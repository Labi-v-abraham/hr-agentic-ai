import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

import streamlit as st

@st.cache_resource
def get_llm():
    primary = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )
    fallback = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )
    return primary.with_fallbacks([fallback])