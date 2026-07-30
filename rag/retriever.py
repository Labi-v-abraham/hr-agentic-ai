from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

import streamlit as st

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


@st.cache_resource
def get_retriever():
    vectorstore = Chroma(
        persist_directory=str(Path.cwd() / "vectorstore"),
        embedding_function=get_embeddings(),
    )

    return vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )