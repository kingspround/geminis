import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# --- API 密钥设置 ---
load_dotenv()  # 从 .env 文件加载环境变量
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("请设置 GEMINI_API_KEY 环境变量。")
    st.stop()

genai.configure(api_key=api_key)

# --- 模型设置 ---
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

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

# --- Streamlit 界面 ---
st.title("Gemini Chat")

# 系统提示词输入框
system_instruction = st.text_area("System Instructions (Optional):", value="", key="system_instruction")

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 聊天输入和响应
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            history = []
            if system_instruction:
               history.append({"role": "system", "parts": [{"text": system_instruction}]})
            for msg in st.session_state.messages:
              if msg["role"] == "user":
                 history.append({"role":"user", "parts":[{"text": msg["content"]}]})
              elif msg["role"] == "assistant":
                history.append({"role":"model", "parts":[{"text": msg["content"]}]})
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt, stream=True)

            for chunk in response:
              full_response += chunk.text
              message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
          import traceback
          st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n 详细错误信息:\n{traceback.format_exc()}")
