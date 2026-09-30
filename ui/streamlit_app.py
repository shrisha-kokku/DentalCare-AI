import base64
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
LOGO_PATH = Path(__file__).parent / "static" / "logo.svg"
BOT_AVATAR = "🦷"
USER_AVATAR = "🧑"

EXAMPLES = [
    ("🔍 Find orthodontist slots", "Show available slots for an orthodontist"),
    ("📅 Book an appointment", "I want to book an appointment"),
    ("🔁 Reschedule", "I want to reschedule my appointment"),
    ("❌ Cancel", "I want to cancel my appointment"),
]

st.set_page_config(page_title="DentalCare AI", page_icon="🦷", layout="centered")


def logo_data_uri() -> str | None:
    if not LOGO_PATH.exists():
        return None
    return "data:image/svg+xml;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()


logo_uri = logo_data_uri()

st.markdown(
    """
    <style>
    .hero {display:flex; align-items:center; gap:16px; margin-bottom:4px;}
    .hero img {width:64px; height:64px;}
    .hero h1 {
        margin:0; padding:0; font-size:2.4rem;
        background:linear-gradient(90deg,#5eead4,#0ea5e9);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .tagline {color:#9ca3af; margin-bottom:1.5rem;}
    footer {visibility:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

logo_html = f'<img src="{logo_uri}" alt="logo">' if logo_uri else "<span style='font-size:3rem'>🦷</span>"
st.markdown(
    f'<div class="hero">{logo_html}<h1>DentalCare AI</h1></div>'
    '<div class="tagline">Book, reschedule or cancel dental appointments just by chatting.</div>',
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    if logo_uri:
        st.markdown(f'<img src="{logo_uri}" width="56">', unsafe_allow_html=True)
    st.subheader("Try asking")
    for label, text in EXAMPLES:
        if st.button(label, use_container_width=True):
            st.session_state.pending = text
    st.divider()
    st.caption("Dates use MM/DD/YYYY and 24-hour time, e.g. 5/10/2026 14:00")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

if not st.session_state.history:
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.write(
            "Hi! I'm your dental appointment assistant. I can check doctor availability, "
            "book, reschedule or cancel appointments. How can I help?"
        )

for msg in st.session_state.history:
    avatar = BOT_AVATAR if msg["role"] == "assistant" else USER_AVATAR
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

pending = st.session_state.pop("pending", None)
user_input = st.chat_input("Type your message...") or pending

if user_input:
    st.chat_message("user", avatar=USER_AVATAR).write(user_input)
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"message": user_input, "history": st.session_state.history},
                    timeout=90,
                )
                response.raise_for_status()
                data = response.json()
                st.session_state.history = data["history"]
                st.write(data["reply"])
            except requests.RequestException as exc:
                st.error(f"Could not reach the assistant. Please try again.\n\n{exc}")