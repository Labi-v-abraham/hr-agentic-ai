import streamlit as st
from app.utils.dependencies import get_auth_service

def render_login():
    # CSS to make the login card taller and narrower
    st.markdown("""
        <style>
            [data-testid="stForm"] {
                padding: 2.5rem 1.5rem;
                min-height: 380px;
            }
        </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1.5, 1, 1.5])
    with col:
        st.markdown("<h1 style='text-align: center;'>HRMS</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Login</h3>", unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="admin@hragent.ai")
            st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True)
            password = st.text_input("Password", type="password")
            st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
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
