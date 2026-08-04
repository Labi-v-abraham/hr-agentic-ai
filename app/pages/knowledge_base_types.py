import streamlit as st
import uuid
from app.utils.dependencies import get_authorization_service, get_backend_container

authz = get_authorization_service()
authz.require_auth()

if not authz.can_manage_users():
    st.error("You do not have permission to access this page.")
    st.stop()

st.title("📑 Knowledge Base Types")
st.write("Manage the Knowledge Bases available in the system.")

client = get_backend_container()["supabase_service"].get_admin_client()

# ==========================================
# Fetch all Knowledge Bases
# ==========================================
def fetch_kbs():
    res = client.table("knowledge_bases").select("*").order("name").execute()
    return res.data or []

# ==========================================
# Add Knowledge Base
# ==========================================
with st.expander("➕ Add Knowledge Base"):
    with st.form("add_kb_form", clear_on_submit=True):
        new_name = st.text_input("Knowledge Base Name", placeholder="e.g. Software Engineer")
        new_type = st.selectbox("Type", ["Resume Evaluation", "General HR", "Other"])
        new_desc = st.text_area("Description", placeholder="Enter a brief description...")
        new_status = st.checkbox("Active", value=True)
        
        submitted = st.form_submit_button("Save", type="primary")
        if submitted:
            if not new_name.strip():
                st.error("Name is required.")
            else:
                try:
                    client.table("knowledge_bases").insert({
                        "name": new_name.strip(),
                        "type": new_type,
                        "description": new_desc.strip(),
                        "is_active": new_status
                    }).execute()
                    st.success(f"Knowledge Base '{new_name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add Knowledge Base: {e}")

st.divider()

# ==========================================
# Edit & Delete Dialogs
# ==========================================
@st.dialog("Edit Knowledge Base")
def edit_kb_dialog(kb):
    st.write(f"Editing **{kb['name']}**")
    
    with st.form(f"edit_kb_form_{kb['id']}"):
        edit_name = st.text_input("Knowledge Base Name", value=kb.get("name", ""))
        
        kb_type = kb.get("type", "Resume Evaluation")
        type_options = ["Resume Evaluation", "General HR", "Other"]
        type_index = type_options.index(kb_type) if kb_type in type_options else 0
        
        edit_type = st.selectbox("Type", type_options, index=type_index)
        edit_desc = st.text_area("Description", value=kb.get("description", ""))
        edit_status = st.checkbox("Active", value=kb.get("is_active", True))
        
        save_btn = st.form_submit_button("Update", type="primary")
        if save_btn:
            if not edit_name.strip():
                st.error("Name is required.")
            else:
                try:
                    client.table("knowledge_bases").update({
                        "name": edit_name.strip(),
                        "type": edit_type,
                        "description": edit_desc.strip(),
                        "is_active": edit_status
                    }).eq("id", kb['id']).execute()
                    st.success("Updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")

@st.dialog("Delete Knowledge Base")
def delete_kb_dialog(kb):
    st.warning(f"Are you sure you want to delete **{kb['name']}**?")
    
    # Check for existing documents
    docs_res = client.table("documents").select("id", count="exact").eq("knowledge_base_id", kb["id"]).execute()
    count = docs_res.count if hasattr(docs_res, 'count') and docs_res.count is not None else len(docs_res.data)
    
    if count > 0:
        st.error(f"This Knowledge Base contains {count} documents. Move or delete those documents first. Do not delete.")
        if st.button("Cancel"):
            st.rerun()
    else:
        st.write("No documents found. Safe to delete.")
        if st.button("Confirm Delete", type="primary"):
            try:
                client.table("knowledge_bases").delete().eq("id", kb["id"]).execute()
                st.success("Deleted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete: {e}")

# ==========================================
# Display Knowledge Bases List
# ==========================================
kbs = fetch_kbs()

if not kbs:
    st.info("No Knowledge Bases found. Add one above.")
else:
    # Table Header
    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 2])
    with col1: st.markdown("**Knowledge Base Name**")
    with col2: st.markdown("**Type**")
    with col3: st.markdown("**Description**")
    with col4: st.markdown("**Status**")
    with col5: st.markdown("**Actions**")
    st.divider()

    # Rows
    for kb in kbs:
        c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 1, 2], vertical_alignment="center")
        
        with c1:
            st.write(kb.get("name", "N/A"))
        with c2:
            st.write(kb.get("type", "N/A"))
        with c3:
            desc = kb.get("description", "")
            st.caption(desc if len(desc) < 50 else desc[:47] + "...")
        with c4:
            if kb.get("is_active", True):
                st.write("✅ Active")
            else:
                st.write("❌ Inactive")
        with c5:
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Edit", key=f"edit_{kb['id']}"):
                    edit_kb_dialog(kb)
            with action_col2:
                if st.button("Delete", key=f"delete_{kb['id']}"):
                    delete_kb_dialog(kb)
        
        st.divider()
