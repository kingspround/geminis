# 导入必要的库
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
from datetime import datetime  # 导入datetime模块用于生成时间戳

# 导入你的 API 密钥
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"
if "key" not in st.session_state:
    st.session_state.key = None
if not st.session_state.key:
    st.info("请添加你的 API 密钥以继续。")
    st.stop()

# 配置 API 密钥
genai.configure(api_key=st.session_state.key)

# 设置模型参数
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
# 初始化模型
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config, safety_settings=safety_settings)

# 定义获取模型回复的函数
def getAnswer(prompt):
    his_messages = []
    his_messages.append(
        {"role": "model", "parts": [{"text": ""}]}
    )
    # 获取最近 20 条聊天记录
    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    try:
        # 使用模型生成回复
        response = model.generate_content(contents=his_messages, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response  # 返回完整的回复
    except Exception as e:
        st.error(f"发生错误：{e}")
        return ""  # 在发生错误时返回空字符串

# Streamlit 界面
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Gemini 聊天")

# 用户输入框
user_input = st.text_input("在这里输入你的消息：")

# 发送按钮
if st.button("发送"):
    if user_input:
        # 将用户消息添加到聊天记录中
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "model", "content": ""})
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(user_input)
        # 显示模型回复
        with st.chat_message("model"):
            for chunk in getAnswer(user_input):
                st.markdown(chunk)

# 保存聊天记录按钮
if st.button("保存聊天记录"):
    # 获取当前的聊天记录
    chat_history = st.session_state.messages

    # 创建 logs 目录，如果不存在
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # 生成一个唯一的文件名
    filename = f"chat_log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    filepath = os.path.join(logs_dir, filename)

    # 将聊天记录保存到文件中
    with open(filepath, 'w') as f:
        for message in chat_history:
            f.write(f"{message['role']}: {message['content']}\n")

    # 显示保存成功提示
    st.success(f"聊天记录已保存到 {filepath}")
