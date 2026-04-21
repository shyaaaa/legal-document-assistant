import streamlit as st   #type:ignore
from agent import ask

st.set_page_config(page_title="Legal Assistant", layout="centered")

st.title("⚖️ Legal Document Assistant")

query = st.text_input("Enter your question:")

if query:
    response = ask(query)
    st.success(response)