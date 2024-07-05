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


def save_history():
    """将聊天记录保存到 logs 文件夹的 chat_log.pkl 文件"""
    os.makedirs("logs", exist_ok=True)
    # 获取当前文件名
    current_filename = os.path.basename(__file__).split('.')[0]
    # 保存聊天记录到 logs 文件夹
    filename = os.path.join("logs", f"{current_filename}_chat_log.pkl")
    with open(filename, "wb") as f:
        pickle.dump(st.session_state.messages, f)


def load_history():
    """从 logs 文件夹加载聊天记录"""
    files = [f for f in os.listdir("logs") if f.endswith(".pkl")]
    if files:
        selected_file = st.selectbox("选择要加载的记录文件", files)
        filename = os.path.join("logs", selected_file)
        with open(filename, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"聊天记录已加载")
    else:
        st.warning("logs 文件夹中没有记录文件")


def clear_history():
    """清除当前聊天记录"""
    st.session_state.messages = []
    st.session_state.last_response = []  # 清除 last_response 列表
    st.session_state.page_index = 0  # 重置页面索引
    st.success("聊天记录已清除")


def increase_page_index():
    """增加页面索引"""
    st.session_state.page_index += 1


def decrease_page_index():
    """减少页面索引"""
    st.session_state.page_index = max(0, st.session_state.page_index - 1)


def next_page_index():
    """跳转到下一页"""
    st.session_state.page_index = min(len(st.session_state.last_response) - 1, st.session_state.page_index + 1)


def reoutput_last_response():
    """重新输出最后一条回复，将新回复添加到最后并更新上下文"""
    if st.session_state.last_response:
        # 获取当前回复在 last_response 中的索引
        current_response_index = st.session_state.page_index
        # 删除当前回复
        del st.session_state.last_response[current_response_index]

        # 获取对应用户消息的索引
        user_message_index = len(st.session_state.messages) - 1
        # 删除旧的用户消息和回复
        del st.session_state.messages[user_message_index]

        # 重新发送用户消息并获取新的回复
        user_message = st.session_state.messages[-1]
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in getAnswer(user_message["content"], user_message["token"],
                                    st.session_state.img):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        # 将新的回复添加到最后
        st.session_state.last_response.append(full_response)

        # 更新页面索引，指向新的回复
        st.session_state.page_index = len(st.session_state.last_response) - 1
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


if "messages" not in st.session_state:
    st.session_state.messages = []
if "img" not in st.session_state:
    st.session_state.img = None
if "last_response" not in st.session_state:
    st.session_state.last_response = [""] # 初始化时添加默认值
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

# 侧边栏
st.sidebar.title("控制面板")
st.sidebar.button("读取历史记录", on_click=load_history)
st.sidebar.button("清除历史记录", on_click=clear_history)
st.sidebar.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))
# 图片上传
uploaded_file = st.sidebar.file_uploader("上传图片", type=['png', 'jpg', 'jpeg', 'gif'])
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    bytes_io = BytesIO(bytes_data)
    img = Image.open(bytes_io)
    # 将图片转换为 JPEG 格式
    img = img.convert('RGB')
    st.session_state.img = img  # 保存到 st.session_state.img
    st.sidebar.image(bytes_io, width=150)  # 在侧边栏显示图片
# AI 最后一条回复管理按钮
col1, col2 = st.sidebar.columns(2)
with col1:
    st.button("✨", on_click=reoutput_last_response, help="重新输出这条回复")
with col2:
    st.button("➡️", on_click=generate_new_response, help="翻页并输出新结果")
# 侧边栏按钮切换结果
if len(st.session_state.last_response) > 1:
    col3, col4 = st.sidebar.columns(2)
    with col3:
        st.button("⏪", on_click=decrease_page_index, help="上一页")
    with col4:
        st.button("⏩", on_click=next_page_index, help="下一页")

# 显示当前页面的 AI 回复
if st.session_state.page_index >= 0 and st.session_state.page_index < len(st.session_state.last_response):
    with st.chat_message("assistant"):
        st.markdown(st.session_state.last_response[st.session_state.page_index])
# 显示页码
if len(st.session_state.last_response) > 1:
    st.write(f"第 {st.session_state.page_index + 1} 页 / 共 {len(st.session_state.last_response)} 页")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if prompt := st.chat_input("Enter your message:"):
    token = generate_token()
    st.session_state.messages.append({"role": "user", "content": prompt, "token":token})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        # 在获取回复时传入token
        for chunk in getAnswer(prompt, token, st.session_state.img):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # 更新 last_response 和 page_index
    st.session_state.last_response.append(full_response)
    st.session_state.page_index = len(st.session_state.last_response) - 1
# 自动保存聊天记录
save_history()
