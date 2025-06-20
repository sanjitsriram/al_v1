"""
Builds a context-rich prompt using RAG and sends it to Azure OpenAI GPT-4.
"""

import json
import logging
from openai import AzureOpenAI
from backend.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)

# ---------------------- Logging Setup ----------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler("logs/chatbot.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ---------------------- Azure GPT-4 Client Setup ----------------------
try:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    logger.debug("[RAG] Azure OpenAI client initialized.")
except Exception as e:
    logger.exception("[RAG] ❌ Failed to initialize Azure OpenAI client.")
    client = None

# ---------------------- CONTEXT BUILDER ----------------------
def build_context(data):
    """
    Converts dictionary or list data (from MongoDB) into a human-readable context string.
    """
    context = ""

    if not data:
        logger.debug("[RAG] Empty context data.")
        return "No relevant data was found in the system."

    try:
        if isinstance(data, list):
            for item in data:
                context += json.dumps(item, indent=2, default=str) + "\n"

        elif isinstance(data, dict):
            for key, val in data.items():
                context += f"\n[{key.upper()}]\n"
                if isinstance(val, list):
                    for entry in val:
                        context += json.dumps(entry, indent=2, default=str) + "\n"
                else:
                    context += json.dumps(val, indent=2, default=str) + "\n"

        else:
            context = str(data)

        logger.debug(f"[RAG] Context built for GPT (truncated):\n{context[:500]}...")

    except Exception as e:
        logger.exception("[RAG] Failed to build context.")
        context = "⚠️ Context could not be formatted."

    return context

# ---------------------- RAG MAIN FUNCTION ----------------------
def generate_response(user_query, context_data):
    """
    Builds the final prompt using retrieved MongoDB data
    and sends it to GPT-4 to generate a response.
    """
    try:
        logger.debug("[RAG] Building RAG prompt...")
        context = build_context(context_data)

        full_prompt = f"""
You are a helpful AI medical assistant for doctors.
Here is some background information retrieved from internal systems:

{context}

Doctor's question:
{user_query}

Please respond professionally, clearly, and concisely based on the above context.
"""

        logger.debug(f"[RAG] Final prompt sent to GPT (truncated):\n{full_prompt[:500]}...")

        if not client:
            raise RuntimeError("Azure OpenAI client is not initialized.")

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.6,
            max_tokens=100
        )

        answer = response.choices[0].message.content
        logger.debug("[RAG] GPT-4 response received.")
        return answer

    except Exception as e:
        logger.exception("[RAG] GPT API call failed.")
        return (
            "⚠️ Sorry, I couldn’t generate a response due to a system error. "
            "Please try again or rephrase your question."
        )
