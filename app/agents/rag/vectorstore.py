from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.agents.rag.loader import load_documents


import streamlit as st

@st.cache_resource
def get_google_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2"
    )

def build_vectorstore(pdf_path: str, collection_name: str):

    docs = load_documents(pdf_path)

    Chroma.from_documents(
        documents=docs,
        embedding=get_google_embeddings(),
        collection_name=collection_name,
        persist_directory="vectorstore"
    )

    print("Vector Store Created")