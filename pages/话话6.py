import os
import google.generativeai as genai
import json
import streamlit as st
import pickle
import random
import string
import time
import zipfile
from io import BytesIO
from google.api_core import exceptions
from datetime import datetime


# --- API 密钥设置 ---
API_KEYS = {
    "主密钥": "AIzaSyCBjZbA78bPusYmUNvfsmHpt6rPx6Ur0QE",  # 替换成你的主 API 密钥
    "备用1号": "AIzaSyAWfFf6zqy1DizINOwPfxPD8EF2ACdwCaQ",  # 替换成你的备用 API 密钥
    "备用2号":"AIzaSyD4UdMp5wndOAKxtO1CWpzuZEGEf78YKUQ",
    "备用3号":"AIzaSyBVbA7tEyyy_ASp7l9P60qSh1xOM2CSMNw",
    "备用4号":"AIzaSyDezEpxvtY1AKN6JACMU9XHte5sxATNcUs",
    "备用5号":"AIzaSyBgyyy2kTTAdsLB53OCR2omEbj7zlx1mjw",
    "备用6号":"AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY",
    "备用7号":"AIzaSyDdyhqcowl0ftcbK9pMObXzM7cIOQMtlmA",
    "备用8号":"AIzaSyAA7Qs9Lzy4UxxIqCIQ4RknchiWQt_1hgI",
    "备用9号":"AIzaSyCj_CCwQua1mfq3EjzqV6Up6NHsxtb9dy8",
    "备用10号":"AIzaSyDOI2e-I1RdXBnk99jY2H00A3aymXREETA"
    # 可以继续添加更多 API key
}


# --- 配置 API 密钥 ---
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]  # Default to the first key
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# --- 模型设置 ---
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-thinking-exp-1219",
  generation_config=generation_config,
  safety_settings=safety_settings,
  system_instruction="""
小兔子

""",
)


# --- 默认角色设定 ---
DEFAULT_CHARACTER_SETTINGS = {
    "设定1": "这是一个示例设定 1。",
    "设定2": "这是一个示例设定 2。",
}

# --- 文件操作函数 ---
# 获取当前文件路径
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'character_settings' not in st.session_state:
    st.session_state.character_settings = {}
if 'enabled_settings' not in st.session_state:
    st.session_state.enabled_settings = {}
if 'regenerate_index' not in st.session_state:
    st.session_state.regenerate_index = None
if 'continue_index' not in st.session_state:
    st.session_state.continue_index = None
if "use_token" not in st.session_state:
    st.session_state.use_token = True  # 默认启用token

# --- 功能函数 ---
def generate_token():
    """生成带括号的随机 token (汉字+数字，数字个数随机)"""
    import random
    import string
    random.seed()
    token_length = random.randint(10, 15)
    characters = "一乙二十丁厂七卜人入八九几儿了力乃刀又三于干亏士工土才寸下大丈与万上小口巾山千乞川亿个勺久凡及夕丸么广亡门义之尸弓己已子卫也女飞刃习叉马乡丰王井开鳍癞瀑襟璧戳攒孽蘑藻鳖蹭蹬簸簿蟹靡癣羹鬓攘蠕巍鳞糯霹躏髓蘸镶瓤矗"
    hanzi_token = "".join(random.choice(characters) for _ in range(token_length - 1))

    probability = random.random()
    if probability < 0.4:
        digit_count = 1
    elif probability < 0.7:
        digit_count = 2
    else:
        digit_count = 3

    digit_token = "、".join(random.choice(string.digits) for _ in range(digit_count))

    return f"({hanzi_token})({digit_token})"

def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"成功读取历史记录！({os.path.basename(log_file)})")
    except FileNotFoundError:
        st.warning(f"没有找到历史记录文件。({os.path.basename(log_file)})")

def clear_history(log_file):
    st.session_state.messages.clear()
    if os.path.exists(log_file):
        os.remove(log_file)
    st.success("历史记录已清除！")

def regenerate_message(i):
    st.session_state.regenerate_index = i

def continue_message(i):
    st.session_state.continue_index = i

def getAnswer(prompt, continue_mode=False):
    system_message = ""
    if st.session_state.get("test_text"):
        system_message += st.session_state.test_text + "\n"
    for setting_name in st.session_state.enabled_settings:
        if st.session_state.enabled_settings[setting_name]:
            system_message += st.session_state.character_settings[setting_name] + "\n"

    chat_session = model.start_chat(history=[])
    if system_message:
        chat_session.send_message(system_message)

    if continue_mode and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        prompt = f"[请继续补全这句话，不要重复之前的内容，使用合适的标点符号和大小写：{st.session_state.messages[-1]['content']}]"

    response = chat_session.send_message(prompt, stream=True)
    for chunk in response:
        yield chunk.text

# --- Streamlit 布局 ---
st.set_page_config(
    page_title="Gemini Chatbot",
    layout="wide"
)

# 添加 API key 选择器
with st.sidebar.expander("API Key 选择"):
    st.session_state.selected_api_key = st.selectbox(
        "选择 API Key:",
        options=list(API_KEYS.keys()),
        index=list(API_KEYS.keys()).index(st.session_state.selected_api_key),
    )
    genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# 在左侧边栏创建 token 复选框
