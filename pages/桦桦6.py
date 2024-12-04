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
import glob



# --- API 密钥设置 ---
api_keys = {
    "主密钥": "AIzaSyCBjZbA78bPusYmUNvfsmHpt6rPx6Ur0QE",  # 替换成你的主 API 密钥
    "备用1号": "AIzaSyAWfFf6zqy1DizINOwPfxPD8EF2ACdwCaQ",  # 替换成你的备用 API 密钥
    "备用2号":"AIzaSyD4UdMp5wndOAKxtO1CWpzuZEGEf78YKUQ",
    "备用3号":"AIzaSyBVbA7tEyyy_ASp7l9P60qSh1xOM2CSMNw",
    "备用4号":"AIzaSyDezEpxvtY1AKN6JACMU9XHte5sxATNcUs",
    "备用5号":"AIzaSyBgyyy2kTTAdsLB53OCR2omEbj7zlx1mjw",
    "备用6号":"AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"
}

selected_key = st.sidebar.selectbox("选择 API 密钥", list(api_keys.keys()), index=0) # 默认选择主密钥
api_key = api_keys[selected_key]

if not api_key:
    st.error("请设置有效的API密钥。")
    st.stop()

genai.configure(api_key=api_key)


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

model = genai.GenerativeModel(model_name="gemini-1.5-pro-001", generation_config=generation_config, safety_settings=safety_settings)



# --- 碎片设定 ---
DEFAULT_FRAGMENTS = {
    "fragment1": "你是用户的好朋友，名叫桦桦",
    "fragment2": "设定2的内容...",
    "fragment3": "设定3的内容...",
    # ... 添加更多预设碎片
}


# --- LLM 函数 ---
def getAnswer(prompt):
    enabled_settings_content = ""
    enabled_settings = st.session_state.get("enabled_settings", {})

    his_messages = []
    his_messages.append(
        {"role": "model", "parts": [{"text": """
 Use code with caution.
[SYSTEM]
[]
[Personality：
]
[function：

]"""}]}
    )

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    his_messages = [msg for msg in his_messages if msg.get("parts") and msg["parts"][0].get("text")]

    # 添加角色设定到提示 (修正后的代码)
    enabled_settings = st.session_state.get("enabled_settings", {})
    active_settings = [name for name, enabled in enabled_settings.items() if enabled]

    if active_settings:
        settings_text = "[Character Settings]:\n"
        for setting_name in active_settings:
            setting_content = st.session_state.character_settings.get(setting_name, "")
            settings_text += f"{setting_name}:\n{setting_content}\n"

        his_messages.append({"role": "system", "parts": [{"text": settings_text}]})


    try:
        response = model.generate_content(contents=his_messages, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response
    except Exception as e:
        st.error(f"发生错误: {e}. 请检查你的API密钥是否有效。")
        return ""



# --- 文件操作函数 ---
filename = os.path.splitext(os.path.basename(__file__))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(__file__), filename)

# --- 读取历史记录 ---
def load_history(log_file):  # 将函数定义移到这里
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"成功从 {filename} 加载历史记录！")
    except (FileNotFoundError, EOFError):
        st.warning(f"{filename} 不存在或为空。")
        st.session_state.messages = []

# 确保文件存在
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass


# 初始化 session state
if "messages" not in st.session_state:
    load_history(log_file) #  直接调用load_history初始化

# ---  清除历史记录 ---
def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除 {filename} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{filename} 不存在。")

# --- 读取历史记录 ---
def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"成功从 {filename} 加载历史记录！")
    except (FileNotFoundError, EOFError):
        st.warning(f"{filename} 不存在或为空。")
        st.session_state.messages = []




# 显示历史记录和编辑功能 (与之前相同，略作简化)
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"], key=f"message_{i}")
    if i >= len(st.session_state.messages) - 2:
        if st.button("编辑", key=f"edit_{i}"):
            st.session_state.editable_index = i
            st.session_state.editing = True

if st.session_state.get("editing"):
    i = st.session_state.editable_index
    message = st.session_state.messages[i]
    with st.chat_message(message["role"]):
        new_content = st.text_area(f"{message['role']}:", message["content"], key=f"message_edit_{i}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存", key=f"save_{i}"):
                st.session_state.messages[i]["content"] = new_content
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.success("已保存更改！")
                st.session_state.editing = False
        with col2:
            if st.button("取消", key=f"cancel_{i}"):
                st.session_state.editing = False



# --- Streamlit 应用程序 ---

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "character_settings" not in st.session_state:
    st.session_state.character_settings = DEFAULT_FRAGMENTS.copy()

if "enabled_settings" not in st.session_state:
    st.session_state.enabled_settings = {name: False for name in DEFAULT_FRAGMENTS}


# ---  三个功能区侧边栏 ---
# 功能区 1: 文件操作
with st.sidebar.expander("文件操作"):
    if len(st.session_state.messages) > 0:
        st.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))

    st.button("读取历史记录", on_click=lambda: load_history(log_file))
    st.button("清除历史记录", on_click=lambda: clear_history(log_file))
    st.download_button(
        label="下载聊天记录",
        data=open(log_file, "rb").read(),
        file_name=filename,
        mime="application/octet-stream",
    )

    if "pkl_file_loaded" not in st.session_state:
        st.session_state.pkl_file_loaded = False  # 初始化标志

    uploaded_file = st.file_uploader("读取本地pkl文件", type=["pkl"])  # 只接受 .pkl 文件
    if uploaded_file is not None and not st.session_state.pkl_file_loaded:
        try:
            loaded_messages = pickle.load(uploaded_file)
            # 将加载的消息添加到现有的消息列表中 (或替换，取决于你的需求)
            st.session_state.messages.extend(loaded_messages)  # 使用extend追加消息
            # st.session_state.messages = loaded_messages  # 使用 = 替换现有消息

            st.session_state.pkl_file_loaded = True  # 设置标志，防止重复读取
            st.experimental_rerun() # 刷新页面以显示新的消息

        except Exception as e:
            st.error(f"读取本地pkl文件失败：{e}")


# 功能区 2: 角色设定
with st.sidebar.expander("角色设定"):
    for setting_name, setting_content in st.session_state.character_settings.items():
        st.checkbox(setting_name, key=f"enabled_{setting_name}", value=st.session_state.enabled_settings.get(setting_name, False))
        if st.session_state["enabled_settings"].get(setting_name, False):
            new_content = st.text_area(f"{setting_name} 内容:", setting_content, key=f"setting_content_{setting_name}")
            st.session_state.character_settings[setting_name] = new_content



# 功能区 3: ... (其他功能区)


# --- 聊天输入和响应 ---
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)
