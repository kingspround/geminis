import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import streamlit as st
import random
import pickle

# Insert your API key here
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"

if "key" not in st.session_state:
    st.session_state.key = NONE

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

# Vision Model
model_v = genai.GenerativeModel(model_name='gemini-pro-vision',generation_config=generation_config)

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
        {"role": "model", "parts": [{"text": f"你的随机token是：{token}"""}]}
    )

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    if image is not None:
        # 将图片转换为字节流
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        prompt_v = ""
        for msg in st.session_state.messages[-20:]:
            prompt_v += f'''{msg["role"]}:{msg["content"]}
'''
        response = model_v.generate_content([prompt_v, img_bytes], stream=True)  # 将图片字节流传递给模型
    else:
        response = model.generate_content(contents=his_messages, stream=True)

    full_response = ""
    responses = []  # 存储多个回复
    for chunk in response:
        full_response += chunk.text
        responses.append(chunk.text)
        yield chunk.text
    return responses  # 返回所有回复

def save_history():
    """将聊天记录保存到 logs 文件夹的 .pkl 文件"""
    os.makedirs("logs", exist_ok=True)
    filename = f"logs/{generate_token()}.pkl"  # 使用随机 token 生成文件名
    with open(filename, "wb") as f:
        # 将消息内容转换为纯文本
        messages_to_save = [
            {"role": msg["role"], "content": msg["content"].replace("  ✨ ➡️", "").replace("  ⏪ ⏩ ✨ ➡️", "")}
            for msg in st.session_state.messages
        ]
        pickle.dump(messages_to_save, f)
    # 不再显示保存提示

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
    st.success("聊天记录已清除")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "img" not in st.session_state:
    st.session_state.img = None

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

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # 为最后一条聊天记录添加按钮
        if i == len(st.session_state.messages) - 1 and message["role"] == "assistant":
            if "responses" in message:
                current_index = message.get("current_index", 0)
                if len(message["responses"]) > 1:
                    st.markdown(f"  ✨ ➡️ ⏪ ⏩")
                    st.button("⏪", key=f"prev_{i}", on_click=lambda i=i: setattr(st.session_state.messages[i], "current_index", (current_index - 1) % len(st.session_state.messages[i]["responses"])))
                    st.button("⏩", key=f"next_{i}", on_click=lambda i=i: setattr(st.session_state.messages[i], "current_index", (current_index + 1) % len(st.session_state.messages[i]["responses"])))
                st.button("✨", key=f"regenerate_{i}", on_click=lambda i=i: regenerate_last_message(i))
                st.button("➡️", key=f"add_new_{i}", on_click=lambda i=i: add_new_response(i))
            else:
                st.button("✨", key=f"regenerate_{i}", on_click=lambda i=i: regenerate_last_message(i))
                st.button("➡️", key=f"add_new_{i}", on_click=lambda i=i: add_new_response(i))

def regenerate_last_message(i):
    """重新生成最后一条聊天记录"""
    message = st.session_state.messages[i]
    if message["role"] == "assistant":
        prompt = message["content"].split("  ✨ ➡️")[0]  # 获取消息内容
        token = generate_token()
        responses = getAnswer(prompt, token, st.session_state.img)
        message["responses"] = responses
        message["current_index"] = 0
        st.session_state.messages[i] = message
        update_last_message_content(i)

def add_new_response(i):
    """额外输出一个新的结果"""
    message = st.session_state.messages[i]
    if message["role"] == "assistant":
        prompt = message["content"].split("  ✨ ➡️")[0]  # 获取消息内容
        token = generate_token()
        new_response = getAnswer(prompt, token, st.session_state.img)
        if "responses" not in message:
            message["responses"] = []
        message["responses"].extend(new_response)
        st.session_state.messages[i] = message
        update_last_message_content(i)

def update_last_message_content(i):
    """更新最后一条聊天记录的内容"""
    message = st.session_state.messages[i]
    if message["role"] == "assistant":
        if "responses" in message:
            current_index = message.get("current_index", 0)
            st.session_state.messages[i]["content"] = message["responses"][current_index]
            # 重新添加按钮
            if len(message["responses"]) > 1:
                st.session_state.messages[i]["content"] += f"  ⏪ ⏩ ✨ ➡️"
            else:
                st.session_state.messages[i]["content"] += f"  ✨ ➡️"

if prompt := st.chat_input("Enter your message (including your token):"):
    token = generate_token()
    st.session_state.messages.append({"role": "user", "content": f"{prompt}  (token: {token})"})
    with st.chat_message("user"):
        st.markdown(f"{prompt}  (token: {token})")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        responses = getAnswer(prompt, token, st.session_state.img)
        st.session_state.messages[-1]["responses"] = responses
        st.session_state.messages[-1]["current_index"] = 0
        for chunk in responses:
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
    # 自动保存聊天记录
    save_history()
