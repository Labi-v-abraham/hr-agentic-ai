import streamlit as st
import pandas as pd
from app.utils.dependencies import get_authorization_service, get_user_service, get_session_manager

authz = get_authorization_service()
# Middlewares
authz.require_admin()

user_service = get_user_service()
session_manager = get_session_manager()
current_profile = session_manager.get_current_profile()

st.title("⚙️ Admin Dashboard")
st.write("Manage Users and System Settings")

# ==================================================
# Change Default Password Warning
# ==================================================
if current_profile and current_profile.email == "admin@hragent.ai":
    st.warning("⚠️ You are using the default admin account. Please change your password in Supabase or add a reset feature.")

st.divider()

# ==================================================
# User Management
# ==================================================
st.header("👥 User Management")

tab1, tab2 = st.tabs(["View Users", "Create User"])

with tab1:
    users = user_service.get_all_users()
    if users:
        from app.models.user import Role

        # Data table
        user_data = [{
            "Name": u.name,
            "Email": u.email,
            "Role": u.role.value,
            "Status": u.status.value,
            "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M:%S") if u.last_login else "Never",
            "Created At": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "Unknown"
        } for u in users]
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True)

        # Role change controls
        st.subheader("🔄 Change User Role")
        role_options = [r.value for r in Role]
        for u in users:
            col_name, col_role, col_btn = st.columns([3, 2, 1])
            with col_name:
                st.markdown(f"**{u.name}** ({u.email})")
            with col_role:
                new_role = st.selectbox(
                    "Role",
                    options=role_options,
                    index=role_options.index(u.role.value),
                    key=f"role_select_{u.auth_user_id}",
                    label_visibility="collapsed",
                )
            with col_btn:
                if st.button("Update", key=f"role_btn_{u.auth_user_id}"):
                    if new_role != u.role.value:
                        success = user_service.change_user_role(u.auth_user_id, new_role)
                        if success:
                            st.success(f"Role for {u.name} changed to {new_role}.")
                            st.rerun()
                        else:
                            st.error(f"Failed to update role for {u.name}.")
                    else:
                        st.info("Role is already set to the selected value.")
    else:
        st.info("No users found.")

with tab2:
    with st.form("create_user_form"):
        st.subheader("Create New User")
        st.info("Creating a user will use the Service Role Key to bypass email confirmations (if configured).")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            if not new_email or not new_password:
                st.error("Email and password are required.")
            else:
                success, msg = user_service.create_user(email=new_email, password=new_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
