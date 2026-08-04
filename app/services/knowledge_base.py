import os
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import uuid

from app.database.supabase_service import SupabaseService
from app.agents.rag.loader import load_documents
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    Handles permanent knowledge base storage.
    Responsibilities:
    - Supabase Storage for files.
    - Postgres 'documents' table for metadata.
    - ChromaDB for permanent vector embeddings.
    """
    BUCKET_NAME = "hr_documents"

    def __init__(self, supabase_service, embeddings):
        self.supabase = supabase_service.get_admin_client()
        self.embeddings = embeddings
        self.vectorstore_path = Path.cwd() / "vectorstore"
        self.bucket_initialized = False

    def _ensure_bucket_exists(self):
        if self.bucket_initialized:
            return
            
        try:
            buckets = self.supabase.storage.list_buckets()
            if not any(b.name == self.BUCKET_NAME for b in buckets):
                self.supabase.storage.create_bucket(self.BUCKET_NAME, options={"public": False})
                logger.info(f"Created Supabase storage bucket: {self.BUCKET_NAME}")
            self.bucket_initialized = True
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise Exception(f"Storage initialization failed: {e}")

    def get_vectorstore(self) -> Chroma:
        """Returns the persistent ChromaDB instance."""
        return Chroma(
            persist_directory=str(self.vectorstore_path),
            embedding_function=self.embeddings,
        )

    def get_knowledge_base_id(self, kb_name: str) -> str:
        print("=" * 60)
        print("KB NAME RECEIVED:", repr(kb_name))
        print("=" * 60)

        result = (
            self.supabase
            .table("knowledge_bases")
            .select("id, name")
            .eq("name", kb_name.strip())
            .execute()
        )

        print("SUPABASE RESULT:", result.data)

        if not result.data:
            raise Exception(f"Knowledge Base '{kb_name}' not found")

        return result.data[0]["id"]


    def upload_document(self, file_bytes: bytes, filename: str, uploader_id: str, mime_type: str, kb_name: str = "General HR") -> Tuple[bool, str]:
        """Full pipeline: Upload to storage -> Save Metadata -> Embed into Chroma"""
        try:
            self._ensure_bucket_exists()
            
            # 1. Insert Metadata (Status: UPROCESSING)
            storage_path = f"{uuid.uuid4()}_{filename}"
            
            kb_id = self.get_knowledge_base_id(kb_name)

            db_res = self.supabase.table("documents").insert({
                "name": filename,
                "file_path": filename,
                "mime_type": mime_type,
                "file_size": len(file_bytes),
                "storage_bucket": self.BUCKET_NAME,
                "storage_path": storage_path,
                "uploaded_by": uploader_id,
                "status": "PROCESSING",
                "knowledge_base_id": kb_id
            }).execute()
            
            if not db_res.data:
                return False, "Failed to insert document metadata."
                
            doc_id = db_res.data[0]["id"]

            # 2. Upload to Supabase Storage
            try:
                self.supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": mime_type}
                )
            except Exception as e:
                # Rollback DB if storage fails
                self.supabase.table("documents").delete().eq("id", doc_id).execute()
                logger.error(f"Storage upload failed: {e}")
                return False, f"Storage upload failed: {str(e)}"

            # 3. Extract and Embed
            success, msg = self._extract_and_embed(doc_id, file_bytes, filename, kb_name, kb_id)
            
            if success:
                self.supabase.table("documents").update({"status": "PROCESSED"}).eq("id", doc_id).execute()
                return True, "Document uploaded and indexed successfully."
            else:
                self.supabase.table("documents").update({"status": "FAILED"}).eq("id", doc_id).execute()
                return False, f"Indexing failed: {msg}"

        except Exception as e:
            logger.error(f"Unexpected error in upload_document: {e}")
            return False, str(e)

    def _extract_and_embed(self, document_id: str, file_bytes: bytes, filename: str, kb_name: str, kb_id: str) -> Tuple[bool, str]:
        """Saves bytes to tmp file, loads with PyPDFLoader, and adds to ChromaDB with deterministic IDs."""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = tmp_file.name

            # 1. Extract and chunk
            chunks = load_documents(tmp_path)
            if not chunks:
                return False, "No text could be extracted from the document."

            # 2. Assign metadata and deterministic IDs to avoid duplicates
            vectorstore = self.get_vectorstore()
            
            ids = []
            for i, chunk in enumerate(chunks):
                chunk.metadata["knowledge_base_id"] = kb_id
                chunk.metadata["knowledge_base_name"] = kb_name
                chunk.metadata["document_id"] = document_id
                chunk.metadata["filename"] = filename
                
                print("\nMetadata before insertion:")
                print(chunk.metadata)
                
                ids.append(f"{document_id}_chunk_{i}")

            # 3. Upsert to ChromaDB (Adds if missing, updates if existing)
            vectorstore.add_documents(documents=chunks, ids=ids)
            
            print("\n===============================")
            print("Total vector count:", vectorstore._collection.count())
            stored_metadatas = vectorstore._collection.get(include=["metadatas"])["metadatas"]
            print("First 5 stored metadatas:", stored_metadatas[:5])
            print("===============================\n")
            
            
            return True, "Success"

        except Exception as e:
            logger.error(f"Error extracting/embedding document {document_id}: {e}")
            return False, str(e)
            
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def delete_document(self, document_id: str) -> Tuple[bool, str]:
        """Soft deletes metadata, removes file from storage, and drops embeddings."""
        try:
            doc_res = self.supabase.table("documents").select("*").eq("id", document_id).execute()
            if not doc_res.data:
                return False, "Document not found."
            
            doc = doc_res.data[0]

            # 1. Soft delete in Postgres
            self.supabase.table("documents").update({"is_deleted": True}).eq("id", document_id).execute()

            # 2. Attempt to remove from Storage (optional, soft delete usually keeps it, but prompt says "permanent storage" so we might keep it or delete it. Let's delete storage to save space).
            if doc.get("storage_path"):
                try:
                    self.supabase.storage.from_(self.BUCKET_NAME).remove([doc["storage_path"]])
                except Exception as e:
                    logger.warning(f"Failed to remove file from storage: {e}")

            # 3. Remove embeddings from ChromaDB
            try:
                vectorstore = self.get_vectorstore()
                # Chroma doesn't support deleting by metadata directly in some versions easily, 
                # but since our IDs are prefixed with document_id, we can fetch and delete.
                # A robust way is fetching IDs by where condition:
                items = vectorstore.get(where={"document_id": document_id})
                if items and items.get("ids"):
                    vectorstore.delete(ids=items["ids"])
            except Exception as e:
                logger.error(f"Failed to remove embeddings for {document_id}: {e}")

            return True, "Document deleted successfully."
        except Exception as e:
            logger.error(f"Error in delete_document: {e}")
            return False, str(e)

    def list_documents(self, kb_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List non-deleted documents, optionally filtered by kb_name."""
        try:
            query = self.supabase.table("documents").select("*, knowledge_bases(name)").eq("is_deleted", False).order("created_at", desc=True)
            if kb_name:
                kb_id = self.get_knowledge_base_id(kb_name)
                query = query.eq("knowledge_base_id", kb_id)
            res = query.execute()
            
            docs = []
            for d in res.data:
                kb_info = d.pop("knowledge_bases", None)
                if kb_info and isinstance(kb_info, dict):
                    d["kb_name"] = kb_info.get("name", "Unknown")
                else:
                    d["kb_name"] = "Unknown"
                docs.append(d)
            return docs
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

    def reindex_document(self, document_id: str) -> Tuple[bool, str]:
        """Re-downloads from storage and re-embeds."""
        try:
            doc_res = self.supabase.table("documents").select("*").eq("id", document_id).execute()
            if not doc_res.data:
                return False, "Document not found."
            
            doc = doc_res.data[0]
            storage_path = doc.get("storage_path")
            
            if not storage_path:
                return False, "Storage path missing. Cannot reindex."

            # Update status
            self.supabase.table("documents").update({"status": "PROCESSING"}).eq("id", document_id).execute()

            # Download bytes
            file_bytes = self.supabase.storage.from_(self.BUCKET_NAME).download(storage_path)
            
            kb = (
                    self.supabase
                    .table("knowledge_bases")
                    .select("name")
                    .eq("id", doc["knowledge_base_id"])
                    .single()
                    .execute()
                )

            kb_name = kb.data["name"]

            # Embed
            success, msg = self._extract_and_embed(
                document_id,
                file_bytes,
                doc["name"],
                kb_name,
                doc["knowledge_base_id"]
            )
            
            if success:
                self.supabase.table("documents").update({"status": "PROCESSED"}).eq("id", document_id).execute()
                return True, "Document reindexed successfully."
            else:
                self.supabase.table("documents").update({"status": "FAILED"}).eq("id", document_id).execute()
                return False, f"Reindexing failed: {msg}"
                
        except Exception as e:
            logger.error(f"Error reindexing document: {e}")
            self.supabase.table("documents").update({"status": "FAILED"}).eq("id", document_id).execute()
            return False, str(e)
