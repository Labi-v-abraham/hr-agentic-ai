from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag.loader import load_documents


import streamlit as st

@st.cache_resource
def get_google_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )

def build_vectorstore(pdf_path: str):

    docs = load_documents(pdf_path)

    Chroma.from_documents(
        documents=docs,
        embedding=get_google_embeddings(),
        persist_directory="vectorstore"
    )

    print("Vector Store Created")