with st.sidebar:
    st.session_state.use_token = st.checkbox("Token", value=True) # 默认开启

# 聊天输入框
if prompt := st.chat_input("输入你的消息:"):
    token = generate_token()
    if "use_token" in st.session_state and st.session_state.use_token:
        full_prompt = f"{prompt} (token: {token})"
        st.session_state.messages.append({"role": "user", "content": full_prompt})
    else:
        full_prompt = prompt
        st.session_state.messages.append({"role": "user", "content": full_prompt})

    with st.chat_message("user"):
        st.markdown(prompt if not st.session_state.use_token else f"{prompt} (token: {token})")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(full_prompt):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 保存聊天记录
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)

# 功能区 1: 文件操作
with st.sidebar.expander("文件操作"):
    if len(st.session_state.messages) > 0:
        st.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 else None)
    st.button("读取历史记录", on_click=lambda: load_history(log_file))
    if st.button("清除历史记录"):
        st.session_state.clear_confirmation = True
    if "clear_confirmation" in st.session_state and st.session_state.clear_confirmation:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认清除", key="clear_history_confirm"):
                clear_history(log_file)
                st.session_state.clear_confirmation = False
                st.experimental_rerun()
        with col2:
            if st.button("取消", key="clear_history_cancel"):
                st.session_state.clear_confirmation = False
    st.download_button(
        label="下载聊天记录",
        data=pickle.dumps(st.session_state.messages),
        file_name=os.path.basename(log_file),
        mime="application/octet-stream",
    )
    uploaded_file = st.file_uploader("读取本地 pkl 文件", type=["pkl"])
    if uploaded_file is not None:
        try:
            loaded_messages = pickle.load(uploaded_file)
            st.session_state.messages = loaded_messages
            st.success(f"成功读取本地 pkl 文件！({uploaded_file.name})")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"读取本地 pkl 文件失败：{e}")

# 功能区 2: 角色设定
with st.sidebar.expander("角色设定"):
    uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt)", type=["txt"])
    if uploaded_setting_file is not None:
        try:
            setting_name = os.path.splitext(uploaded_setting_file.name)[0]
            setting_content = uploaded_setting_file.read().decode("utf-8")
            st.session_state.character_settings[setting_name] = setting_content
            st.session_state.enabled_settings[setting_name] = False
            st.experimental_rerun()
        except Exception as e:
            st.error(f"读取文件失败: {e}")

    for setting_name in DEFAULT_CHARACTER_SETTINGS:
        if setting_name not in st.session_state.character_settings:
            st.session_state.character_settings[setting_name] = DEFAULT_CHARACTER_SETTINGS[setting_name]
        st.session_state.enabled_settings[setting_name] = st.checkbox(setting_name, st.session_state.enabled_settings.get(setting_name, False), key=f"checkbox_{setting_name}")

    st.session_state.test_text = st.text_area("System Message (Optional):", st.session_state.get("test_text", ""), key="system_message")

    if st.button("刷新"):
        st.experimental_rerun()

# 显示历史记录和编辑功能
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        main_col, button_col = st.columns([12, 1])
        with main_col:
            st.write(message["content"], key=f"message_{i}")
        with button_col:
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✏️", key=f"edit_{i}"):
                        st.session_state.editable_index = i
                        st.session_state.editing = True
                with col2:
                    if st.button("♻️", key=f"regenerate_{i}"):
                        regenerate_message(i)
                with col3:
                    if st.button("➕", key=f"continue_{i}"):
                        continue_message(i)

if st.session_state.get("editing"):
    i = st.session_state.editable_index
    message = st.session_state.messages[i]
    with st.chat_message(message["role"]):
        new_content = st.text_area(f"{message['role']}:", message["content"], key=f"message_edit_{i}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存 ✅", key=f"save_{i}"):
                st.session_state.messages[i]["content"] = new_content
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.success("已保存更改！")
                st.session_state.editing = False
        with col2:
            if st.button("取消 ❌", key=f"cancel_{i}"):
                st.session_state.editing = False

# 处理重新生成的消息
if st.session_state.regenerate_index is not None:
    i = st.session_state.regenerate_index
    st.session_state.regenerate_index = None
    with st.spinner("正在重新生成回复..."):
        prompt = st.session_state.messages[i - 1]["content"] if i > 0 and st.session_state.messages[i - 1]["role"] == "user" else None
        if prompt:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for chunk in getAnswer(prompt):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages[i]["content"] = full_response
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.experimental_rerun()
        else:
            st.error("无法获取上一条用户消息以重新生成。")

# 处理延续生成的消息
if st.session_state.continue_index is not None:
    i = st.session_state.continue_index
    st.session_state.continue_index = None
    with st.spinner("正在继续生成回复..."):
        prompt = st.session_state.messages[i]["content"] if i >= 0 else None
        if prompt:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for chunk in getAnswer(prompt, continue_mode=True):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
        else:
            st.error("无法获取上一条消息以继续生成。")

# 显示已加载的设定
enabled_settings_display = [setting_name for setting_name, enabled in st.session_state.enabled_settings.items() if enabled]
if enabled_settings_display:
    st.write("已加载设定:", ", ".join(enabled_settings_display))
