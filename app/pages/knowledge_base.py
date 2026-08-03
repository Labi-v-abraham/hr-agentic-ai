import os
import tempfile
import streamlit as st

from app.utils.dependencies import (
    get_authorization_service, 
    get_session_manager, 
    get_knowledge_base_service
)

authz = get_authorization_service()
if not authz.can_upload_documents():
    st.error("You do not have permission to access the Knowledge Base management page.")
    st.stop()

session_manager = get_session_manager()
profile = session_manager.get_current_profile()
kb_service = get_knowledge_base_service()

st.title("📚 Knowledge Base Management")
st.markdown("Upload and manage documents for your different Knowledge Bases.")

# ==========================================
# Upload Section
# ==========================================
st.subheader("Upload Document")
with st.container(border=True):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        kb_name = st.text_input("Knowledge Base Name", value="General HR", help="Specify which knowledge base this document belongs to (e.g., Software Engineer, General HR)")
    
    with col2:
        uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])
        
    if uploaded_file and st.button("Upload & Index", type="primary"):
        with st.spinner("Processing document..."):
            file_bytes = uploaded_file.read()
            mime_type = "application/pdf"
            success, msg = kb_service.upload_document(file_bytes, uploaded_file.name, str(profile.id), mime_type, kb_name)
            
            if success:
                st.success(f"Successfully uploaded to **{kb_name}** KB!")
            else:
                st.error(f"Upload failed: {msg}")

st.divider()

# ==========================================
# Documents List
# ==========================================
st.subheader("Indexed Documents")
docs = kb_service.list_documents()

if not docs:
    st.info("No documents have been indexed yet.")
else:
    for doc in docs:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
            
            kb = doc.get('kb_name', 'General HR')
            status = doc.get('status', 'UNKNOWN')
            date_str = doc['created_at'].split('T')[0] if doc.get('created_at') else "Unknown"
            
            with c1:
                st.markdown(f"**{doc['name']}**")
                st.caption(f"{(doc['file_size']/1024):.1f} KB")
            
            with c2:
                st.markdown(f"🗂️ `{kb}`")
            
            with c3:
                st.markdown(f"Status: `{status}`")
                st.caption(f"Date: {date_str}")
            
            with c4:
                # Actions
                a1, a2, a3 = st.columns(3)
                
                with a1:
                    if st.button("👁 View", key=f"v_{doc['id']}", help="View Details"):
                        st.session_state[f"view_{doc['id']}"] = not st.session_state.get(f"view_{doc['id']}", False)
                
                with a2:
                    if st.button("✏ Edit", key=f"e_{doc['id']}", help="Edit Metadata"):
                        st.session_state[f"edit_{doc['id']}"] = not st.session_state.get(f"edit_{doc['id']}", False)
                        
                with a3:
                    if st.button("🗑 Delete", key=f"d_{doc['id']}", help="Delete Document"):
                        st.session_state[f"del_{doc['id']}"] = True

            # Inline Edit Form
            if st.session_state.get(f"edit_{doc['id']}", False):
                with st.expander("Edit Document Metadata", expanded=True):
                    new_kb = st.text_input("Knowledge Base", value=kb, key=f"nkb_{doc['id']}")
                    if st.button("Save Changes", key=f"save_{doc['id']}"):
                        try:
                            new_kb_id = kb_service.get_knowledge_base_id(new_kb)
                            from app.database.supabase_service import SupabaseService
                            SupabaseService().get_admin_client().table("documents").update({"knowledge_base_id": new_kb_id}).eq("id", doc['id']).execute()
                            st.success("Metadata updated!")
                            st.session_state[f"edit_{doc['id']}"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")

            # Inline View
            if st.session_state.get(f"view_{doc['id']}", False):
                with st.expander("Document Details", expanded=True):
                    st.json(doc)
            
            # Inline Delete Confirmation
            if st.session_state.get(f"del_{doc['id']}", False):
                with st.expander("Confirm Deletion", expanded=True):
                    st.warning("Are you sure you want to permanently delete this document?")
                    d1, d2 = st.columns(2)
                    if d1.button("Confirm Delete", type="primary", key=f"cd_{doc['id']}"):
                        with st.spinner("Deleting..."):
                            kb_service.delete_document(doc['id'])
                            st.session_state[f"del_{doc['id']}"] = False
                            st.rerun()
                    if d2.button("Cancel", key=f"cancel_{doc['id']}"):
                        st.session_state[f"del_{doc['id']}"] = False
                        st.rerun()
