import streamlit as st
from datetime import datetime
import time
import sys
import os
import asyncio
import nest_asyncio
import re
import html

# Fix event loop reuse issue
nest_asyncio.apply()

# Add root path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import process_query  # ✅ Async backend router

# ------------------- Page Config -------------------
st.set_page_config(page_title="Doctor Assistant Chatbot", layout="wide")

# ------------------- Custom Styles -------------------
st.markdown("""
    <style>
        .chat-container {
            max-height: 70vh;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .message {
            padding: 1rem;
            border-radius: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            max-width: 85%;
            font-size: 0.95rem;
            color:black;
            font-family: 'Segoe UI', sans-serif;
        }
        .user {
            background-color: #d2f8d2;
            align-self: flex-end;
            text-align: right;
        }
        .bot {
            background-color: #fff;
            align-self: flex-start;
            text-align: left;
        }
        .timestamp {
            font-size: 0.7rem;
            color: #999;
            margin-top: 4px;
        }
        .typing {
            width: 60px;
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
        }
        .typing span {
            height: 10px;
            width: 10px;
            background: #bbb;
            border-radius: 50%;
            display: inline-block;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes bounce {
            0%, 80%, 100% {
                transform: scale(0);
            } 40% {
                transform: scale(1);
            }
        }
    </style>
""", unsafe_allow_html=True)

# ------------------- Sidebar -------------------
with st.sidebar:
    st.image("https://img.icons8.com/dusk/64/medical-doctor.png", width=80)
    st.title("Doctor Chatbot")
    st.caption("Smart assistant for healthcare interactions.")
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ------------------- Session Init -------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------- Display Chat -------------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"""
            <div class='message {msg["role"]}'>
                {msg["content"]}
                <div class='timestamp'>{msg["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------- Format Response -------------------
def format_response(response: str) -> str:
    def format_section(title, content_dict):
        if not content_dict:
            return f"<h4>{html.escape(title)}</h4><p>No data available.</p>"
        return f"<h4>{html.escape(title)}</h4><ul>" + ''.join(
            [f"<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>" for k, v in content_dict.items()]
        ) + "</ul>"

    # Handle both structured and unstructured inputs
    sections = re.split(r"###?\s*|\n(?=[A-Z])", response)
    output = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Detect title and content
        lines = section.split("\n")
        first_line = lines[0]
        content = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # Merge title and content if necessary
        if '-' in first_line and '**' in first_line:
            content = first_line
            title = "Information"
        else:
            title = first_line

        # Extract key-value pairs from content
        pairs = {}
        kv_matches = re.findall(r"\*\*([^\n*]+?)\*\*[:\-\s]*([\S \t]+)", content)
        if not kv_matches:
            kv_matches = re.findall(r"-\s*\*\*([^\n*]+?)\n?\*\*[:\-\s]*([\S \t]+)", content)

        for k, v in kv_matches:
            pairs[k.strip()] = v.strip()

        if pairs:
            output += format_section(title, pairs)
        else:
            output += f"<h4>{html.escape(title)}</h4><p>{html.escape(content.strip())}</p>"

    return output or "<p>No structured information found.</p>"

# ------------------- Main Chat Logic -------------------
user_input = st.chat_input("Ask me something...")

if user_input:
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })

    with st.chat_message("user"):
        st.markdown(f"""
            <div class='message user'>
                {user_input}
                <div class='timestamp'>{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)

    # Bot typing indicator
    with st.chat_message("bot"):
        typing = st.empty()
        typing.markdown('<div class="typing"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
        bot_placeholder = st.empty()

        # Await backend response
        bot_response = asyncio.get_event_loop().run_until_complete(process_query(user_input))
        formatted = format_response(bot_response)

        # Show formatted response
        typing.empty()
        bot_placeholder.markdown(f"""
            <div class='message bot'>
                {formatted}
                <div class='timestamp'>{datetime.now().strftime("%H:%M")}</div>
            </div>
        """, unsafe_allow_html=True)

    # Save bot message
    st.session_state.messages.append({
        "role": "bot",
        "content": formatted,
        "timestamp": datetime.now().strftime("%H:%M")
    })