import os
from google import genai
from google.genai import types
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
generation_config = types.GenerateContentConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

# 安全设置，全部设置为 BLOCK_NONE（注意风险）
safety_settings = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

# --- 系统指令 (写死在代码中) ---
SYSTEM_INSTRUCTIONS = """
你是一个有用的助手。
请记住，你是一个 AI 模型，因此没有感情或信仰。
你的目标是尽可能地回答用户的问题。
所有回复都以中文回复。
请不要分开输出思考过程和内容，而是将两者自然地融合在一起。
"""
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
    history_messages.append(
        types.Part.from_text(SYSTEM_INSTRUCTIONS, role="system")
    )
    for msg in st.session_state.messages:
      if msg and msg.get("role") and msg.get("content"):
            if msg["role"] == "user":
               history_messages.append(types.Part.from_text(msg["content"], role="user"))
            elif msg["role"] == "assistant" and msg["content"] is not None:
               history_messages.append(types.Part.from_text(msg["content"], role="model"))
          
    if prompt:
       history_messages.append(types.Part.from_text(prompt, role="user"))

    try:
      # 创建聊天会话
      response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=history_messages,
            config=generation_config,
            tools = 'code_execution',
            safety_settings=safety_settings
        )

      full_response = ""
      for chunk in response.text:
            full_response += chunk
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
