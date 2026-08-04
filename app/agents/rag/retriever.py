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

def get_retriever(active_kb_ids: list[str] = None):
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    
    total = collection.count()
    print(f"\n[RETRIEVER] Collection name: {collection.name}")
    print(f"[RETRIEVER] Total documents in collection: {total}")
    
    if total > 0:
        all_result = collection.get(include=["metadatas"])
        all_meta = all_result.get("metadatas", [])
        
        has_kb = [m for m in all_meta if "knowledge_base_id" in m]
        missing_kb = [m for m in all_meta if "knowledge_base_id" not in m]
        
        print(f"[RETRIEVER] Chunks WITH knowledge_base_id: {len(has_kb)}")
        print(f"[RETRIEVER] Chunks MISSING knowledge_base_id: {len(missing_kb)}")
        
        if missing_kb:
            print("\n" + "="*60)
            print("🚨 WARNING: LEGACY CHROMA METADATA DETECTED 🚨")
            print(f"   {len(missing_kb)} chunk(s) are missing 'knowledge_base_id'.")
            for m in missing_kb:
                print(f"   - document_id={m.get('document_id', 'unknown')} filename={m.get('filename', 'unknown')} kb_name={m.get('kb_name', 'unknown')}")
            print("   → Use the Admin Dashboard to reindex these documents.")
            print("="*60 + "\n")
        
        if active_kb_ids:
            present_kb_ids = list(set(m["knowledge_base_id"] for m in has_kb))
            print(f"[RETRIEVER] Retrieval filter: knowledge_base_id IN {active_kb_ids}")
            print(f"[RETRIEVER] KB IDs present in Chroma: {present_kb_ids}")
            matched = [kb for kb in active_kb_ids if kb in present_kb_ids]
            print(f"[RETRIEVER] Filter matches {len(matched)} of {len(active_kb_ids)} requested KB(s)")
    
    search_kwargs = {"k": 10, "fetch_k": 30}
    if active_kb_ids:
        search_kwargs["filter"] = {"knowledge_base_id": {"$in": active_kb_ids}}

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )