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
    st.info("臭群友！  (๑•̀ㅂ•́)و✧  还不快说你的密语！  (๑•̀ㅂ•́)و✧  不然人家就生气了！")
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
        # 将 his_messages 转换成 Content 类型
        contents = {
            "parts": his_messages
        }

        response = model.generate_content(contents=contents, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response  # 返回完整的回复
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""  # 在发生错误时返回空字符串

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

# 显示历史记录（只执行一次）
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # 使用 st.write 显示对话内容
        st.write(message["content"], key=f"message_{i}")

        # 在最后两个对话中添加编辑按钮
        if i >= len(st.session_state.messages) - 2:
            if st.button("编辑♡", key=f"edit_{i}"):
                # 更改为可编辑文本
                st.session_state.editable_index = i  # 记录可编辑的索引
                st.session_state.editing = True  # 表示正在编辑

if st.session_state.get("editing"):
    # 如果正在编辑，显示编辑框和保存/取消按钮
    i = st.session_state.editable_index
    message = st.session_state.messages[i]

    with st.chat_message(message["role"]):
        new_content = st.text_area(
            f"{message['role']}:", message["content"], key=f"message_edit_{i}"
        )

        col1, col2 = st.columns(2)  # 创建两列布局
        with col1:
            if st.button("保存", key=f"save_{i}"):
                st.session_state.messages[i]["content"] = new_content
                # 保存更改到文件
                with open(log_file, "wb") as f:  # 使用 "wb" 模式写入
                    pickle.dump(st.session_state.messages, f)
                st.success(f"已保存更改！")
                st.session_state.editing = False  # 结束编辑状态
        with col2:
            if st.button("取消", key=f"cancel_{i}"):
                st.session_state.editing = False  # 结束编辑状态

if prompt := st.chat_input("臭群友，  快来跟人家玩游戏吧！~♡  "):
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

    # 魅魔女王反问
    st.session_state.messages.append({"role": "user", "content": "哼，  (｡•ˇ‸ˇ•｡)  你想要人家怎么玩呢？  (｡•ˇ‸ˇ•｡)  说清楚点！  (๑•̀ㅂ•́)و✧  "})
    with st.chat_message("user"):
        st.markdown("哼，  (｡•ˇ‸ˇ•｡)  你想要人家怎么玩呢？  (｡•ˇ‸ˇ•｡)  说清楚点！  (๑•̀ㅂ•́)و✧  ")

    # 保存历史记录到文件
    with open(log_file, "wb") as f:  # 使用 "wb" 模式写入
        pickle.dump(st.session_state.messages, f)

# 使用 st.sidebar 放置按钮
st.sidebar.title("操弄 AI~♡")
if len(st.session_state.messages) > 0:
    st.sidebar.button("重置上一个输出，不然人家就生气了！", on_click=lambda: st.session_state.messages.pop(-1))
st.sidebar.download_button(
    label="下载聊天记录",  # 使用 st.sidebar.download_button 直接下载
    data=open(log_file, "rb").read(),  # 读取文件内容
    file_name=filename,  # 设置下载文件名
    mime="application/octet-stream",  # 设置 MIME 类型
)
st.sidebar.button("读取历史记录♡", on_click=lambda: load_history(log_file))
st.sidebar.button("清除历史记录♡", on_click=lambda: clear_history(log_file))

# 添加读取本地文件的按钮
if st.sidebar.button("读取本地文件♡"):
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
                        if st.button("编辑♡", key=f"edit_{i}"):
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
