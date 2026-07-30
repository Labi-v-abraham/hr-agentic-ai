import streamlit as st

st.title("⚙️ Settings")

st.write("Knowledge Base")

if st.button("Rebuild Vector Store"):
    st.success("Vector Store Rebuilt")

st.divider()

if st.button("Clear Chat History"):
    st.success("Chat Cleared")