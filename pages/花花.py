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

# 加载 API 密钥
load_dotenv()
api_key = os.getenv("API_KEY")  # 将你的 API 密钥放在 .env 文件中，变量名为 API_KEY

# 配置 Gemini 模型
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
model_v = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config=generation_config)

# 聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []
if "img" not in st.session_state:
    st.session_state.img = None

# 额外输出管理
if "extra_outputs" not in st.session_state:
    st.session_state.extra_outputs = []
if "current_output_index" not in st.session_state:
    st.session_state.current_output_index = 0

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

# 聊天界面
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"], key=f"{i}_{message['role']}_{message['content'][:10]}"):  # 添加更具唯一性的 key
        if i == len(st.session_state.messages) - 1 and len(st.session_state.extra_outputs) > 1:
            # 只有最后一条回复才显示多个结果切换按钮
            st.markdown(st.session_state.extra_outputs[st.session_state.current_output_index])
            if st.button(" ", key=f"prev_{i}"):
                st.session_state.current_output_index = max(0, st.session_state.current_output_index - 1)
            if st.button(" ", key=f"next_{i}"):
                st.session_state.current_output_index = min(len(st.session_state.extra_outputs) - 1, st.session_state.current_output_index + 1)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Enter your message (including your token):"):
    with st.chat_message("user"):
        st.markdown(f"{prompt}")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        st.session_state.extra_outputs = []
        for chunk in getAnswer(prompt, st.session_state.img):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 操作栏
col1, col2 = st.columns(2)

with col1:
    # 重新输出按钮
    if st.button("✨", key="regenerate"):  # 替换成你想要的图标
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            st.session_state.extra_outputs = []
            for chunk in getAnswer(prompt, st.session_state.img):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

with col2:
    # 额外输出按钮
    if st.button("➡️", key="extra_output"):  # 替换成你想要的图标
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in getAnswer(prompt, st.session_state.img):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.extra_outputs.append(full_response)

# 自动保存聊天记录
save_history()

# 定义 getAnswer 函数
def getAnswer(prompt, image):
    his_messages = []
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
Use code with caution.
'''
        response = model_v.generate_content([prompt_v, img_bytes], stream=True)  # 将图片字节流传递给模型
    else:
        response = model.generate_content(contents=his_messages, stream=True)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
        yield chunk.text
    return full_response

# 保存和加载聊天记录
def save_history():
    import os
    import pickle
    filename = os.path.splitext(os.path.basename(__file__))[0] + ".pkl"  # 获取当前文件名
    with open(filename, "wb") as f:
        pickle.dump(st.session_state.messages, f)

def load_history():
    files = [f for f in os.listdir(".") if f.endswith(".pkl")]
    if files:
        selected_file = st.selectbox("选择要加载的记录文件", files)
        with open(selected_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"聊天记录已加载")
    else:
        st.warning("当前目录下没有记录文件")

def clear_history():
    st.session_state.messages = []
    st.success("聊天记录已清除")
