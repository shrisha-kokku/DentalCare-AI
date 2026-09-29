import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DentalCare AI", layout="centered")
st.title("DentalCare AI")
st.caption("Chat with the dental appointment assistant")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Type your message...")
if user_input:
    st.chat_message("user").write(user_input)
    response = requests.post(f"{API_URL}/chat", json={"message": user_input, "history": st.session_state.history})
    data = response.json()
    st.session_state.history = data["history"]
    st.chat_message("assistant").write(data["reply"])