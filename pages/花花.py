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
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"  # **请勿将您的API Key 泄露在公开场合**
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
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config,
                            safety_settings=safety_settings)
# Vision Model
model_v = genai.GenerativeModel(model_name='gemini-pro-vision', generation_config=generation_config)


# LLM
def generate_token():
    """生成一个 10 位到 20 位的随机 token"""
    token_length = random.randint(10, 20)
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    token = ''.join(random.choice(characters) for i in range(token_length))
    return token


def getAnswer(prompt, token, image):
    his_messages = []
    his_messages.append(
        {"role": "model", "parts": [{"text": f"你的随机token是：{token}"}]}
    )
    # 只保留用户输入的最后一条消息
    for msg in st.session_state.messages[-1:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
    if image is not None:
        # 将图片转换为字节流
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        prompt_v = ""
        for msg in st.session_state.messages[-1:]:
            prompt_v += f'''{msg["role"]}:{msg["content"]}'''
        response = model_v.generate_content([prompt_v, img_bytes], stream=True)  # 将图片字节流传递给模型
    else:
        response = model.generate_content(contents=his_messages, stream=True)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
        yield chunk.text
    #  更新最后一条回复
    if st.session_state.last_response:
        st.session_state.last_response[-1] = full_response


# 获取文件名，并生成对应的文件名
# 获取当前 Python 文件名
filename = os.path.splitext(os.path.basename(__file__))[0] + ".pkl"  # 使用 .pkl 扩展名

# 获取完整路径
log_file = os.path.join(os.path.dirname(__file__), filename)  # 使用 os.path.dirname 获取当前目录

# 检查文件是否存在，如果不存在就创建空文件
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass  # 创建空文件

# 加载历史记录（只执行一次）
if "messages" not in st.session_state:
    # 从文件加载历史记录
    try:
        with open(log_file, "rb") as f:  # 使用 "rb" 模式读取
            st.session_state.messages = pickle.load(f)
    except FileNotFoundError:
        st.session_state.messages = []
    except EOFError:
        st.warning(f"读取历史记录失败：文件可能损坏。")
        st.session_state.messages = []  # 清空 messages
        # 可以考虑在这里添加代码，提示用户重新创建文件或重新加载数据

# 初始化 st.session_state.editing_index
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None

if "last_response" not in st.session_state:
    st.session_state.last_response = [""]  # 初始化时添加默认值
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

# 显示历史记录（只执行一次）
for i, message in enumerate(st.session_state.messages):
    col1, col2 = st.columns([9, 1])  # 调整列宽，为按钮预留更多空间
    with col1:
        with st.chat_message(message["role"]):
            st.write(message["content"], key=f"message_{i}")

    # ===  在循环内部添加按钮和编辑逻辑 ===
    #  只有在最后一条消息旁边添加按钮
    if i == len(st.session_state.messages) - 1:
        with col2:
            #  编辑按钮
            if st.button("✏️", key=f"edit_button_{i}"):
                st.session_state.editing_index = i
                
            # 按钮和 按钮
            col3, col4 = st.columns(2)
            with col3:
                # 按钮内嵌翻页功能
                st.button("✨", key=f"generate_{i}", on_click=generate_new_response)
            with col4:
                st.button("➡️", key=f"reoutput_{i}", on_click=reoutput_last_response)

            #  " " 和 " " 按钮只在最后一条消息拥有两个回答时显示
            if len(st.session_state.last_response) > 1:
                col5, col6 = st.columns(2)
                with col5:
                    st.button("⏩", key=f"decrease_{i}", on_click=lambda: decrease_page_index(0),
                               disabled=st.session_state.page_index == 0)
                with col6:
                    st.button("⏪", key=f"next_{i}", on_click=lambda: next_page_index(len(st.session_state.last_response) - 1),
                               disabled=st.session_state.page_index == len(st.session_state.last_response) - 1)
                        
                #  显示页码，只在最后一条消息拥有两个回答时显示
                st.write(f"第 {st.session_state.page_index + 1} 页 / 共 {len(st.session_state.last_response)} 页")

    # 如果当前消息正在编辑，显示文本框
    if st.session_state.editing_index == i:
        with st.chat_message(message["role"]):
            new_content = st.text_area(
                "编辑消息:",
                value=message["content"],
                key=f"edit_text_{i}"
            )
            if st.button("保存", key=f"save_button_{i}"):
                # 更新消息内容
                st.session_state.messages[i]["content"] = new_content
                # 保存到文件
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                # 重置编辑状态
                st.session_state.editing_index = None
                # 刷新页面，重新加载聊天记录
                st.experimental_rerun()

    # 定义 generate_new_response 函数
    def generate_new_response():
        """生成新的回复并显示"""
        if st.session_state.messages:
            # 获取最后一个用户的提示和token
            last_user_prompt = st.session_state.messages[-1]["content"]
            last_user_token = st.session_state.messages[-1]["token"]
            # 生成新回复
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for chunk in getAnswer(last_user_prompt, last_user_token, st.session_state.img):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            # 更新 last_response 和 page_index
            st.session_state.last_response.append(full_response)
            st.session_state.page_index = len(st.session_state.last_response) - 1
            
            # 现在，在更新 last_response 后，我们需要更新 page_index，以确保编辑功能可以定位到最新的 AI 回复
            st.session_state.page_index += 1
            
            #  保存聊天记录
            with open(log_file, "wb") as f:  # 使用 "wb" 模式写入
                pickle.dump(st.session_state.messages, f)

def decrease_page_index(min_index):
    """减少页面索引"""
    st.session_state.page_index = max(min_index, st.session_state.page_index - 1)
    # 重新显示当前页面的 AI 回复
    if st.session_state.page_index >= 0 and st.session_state.page_index < len(st.session_state.last_response):
        with st.chat_message("assistant"):
            st.markdown(st.session_state.last_response[st.session_state.page_index])

def next_page_index(max_index):
    """跳转到下一页"""
    st.session_state.page_index = min(max_index, st.session_state.page_index + 1)
    # 重新显示当前页面的 AI 回复
    if st.session_state.page_index >= 0 and st.session_state.page_index < len(st.session_state.last_response):
        with st.chat_message("assistant"):
            st.markdown(st.session_state.last_response[st.session_state.page_index])

def reoutput_last_response():
    """重新输出上一个 AI 的回答"""
    if st.session_state.last_response and len(st.session_state.last_response) > 1:
        # 如果存在上一个 AI 的回答，且超过一个回答
        st.session_state.page_index = (st.session_state.page_index + 1) % len(st.session_state.last_response)
        # 更新页面索引，循环显示 AI 的回答
        with st.chat_message("assistant"):
            st.markdown(st.session_state.last_response[st.session_state.page_index])
            # 重新显示当前页面的 AI 回复

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

# 在 Streamlit 界面中添加输入框
user_input = st.text_input("输入你的消息:", key="user_input")

# 添加发送消息按钮
if st.button("发送", on_click=send_message):
    if user_input:
        # 获取用户输入的消息
        message = user_input
        # 将用户消息添加到聊天记录中
        st.session_state.messages.append({"role": "user", "content": message})
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(message)
        # 清空输入框
        st.session_state.user_input = ""

def send_message():
    """发送用户消息并显示 AI 的回复"""
    # 获取用户输入的消息
    message = st.session_state.user_input
    # 生成随机 token
    token = generate_token()
    # 将用户消息和 token 添加到聊天记录
    st.session_state.messages.append({"role": "user", "content": message, "token": token})
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(message)
    # 清空输入框
    st.session_state.user_input = ""
    # 生成 AI 回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(message, token, st.session_state.img):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # 更新 last_response 和 page_index
    st.session_state.last_response.append(full_response)
    st.session_state.page_index = len(st.session_state.last_response) - 1
    # 保存聊天记录
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)
