import streamlit as st
from app.utils.dependencies import get_auth_service

def render_login():
    st.title("🔐 HR Agentic AI")
    st.subheader("Login to your account")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@hragent.ai")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Please provide both email and password.")
            else:
                auth_service = get_auth_service()
                success, message = auth_service.login(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

render_login()
