import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import pickle
from io import StringIO

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

# 安全设置，全部设置为 BLOCK_NONE（注意风险）
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
# --- 系统指令 (写死在代码中) ---
SYSTEM_INSTRUCTIONS = """
你是一个骚货兔子娘
"""

# 创建模型实例，启用代码执行
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
    tools='code_execution'
)
# --- 文件操作函数 ---
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


def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")

# --- LLM 函数 ---
def getAnswer(prompt):
    prompt = prompt or ""

    history_messages = []
    for msg in st.session_state.messages:
        if msg and msg.get("role") and msg.get("content"):
            if msg["role"] == "user":
                history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant" and msg["content"] is not None:
                history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    if prompt:
        history_messages.append({"role": "user", "parts": [{"text": prompt}]})

    # 创建 chat_session，并将系统指令传递给它
    chat_session = model.start_chat(
        history=history_messages,
        system_instruction = SYSTEM_INSTRUCTIONS
    )

    try:
        response = chat_session.send_message(prompt, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield full_response
        return full_response
    except Exception as e:
        import traceback  # Import traceback
        st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n 详细错误信息:\n{traceback.format_exc()}")
        return ""

# --- Streamlit 界面 ---
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass
if "messages" not in st.session_state:
    load_history(log_file)

# 文件操作区
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

# 显示聊天记录
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
        st.write(message["content"])

# 聊天输入和响应
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    with open(log_file, "wb") as f:
      pickle.dump(st.session_state.messages, f)
