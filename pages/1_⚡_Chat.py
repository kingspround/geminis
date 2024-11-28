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

if "key" not in st.session_state:
    st.session_state.key = "AIzaSyC7vfMxqZQJVNq0rUhzpOKu1m84y737Tak"
    
if not st.session_state.key:
    st.info("请输入你的 API Key 以继续。")
    st.stop()

try:
    genai.configure(api_key=st.session_state.key)
except Exception as e:
    st.error(f"API Key 配置失败: {e}")
    st.stop()

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",  # 或 "gemini-1.5-pro-latest"
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
except Exception as e:
    st.error(f"模型加载失败: {e}")
    st.stop()



# LLM 函数
def getAnswer(prompt, feedback):
    his_messages = [{"role": "model", "parts": [{"text": ""}]}] # 初始化第一个消息

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})  # 注意 parts 的格式
        elif msg.get("content"): # 检查是否存在 content key
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]}) # 注意 parts 的格式


    try:
        print(json.dumps(his_messages, indent=2)) # 调试用，打印发送给 API 的数据
        response = model.generate_content(contents=his_messages, stream=True)
        ret = ""
        for chunk in response:
            print(chunk.text)
            print("_" * 80)
            ret += chunk.text
            feedback(ret)
        return ret
    except google.api_core.exceptions.InvalidArgument as e:
        st.error(f"Gemini API 参数无效: {e}")
        st.write(f"请求 JSON: {json.dumps(his_messages, indent=2)}")  # 显示 JSON 用于调试
        return ""
    except Exception as e:
        st.error(f"发生意外错误: {e}")
        return ""



# Streamlit 应用
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def writeReply(cont, msg):
    cont.write(msg)

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty()
        re = getAnswer(prompt, lambda x: writeReply(p, x))
        st.session_state.messages.append({"role": "assistant", "content": re})
