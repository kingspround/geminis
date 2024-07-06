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

# Vision Model
model_v = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config=generation_config)

# LLM
def generate_token():
    """生成一个 10 位到 20 位的随机 token"""
    token_length = random.randint(10, 20)
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    token = "".join(random.choice(characters) for i in range(token_length))
    return token


def getAnswer(prompt, token, image):
    his_messages = []
    his_messages.append({"role": "model", "parts": [{"text": f"你的随机token是：{token}"}]})
    # 只保留用户输入的最后一条消息
    for msg in st.session_state.messages[-1:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
    if image is not None:
        # 将图片转换为字节流
        img_bytes = BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        prompt_v = ""
        for msg in st.session_state.messages[-1:]:
            prompt_v += f"{msg['role']}:{msg['content']}"
        response = model_v.generate_content(
            [prompt_v, img_bytes], stream=True
        )  # 将图片字节流传递给模型
    else:
        response = model.generate_content(contents=his_messages, stream=True)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
    yield chunk.text
    # 更新最后一条回复
    if st.session_state.last_response:
        st.session_state.last_response[-1] = full_response

# 初始化聊天记录列表
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入并处理
if prompt := st.chat_input("Enter your message:"):
    token = generate_token()
    st.session_state.messages.append({"role": "user", "content": f"{prompt}  (token: {token})"})
    with st.chat_message("user"):
        st.markdown(f"{prompt}  (token: {token})")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt, token, st.session_state.img):
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
st.sidebar.title("控制面板")
# 图片上传
uploaded_file = st.sidebar.file_uploader("上传图片", type=["png", "jpg", "jpeg", "gif"])
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    bytes_io = BytesIO(bytes_data)
    img = Image.open(bytes_io)
    # 将图片转换为 JPEG 格式
    img = img.convert("RGB")
    st.session_state.img = img  # 保存到 st.session_state.img
    st.sidebar.image(bytes_io, width=150)  # 在侧边栏显示图片

# --- 侧边栏功能 ---

# ---  ---

#  ---- 适配  ----
def load_history():
    """从 logs 文件夹加载聊天记录"""
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"聊天记录已加载")
    except FileNotFoundError:
        st.warning("logs 文件夹中没有记录文件")

def clear_history():
    """清除当前聊天记录"""
    st.session_state.messages = []
    st.session_state.last_response = []  # 清除 last_response 列表
    st.success("聊天记录已清除")

# --- 

# 使用 st.sidebar 放置按钮
st.sidebar.title("操作")
st.sidebar.button("读取历史记录", on_click=load_history)
st.sidebar.button("清除历史记录", on_click=clear_history)

# 使用 st.sidebar 放置按钮
st.sidebar.title("操作")
if len(st.session_state.messages) > 0:
    st.sidebar.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))
st.sidebar.download_button(
    label="下载聊天记录",  # 使用 st.sidebar.download_button 直接下载
    data=open(log_file, "rb").read(),  # 读取文件内容
    file_name=filename,  # 设置下载文件名
    mime="application/octet-stream",  # 设置 MIME 类型
)
st.sidebar.button("读取历史记录", on_click=lambda: load_history(log_file))
st.sidebar.button("清除历史记录", on_click=lambda: clear_history(log_file))

# 添加读取本地文件的按钮
if st.sidebar.button("读取本地文件"):
    st.session_state.file_upload_mode = True

if st.session_state.get("file_upload_mode"):
    uploaded_file = st.sidebar.file_uploader("选择文件", type=["pkl"])
    if "file_loaded" not in st.session_state:  # 如果 file_loaded 不存在
        st.session_state.file_loaded = False

    if uploaded_file is not None and not st.session_state.file_loaded:  # 只有当 file_loaded 为 False 时才读取文件
        try:
            # 读取文件内容
            loaded_messages = pickle.load(uploaded_file)

            # 合并到 st.session_state.messages 中
            st.session_state.messages.extend(loaded_messages)

            # 显示聊天记录和编辑按钮
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.write(message["content"], key=f"message_{i}")
                    if i >= len(st.session_state.messages) - 2:  # 在最后两条消息中添加编辑按钮
                        if st.button("编辑", key=f"edit_{i}"):
                            st.session_state.editable_index = i
                            st.session_state.editing = True

            # 添加关闭按钮
            if st.sidebar.button("关闭", key="close_upload"):
                st.session_state.file_upload_mode = False
                st.session_state.file_loaded = False  # 将 file_loaded 设置为 False

            # 保存合并后的历史记录到文件
            with open(log_file, "wb") as f:
                pickle.dump(st.session_state.messages, f)

            st.session_state.file_loaded = True  # 将 file_loaded 设置为 True

        except Exception as e:
            st.error(f"读取本地文件失败：{e}")


def load_history(log_file):
    try:
        # 重新打开文件
        with open(log_file, "rb") as f:  # 使用 "rb" 模式读取
            messages = pickle.load(f)
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 重新运行应用程序，确保聊天记录加载后不会丢失
            st.experimental_rerun()  

    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")
    except EOFError:  # 处理 EOFError
        st.warning(f"读取历史记录失败：文件可能损坏。")

def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)  # 删除文件
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")
