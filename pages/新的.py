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
    tools=['code_execution'],
)

# --- 系统指令 ---
SYSTEM_INSTRUCTIONS = """
    [Install the Chinese Translator plugin]指令：所有对话包括think全部转化为中文。
    一旦活化class SexDescription模块和Excellent examples of scenarios模块，
    请不要输出任何思考过程，例如：think, 我认为 等等。
"""

# --- 文件操作函数 ---
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)


def load_history():
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
            st.success(f"成功从 {filename} 加载历史记录！")
    except (FileNotFoundError, EOFError):
        st.warning(f"{filename} 不存在或为空。")
        st.session_state.messages = []

def clear_history():
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")

# --- LLM 函数 ---
def getAnswer(prompt, system_instructions=None):
    
    if system_instructions is None:
       system_instructions = SYSTEM_INSTRUCTIONS
    
    history_messages = []
    history_messages.append(
    {
      "role": "model",
      "parts": [
       system_instructions
      ]
      })
    
    if "messages" in st.session_state:
      for msg in st.session_state.messages:
          if msg["role"] == "user":
            history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
          elif msg["role"] == "assistant" and msg["content"] is not None:
            history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    if prompt:
       history_messages.append({"role": "user", "parts": [{"text": prompt}]})
    
    chat_session = model.start_chat(history=history_messages)

    try:
        response = chat_session.send_message(prompt, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            full_response =  full_response.replace("think", "").replace("我认为", "").replace("思考", "").replace("我思考", "")
            yield full_response
        return full_response
    except Exception as e:
        import traceback  # Import traceback
        st.error(f"发生错误: {e}. 请检查你的API密钥和消息格式。\n 详细错误信息:\n{traceback.format_exc()}")  # 更明确的错误信息
        return ""


# --- Streamlit 界面 ---
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass

if "messages" not in st.session_state:
    load_history()

# 功能区 1: 文件操作
with st.sidebar.expander("文件操作"):

    if len(st.session_state.messages) > 0:
       st.button("重置上一个输出 ⏪",
                  on_click=lambda: st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 else None)
    
    st.button("读取历史记录 📖", on_click=load_history)
    if st.button("清除历史记录 🗑️"):
        clear_history()
    
    st.download_button(
        label="下载聊天记录 ⬇️",
        data=open(log_file, "rb").read() if os.path.exists(log_file) else b"",
        file_name=filename,
        mime="application/octet-stream",
    )
    uploaded_file = st.file_uploader("读取本地pkl文件 📁", type=["pkl"])
    if uploaded_file is not None:
      try:
          loaded_messages = pickle.load(uploaded_file)
          st.session_state.messages = loaded_messages  # 使用 = 替换现有消息
          st.success("成功读取本地pkl文件！")
          st.experimental_rerun()
      except Exception as e:
          st.error(f"读取本地pkl文件失败：{e}")

system_instructions_input = st.sidebar.text_area("System Instructions(Override):", "", key="system_instructions")

# 显示历史记录和编辑功能
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"], key=f"message_{i}")

# 聊天输入和响应
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt, system_instructions_input if system_instructions_input else None):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)
