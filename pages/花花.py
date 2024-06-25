# First
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv  
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import streamlit as st
import pickle

# Insert your API key here
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"

if "key" not in st.session_state:
    st.session_state.key = None
    
if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()
    
genai.configure(api_key=st.session_state.key)

# Set up the model
generation_config = {
  "temperature": 1,
  "top_p": 0,
  "top_k": 0,
  "max_output_tokens": 10000,
}

safety_settings = [
   {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
   },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",generation_config=generation_config,safety_settings=safety_settings)

# LLM


def getAnswer(prompt):
    his_messages = []
    his_messages.append(
        {"role": "model", "parts": [{"text": ""}]}
    )

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    try:
        response = model.generate_content(contents=his_messages, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response  # 返回完整的回复
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""  # 在发生错误时返回空字符串


# 获取文件名，并生成对应的文件名
filename = "史莱姆娘" + ".pkl"  # 这里假设文件名就是 "史莱姆娘"
log_dir = "log"  # 日志文件夹名称

# 获取完整路径
log_file = os.path.join(log_dir, filename)

if "messages" not in st.session_state:
    # 从文件加载历史记录
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
    except FileNotFoundError:
        st.session_state.messages = []

# 显示历史记录
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # 显示对话内容
        st.markdown(message["content"], key=f"message_{i}")  # 使用 st.markdown 显示对话内容

        # 在最后两个对话中添加编辑按钮
        if i >= len(st.session_state.messages) - 2:
            if st.button("编辑", key=f"edit_{i}"):
                # 更改为可编辑文本
                st.session_state.editable_index = i  # 记录可编辑的索引
                st.session_state.editing = True  # 表示正在编辑

if st.session_state.get("editing"):
    # 如果正在编辑，显示编辑框和保存/取消按钮
    i = st.session_state.editable_index
    message = st.session_state.messages[i]

    with st.chat_message(message["role"]):
        # 显示可编辑的对话内容
        new_content = st.text_area(
            f"{message['role']}:", message["content"], key=f"message_edit_{i}"
        )

        col1, col2 = st.columns(2)  # 创建两列布局
        with col1:
            if st.button("保存", key=f"save_{i}"):
                st.session_state.messages[i]["content"] = new_content
                # 保存更改到文件
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.success(f"已保存更改！")
                st.session_state.editing = False  # 结束编辑状态
        with col2:
            if st.button("取消", key=f"cancel_{i}"):
                st.session_state.editing = False  # 结束编辑状态

if prompt := st.chat_input("Enter your message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt):  # 正确调用 getAnswer
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 保存历史记录到文件
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)

    # 重新运行页面，使 CSS 样式生效
    st.experimental_rerun() 

# 使用 st.sidebar 放置按钮
st.sidebar.title("操作")
if len(st.session_state.messages) > 0:
    st.sidebar.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))
st.sidebar.button("读取历史记录", on_click=lambda: load_history(log_file))
st.sidebar.button("清除历史记录", on_click=lambda: clear_history(log_file))

def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            messages = pickle.load(f)
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")

def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)  # 删除文件
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")
