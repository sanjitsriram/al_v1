# ----------- Imports ------------------
import streamlit as st
from datetime import datetime
import time
import sys
import os
import asyncio
import nest_asyncio  # ✅ Required to reuse Streamlit’s event loop safely

# Fix event loop reuse issue in Streamlit
nest_asyncio.apply()

# Add root project path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import process_query  # ✅ Async backend router

# ----------- Streamlit Config ---------
st.set_page_config(page_title="Doctor Assistant Chatbot", layout="wide")

# ----------- Custom CSS for Chat UI ---
st.markdown("""
    <style>
        .chat-container {
            max-height: 70vh;
            overflow-y: auto;
            padding: 1rem;
            border: 1px solid #e1e1e1;
            border-radius: 12px;
            background-color: #f9f9f9;
        }
        .message {
            margin-bottom: 1.2rem;
            padding: 0.8rem;
            border-radius: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            max-width: 85%;
            line-height: 1.5;
            color: black;
        }
        .user {
            background-color: #DCF8C6;
            align-self: flex-end;
            text-align: right;
            margin-left: auto;
        }
        .bot {
            background-color: #ffffff;
            align-self: flex-start;
            text-align: left;
            margin-right: auto;
        }
        .timestamp {
            font-size: 0.7rem;
            color: gray;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ----------- Sidebar ------------------
with st.sidebar:
    st.image("https://img.icons8.com/dusk/64/medical-doctor.png", width=80)
    st.title("Doctor Chatbot")
    st.write("Smart assistant for patients, appointments, and staff.")
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ----------- Chat History -------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------- Display Messages ---------
st.markdown("<div class='chat-container chat-scroll'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"""
            <div class='message {msg["role"]}'>
                {msg["content"]}
                <div class='timestamp'>{msg["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ----------- Input & Bot Response -----
with st.container():
    user_input = st.chat_input("Type your question here...")

if user_input:
    # Save and show user message
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": timestamp})
    with st.chat_message("user"):
        st.markdown(f"""
            <div class='message user'>
                {user_input}
                <div class='timestamp'>{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)

    # Placeholder for bot response
    with st.chat_message("bot"):
        bot_placeholder = st.empty()
        full_reply = ""

        # ✅ Await inside Streamlit’s running event loop
        bot_response = asyncio.get_event_loop().run_until_complete(process_query(user_input))

        for word in bot_response.split():
            full_reply += word + " "
            bot_placeholder.markdown(f"""
                <div class='message bot'>
                    {full_reply.strip()}
                    <div class='timestamp'>{datetime.now().strftime("%H:%M")}</div>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(0.03)

    # Save bot message
    st.session_state.messages.append({
        "role": "bot",
        "content": full_reply.strip(),
        "timestamp": datetime.now().strftime("%H:%M")
    })
