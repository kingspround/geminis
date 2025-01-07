import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv


# --- API 密钥设置 ---
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("请设置有效的API密钥。")
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


# --- 初始化 session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- LLM 函数 ---
def getAnswer(prompt, system_instruction):
    history_messages = []
    if system_instruction:
        history_messages.append({"role": "user", "parts":[{"text":system_instruction}]})
    for msg in st.session_state.messages:
      if msg["role"] == "user":
        history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
      elif msg["role"] == "assistant":
         history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
    
    chat_session = model.start_chat(history=history_messages)
    try:
      response = chat_session.send_message(prompt, stream=True)
      full_response = ""
      for chunk in response:
         full_response += chunk.text
         yield full_response
      return full_response
    except Exception as e:
        import traceback
        st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n详细错误信息:\n{traceback.format_exc()}")
        return ""



# --- Streamlit 界面 ---
st.title("Gemini 1.5 Pro Chat")
system_instruction = st.text_area("System Instructions:", key="system_message", value="")

# 显示历史记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt, system_instruction):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
