import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import random
import pickle
import re  # 导入正则表达式库

# API Key 设置
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"  # 请勿将您的API Key 泄露在公开场合
if "key" not in st.session_state:
    st.session_state.key = None
if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()
genai.configure(api_key=st.session_state.key)

# 模型设置
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
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config,
    safety_settings=safety_settings,
)
model_v = genai.GenerativeModel(model_name='gemini-pro-vision', generation_config=generation_config)  # 添加 gemini-pro-vision 模型

# LLM
def generate_token():
    """生成一个 10 位到 20 位的随机 token"""
    token_length = random.randint(10, 20)
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    token = "".join(random.choice(characters) for i in range(token_length))
    return token

def getAnswer_text(prompt, token):
    his_messages = []
    # 只保留用户输入的最后一条消息
    for msg in st.session_state.messages[-1:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})

    response = model.generate_content(contents=his_messages, stream=True)

    full_response = ""
    for chunk in response:
        full_response += chunk.text
        yield chunk.text

    # 更新最后一条回复
    if "last_response" in st.session_state and st.session_state.last_response:  # 判断列表是否为空
        st.session_state.last_response[-1] = full_response
    else:
        st.session_state.last_response = [full_response]  # 初始化

def getAnswer_image(prompt, token, image):
    his_messages = []
    # 只保留用户输入的最后一条消息
    for msg in st.session_state.messages[-1:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})

    # 使用 gemini-pro-vision 模型处理图片
    prompt_v = ""
    for msg in st.session_state.messages[-20:]:
        prompt_v += f'''{msg["role"]}:{msg["content"]}
        Use code with caution.
        '''
    response = model_v.generate_content([prompt_v, image], stream=True)  # 使用 model_v 生成内容

    full_response = ""
    for chunk in response:
        full_response += chunk.text
        yield chunk.text

    # 更新最后一条回复
    if "last_response" in st.session_state and st.session_state.last_response:  # 判断列表是否为空
        st.session_state.last_response[-1] = full_response
    else:
        st.session_state.last_response = [full_response]  # 初始化

# 初始化聊天记录列表
if "messages" not in st.session_state:
    st.session_state.messages = []

# 初始化 last_response 列表
if "last_response" not in st.session_state:
    st.session_state.last_response = []

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入并处理
if prompt := st.chat_input("Enter your message:"):
    if "use_token" in st.session_state and st.session_state.use_token:
        token = generate_token()
        st.session_state.messages.append({"role": "user", "content": f"{prompt} (token: {token})"})
        with st.chat_message("user"):
            st.markdown(f"{prompt} (token: {token})")
    else:
        st.session_state.messages.append({"role": "user", "content": f"{prompt}"})
        with st.chat_message("user"):
            st.markdown(f"{prompt}")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        # 动态判断使用哪个模型
        if "img" in st.session_state and st.session_state.img is not None:  # 检测图片输入栏是否不为空
            # 使用 gemini-pro-vision 处理图片
            model = model_v
        else:
            # 使用 gemini-1.5-pro-latest 处理文本
            model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest', generation_config=generation_config, safety_settings=safety_settings)

        if "use_token" in st.session_state and st.session_state.use_token:
            token = generate_token()
            if "img" in st.session_state and st.session_state.img is not None:  # 检测图片输入栏是否不为空
                for chunk in getAnswer_image(prompt, token, st.session_state.img):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                # 使用正则表达式过滤 "Use code with caution."
                full_response = re.sub(r"Use code with caution\.", "", full_response)
                # 只输出内容，不输出 "assistant:"
                if st.session_state.messages[-1]["role"] == "assistant":  # 检查上一个角色是否为 "assistant"
                    message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                for chunk in getAnswer_text(prompt, token):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            if "img" in st.session_state and st.session_state.img is not None:  # 检测图片输入栏是否不为空
                for chunk in getAnswer_image(prompt, "", st.session_state.img):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                # 使用正则表达式过滤 "Use code with caution."
                full_response = re.sub(r"Use code with caution\.", "", full_response)
                # 只输出内容，不输出 "assistant:"
                if st.session_state.messages[-1]["role"] == "assistant":  # 检查上一个角色是否为 "assistant"
                    message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                for chunk in getAnswer_text(prompt, ""):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 自动保存到本地文件 ---
# 获取文件名，并生成对应的文件名
filename = os.path.splitext(os.path.basename(__file__))[0] + ".pkl"  # 使用 .pkl 扩展名
# 获取完整路径
log_file = os.path.join(os.path.dirname(__file__), filename)  # 使用 os.path.dirname 获取当前目录
# 检查文件是否存在，如果不存在就创建空文件
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass  # 创建空文件
# 保存历史记录到文件
with open(log_file, "wb") as f:
    pickle.dump(st.session_state.messages, f)

# --- 侧边栏功能 ---
st.sidebar.title("操作")

# 上传图片
uploaded_file = st.sidebar.file_uploader("上传图片", type=['png', 'jpg', 'jpeg', 'gif'])
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    bytes_io = BytesIO(bytes_data)
    st.session_state.img = Image.open(bytes_io)  # 存储图片到 st.session_state.img
    st.sidebar.image(bytes_io, width=150)

# 清除图片
if st.session_state.img is not None:
    if st.sidebar.button("清除图片"):
        st.session_state.img = None

# 读取历史记录
if st.sidebar.button("读取历史记录"):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"聊天记录已加载")
    except FileNotFoundError:
        st.warning("聊天记录文件不存在。")
    except EOFError:
        st.warning(f"读取聊天记录失败：文件可能损坏。")

# 清除历史记录
if st.sidebar.button("清除历史记录"):
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除聊天记录！")
    except FileNotFoundError:
        st.warning("聊天记录文件不存在。")

# 重置上一个输出
if len(st.session_state.messages) > 0:
    st.sidebar.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))

# ---  随机token开关 ---
st.sidebar.title("设置")
st.session_state.use_token = st.sidebar.checkbox("开启随机token", value=True)
