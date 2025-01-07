import streamlit as st
import google.generativeai as genai
import os

# --- API 密钥设置 ---
if "GEMINI_API_KEY" not in os.environ:
    st.error("请设置 GEMINI_API_KEY 环境变量。")
    st.stop()

genai.configure(api_key="AIzaSyCBjZbA78bPusYmUNvfsmHpt6rPx6Ur0QE")

# --- 模型设置 ---
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Set all safety settings to BLOCK_NONE
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# --- Streamlit UI ---
st.title("Gemini 1.5 Pro Chat")

# System Instructions Input
system_instructions = st.text_area("System Instructions (Optional):", "")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat Input
if prompt := st.chat_input("Enter your message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Start Chat Session
    history = []
    if system_instructions:
        history.append({"role": "system", "parts": [{"text": system_instructions}]})

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            history.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            history.append({"role": "model", "parts": [{"text": msg["content"]}]})

    chat_session = model.start_chat(history=history)


    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
           response = chat_session.send_message(prompt, stream=True)
           for chunk in response:
               full_response += chunk.text
               message_placeholder.markdown(full_response + "▌")
           message_placeholder.markdown(full_response)
           st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"An error occurred: {e}")


# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
