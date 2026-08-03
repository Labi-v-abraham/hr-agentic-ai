from pathlib import Path

from app.utils.config import get_llm
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


import streamlit as st

@st.cache_resource
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2"
    )


@st.cache_resource
def get_vectorstore():
    return Chroma(
        persist_directory=str(Path.cwd() / "vectorstore"),
        embedding_function=get_embeddings(),
    )

def get_retriever(active_kbs: list[str] = None):
    vectorstore = get_vectorstore()
    
    search_kwargs = {"k": 10, "fetch_k": 30}
    if active_kbs:
        search_kwargs["filter"] = {"kb_name": {"$in": active_kbs}}

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )