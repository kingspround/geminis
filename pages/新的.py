import os
from google.genai import genai # 修改这里
from google.genai import types  # 修改这里
import streamlit as st
from dotenv import load_dotenv
import pickle
import time


# Insert your API key here
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"

if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()

# --- 创建客户端 ---
client = genai.Client(api_key=api_key)

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
# --- 存储文件设置 ---
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)
# --- 创建 model ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
     tools=['code_execution'],
     safety_settings=safety_settings
)
# --- 系统提示词 ---
DEFAULT_SYSTEM_INSTRUCTION = "你是一个小兔子"


# --- 加载历史记录 ---
def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
            st.success(f"成功从 {filename} 加载历史记录！")
    except (FileNotFoundError, EOFError):
        st.warning(f"{filename} 不存在或为空。")
        st.session_state.messages = []

# --- 清空历史记录 ---
def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")

# --- 获取答案 ---
def getAnswer(prompt,system_instruction):

    chat_session = model.start_chat(
        history = st.session_state.messages,
        system_instruction = system_instruction
    )

    try:
        response = chat_session.send_message(prompt, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield full_response
        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        st.session_state.messages.append({"role": "model", "parts": [full_response]})
        with open(log_file, "wb") as f:
            pickle.dump(st.session_state.messages, f)
        return full_response
    except Exception as e:
        import traceback  # Import traceback
        st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n 详细错误信息:\n{traceback.format_exc()}")  # 更明确的错误信息
        return ""
# --- 初始化 Session State ---
if "messages" not in st.session_state:
    load_history(log_file)

# --- Streamlit 界面 ---
st.title("Gemini Chat App")
# --- 系统提示词设置 ---
system_instruction = st.text_area("System Instructions", DEFAULT_SYSTEM_INSTRUCTION, key = "system_instruction")

# --- 文件操作 ---
with st.sidebar.expander("文件操作"):
    st.button("读取历史记录 📖", on_click=lambda: load_history(log_file))
    if st.button("清除历史记录 🗑️"):
        clear_history(log_file)
    st.download_button(
        label="下载聊天记录 ⬇️",
        data=open(log_file, "rb").read() if os.path.exists(log_file) else b"",
        file_name=filename,
        mime="application/octet-stream",
    )
# --- 聊天输入和响应 ---
if prompt := st.chat_input("输入你的消息:"):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt, system_instruction):
           full_response += chunk
           message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
