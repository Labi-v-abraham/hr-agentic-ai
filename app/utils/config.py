import os
import logging

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# Defensive import: app should still start if Groq is not installed
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    ChatGroq = None
    GROQ_AVAILABLE = False
    logger.warning("[LLM Config] langchain_groq not installed. Fallback LLM (Llama 3.3) disabled.")
    print("[LLM Config] ⚠️ langchain_groq not installed. Fallback LLM disabled.")

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    ChatOllama = None
    OLLAMA_AVAILABLE = False
    logger.warning("[LLM Config] langchain_ollama not installed. Local mode disabled.")

try:
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    HF_AVAILABLE = True
except ImportError:
    HuggingFaceEndpoint = None
    ChatHuggingFace = None
    HF_AVAILABLE = False
    logger.warning("[LLM Config] langchain_huggingface not installed. HF mode disabled.")

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

LLM_MODE = os.getenv("LLM_MODE", "cloud").lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.warning("[LLM Config] GROQ_API_KEY not found in .env. Fallback LLM (Llama 3.3) disabled.")
    print("[LLM Config] ⚠️ GROQ_API_KEY not found in .env. Fallback LLM disabled.")

import streamlit as st

@st.cache_resource
def get_llm():
    if LLM_MODE == "local":
        if OLLAMA_AVAILABLE:
            logger.info("[LLM Config] Running in LOCAL mode: Ollama llama3.2")
            print("[LLM Config] 🖥️ LOCAL mode: Ollama llama3.2 (no cloud API calls)")
            return ChatOllama(
                model="llama3.2", 
                temperature=0,
                client_kwargs={"timeout": 60.0}
            )
        else:
            logger.warning("[LLM Config] LLM_MODE is 'local' but langchain_ollama is not installed. Falling back to cloud mode.")
            print("[LLM Config] ⚠️ Local mode requested but langchain_ollama missing. Falling back to cloud mode.")
            
    elif LLM_MODE == "huggingface":
        if HF_AVAILABLE and HF_TOKEN:
            llm_endpoint = HuggingFaceEndpoint(
                repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                huggingfacehub_api_token=HF_TOKEN,
                temperature=0.01,
                max_new_tokens=1024,
            )
            chat_model = ChatHuggingFace(llm=llm_endpoint)
            logger.info("[LLM Config] Running in HUGGINGFACE mode: Mistral-7B-Instruct-v0.3")
            print("[LLM Config] 🤗 HUGGINGFACE mode: Mistral-7B-Instruct-v0.3 (free inference API)")
            return chat_model
        else:
            logger.warning("[LLM Config] LLM_MODE is 'huggingface' but HF_AVAILABLE is False or HF_TOKEN is missing. Falling back to cloud mode.")
            print("[LLM Config] ⚠️ Hugging Face mode requested but langchain_huggingface missing or HF_TOKEN missing. Falling back to cloud mode.")
            
    primary = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        timeout=15,
    )
    logger.info("[LLM Config] Primary LLM: gemini-2.5-flash")
    print("[LLM Config] Primary LLM: gemini-2.5-flash")

    if GROQ_AVAILABLE and GROQ_API_KEY:
        fallback = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            timeout=15,
        )
        logger.info("[LLM Config] Fallback LLM: Groq llama-3.3-70b-versatile")
        print("[LLM Config] Fallback LLM: Groq llama-3.3-70b-versatile ✅")
        print("[LLM Config] Fallback chain: Gemini → Llama 3.3 (Groq)")
        return primary.with_fallbacks([fallback])
    else:
        logger.warning("[LLM Config] No fallback LLM available. Running with primary only.")
        print("[LLM Config] ⚠️ No fallback LLM configured. Running primary only.")
        return primary