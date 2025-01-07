import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import pickle

# Insert your API key here
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"

if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()

genai.configure(api_key=st.session_state.key)

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

# --- System Instructions ---
SYSTEM_INSTRUCTIONS = """
你是色色可爱的兔子娘
"""
# --- 文件操作函数 ---
# 获取当前文件路径
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)

def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
            st.success(f"成功从 {filename} 加载历史记录！")
    except (FileNotFoundError, EOFError):
        st.warning(f"{filename} 不存在或为空。")
        st.session_state.messages = []

def save_history(log_file):
    try:
      with open(log_file, "wb") as f:
          pickle.dump(st.session_state.messages, f)
    except Exception as e:
       st.error(f"保存历史记录失败：{e}")

# --- Streamlit 界面 ---
st.title("Gemini Chat")

# 初始化 session state
if "messages" not in st.session_state:
    load_history(log_file)


# 聊天输入和响应
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            history = [{"role": "system", "parts": [{"text": SYSTEM_INSTRUCTIONS}]}] # 将 system 指令加入到 history 的开头
            for msg in st.session_state.messages:
              if msg["role"] == "user":
                 history.append({"role":"user", "parts":[{"text": msg["content"]}]})
              elif msg["role"] == "assistant":
                history.append({"role":"model", "parts":[{"text": msg["content"]}]})
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt, stream=True) # 只发送用户消息

            for chunk in response:
              full_response += chunk.text
              message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_history(log_file)
        except Exception as e:
            import traceback
            st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n 详细错误信息:\n{traceback.format_exc()}")
