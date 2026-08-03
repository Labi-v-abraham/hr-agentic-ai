import chromadb
from pathlib import Path

from langchain_chroma import Chroma
from app.agents.rag.retriever import get_embeddings
from app.agents.rag.loader import load_documents



def build_vectorstore(pdf_path: str, uploader_id: str = None):
    """
    Deprecated: Replaced by KnowledgeBaseService.
    This function acts as an adapter to prevent breaking existing UI code.
    """
    from pathlib import Path
    import mimetypes
    from app.utils.dependencies import get_knowledge_base_service
    
    path_obj = Path(pdf_path)
    filename = path_obj.name
    
    mime_type, _ = mimetypes.guess_type(pdf_path)
    if not mime_type:
        mime_type = "application/pdf"
        
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
        
    kb = get_knowledge_base_service()
    success, msg = kb.upload_document(file_bytes, filename, uploader_id, mime_type)
    
    if success:
        print("Knowledge Base Created Successfully")
    else:
        print(f"Failed to build Knowledge Base: {msg}")
    
    return success