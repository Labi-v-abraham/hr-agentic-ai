import chromadb
from pathlib import Path

from langchain_chroma import Chroma
from rag.retriever import get_embeddings
from rag.loader import load_documents


def build_vectorstore(pdf_path: str):
    vectorstore_path = Path.cwd() / "vectorstore"

    print("Current working directory:", Path.cwd())
    print("Vectorstore path:", vectorstore_path)

    docs = load_documents(pdf_path)

    client = chromadb.PersistentClient(path=str(vectorstore_path))
    try:
        client.delete_collection("langchain")
    except Exception:
        pass

    Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        client=client,
        persist_directory=str(vectorstore_path),
    )

    print("Knowledge Base Created Successfully")