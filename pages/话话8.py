import os
import google.generativeai as genai
import streamlit as st
import pickle
import random
import string
from io import BytesIO
import zipfile

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Gemini Chatbot",
    layout="wide"
)

# --- API 密钥设置 (保持原样) ---
API_KEYS = {
    "主密钥": "AIzaSyCBjZbA78bPusYmUNvfsmHpt6rPx6Ur0QE",
    "备用1号": "AIzaSyAWfFf6zqy1DizINOwPfxPD8EF2ACdwCaQ",
    "备用2号":"AIzaSyD4UdMp5wndOAKxtO1CWpzuZEGEf78YKUQ",
    "备用3号":"AIzaSyBVbA7tEyyy_ASp7l9P60qSh1xOM2CSMNw",
    "备用4号":"AIzaSyDezEpxvtY1AKN6JACMU9XHte5sxATNcUs",
    "备用5号":"AIzaSyBgyyy2kTTAdsLB53OCR2omEbj7zlx1mjw",
    "备用6号":"AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY",
    "备用7号":"AIzaSyDdyhqcowl0ftcbK9pMObXzM7cIOQMtlmA",
    "备用8号":"AIzaSyAA7Qs9Lzy4UxxIqCIQ4RknchiWQt_1hgI",
    "备用9号":"AIzaSyCj_CCwQua1mfq3EjzqV6Up6NHsxtb9dy8",
    "备用10号":"AIzaSyDOI2e-I1RdXBnk99jY2H00A3aymXREETA"
}

# --- 初始化 Session State ---
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]
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
if "reset_history" not in st.session_state:
    st.session_state.reset_history = False
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "rerun_count" not in st.session_state:
    st.session_state.rerun_count = 0
if "use_token" not in st.session_state:
    st.session_state.use_token = True
# ★★★ 新增/修改：状态锁初始化 ★★★
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "error_occurred" not in st.session_state:
    st.session_state.error_occurred = False # 新增错误状态标志

# --- 配置 API 密钥 (保持原样) ---
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# --- 模型设置 (保持原样) ---
generation_config = {
  "temperature": 1.6, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel(
  model_name="gemini-2.5-flash-preview-05-20",
  generation_config=generation_config,
  safety_settings=safety_settings,
  system_instruction="""
{
    "prompts": [
        {
            "name": "💮二选一💮强化身份定义—小说之弟", "system_prompt": true, "role": "system",
            "content": "<Writer_Activation>...</Writer_Activation>", # 内容保持不变，此处省略
            "identifier": "main", "forbid_overrides": true, "injection_position": 0, "injection_depth": 4
        }
    ]
}
""",
)

# --- 默认角色设定 (保持原样) ---
DEFAULT_CHARACTER_SETTINGS = {"理外祝福": """【理外祝福】的核心概念：\n\n"""}

# --- 文件操作函数 (保持原样) ---
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)
if not os.path.exists(log_file):
    with open(log_file, "wb") as f: pass

# --- 功能函数 (所有功能函数保持原样) ---
def generate_token():
    # ... (代码不变)
    import random
    import string
    random.seed()
    token_length = random.randint(10, 15)
    characters = "一乙二十丁厂七卜人入八九几儿了力乃刀又三于干亏士工土才寸下大丈与万上小口巾山千乞川亿个勺久凡及夕丸么广亡门义之尸弓己已子卫也女飞刃习叉马乡丰王井"
    hanzi_token = "".join(random.choice(characters) for _ in range(token_length - 1))
    probability = random.random()
    if probability < 0.4: digit_count = 1
    elif probability < 0.7: digit_count = 2
    else: digit_count = 3
    digit_token = "、".join(random.choice(string.digits) for _ in range(digit_count))
    return f"({hanzi_token})({digit_token})"

def load_history(log_file):
    # ... (代码不变)
    try:
        with open(log_file, "rb") as f: st.session_state.messages = pickle.load(f)
        st.success(f"成功读取历史记录！({os.path.basename(log_file)})")
        st.session_state.chat_session = None
        st.session_state.rerun_count += 1
    except (FileNotFoundError, EOFError, Exception) as e:
        st.warning(f"读取历史记录失败: {e}")

def clear_history(log_file):
    # ... (代码不变)
    st.session_state.messages.clear()
    st.session_state.chat_session = None
    if os.path.exists(log_file): os.remove(log_file)
    st.success("历史记录已清除！")

def ensure_enabled_settings_exists():
    # ... (代码不变)
    for setting_name in st.session_state.character_settings:
        if setting_name not in st.session_state.enabled_settings:
            st.session_state.enabled_settings[setting_name] = False
ensure_enabled_settings_exists()

def getAnswer(prompt):
    # ... (大部分代码不变, 省略内部构造)
    prompt = prompt or ""
    history_messages = []
    # ... 构建 history_messages 的逻辑保持不变 ...
    for msg in st.session_state.messages[-20:]:
        if msg and msg.get("role") and msg.get("content"):
            if msg["role"] == "user": history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant" and msg["content"] is not None: history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
    if prompt:
        history_messages.append({"role": "user", "parts": [{"text": prompt}]})
    response = model.generate_content(contents=history_messages, stream=True)
    yield from response

def regenerate_message(index):
    # ... (代码不变)
    if 0 <= index < len(st.session_state.messages):
        st.session_state.messages = st.session_state.messages[:index]
        new_prompt = "请重新写"
        st.session_state.messages.append({"role": "user", "content": new_prompt})
        st.session_state.is_generating = True
        st.experimental_rerun()
    else:
        st.error("无效的消息索引")

def continue_message(index):
    # ... (代码不变)
    if 0 <= index < len(st.session_state.messages):
        message_to_continue = st.session_state.messages[index]
        original_message_content = message_to_continue["content"]
        # ... (后续拼接和流式更新逻辑保持不变) ...
        # 此处省略，以保持简洁
        # 但它的核心逻辑被下面的“错误恢复”部分借鉴了
    else:
        st.error("无效的消息索引")

# --- UI 界面部分 (保持原样) ---
with st.sidebar:
    # ... (所有侧边栏代码保持不变，此处省略) ...
    st.session_state.selected_api_key = st.selectbox("选择 API Key:", options=list(API_KEYS.keys()), index=list(API_KEYS.keys()).index(st.session_state.selected_api_key), key="api_selector")
    genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])
    with st.expander("文件操作"): pass # 省略内部
    with st.expander("角色设定"): pass # 省略内部

# 自动加载历史记录
if not st.session_state.messages and not st.session_state.is_generating and not st.session_state.error_occurred:
    load_history(log_file)

# 显示历史记录和编辑功能 (保持原样)
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        message_placeholder = st.empty()
        message_placeholder.write(message["content"], key=f"message_{i}")
        st.session_state.messages[i]["placeholder_widget"] = message_placeholder

if st.session_state.get("editing"):
    # ... (编辑逻辑保持不变，此处省略) ...
    pass

# 最后一条消息下方的紧凑图标按钮 (保持原样)
if len(st.session_state.messages) >= 1 and not st.session_state.is_generating and not st.session_state.error_occurred:
    # ... (编辑/重生成/继续按钮逻辑保持不变，此处省略) ...
    pass

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★        核心交互逻辑 - 使用三段式状态机（输入/生成/错误）        ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

# 状态三：错误恢复模式
if st.session_state.get("error_occurred"):
    st.warning("生成被中断。您可以选择继续生成。")
    if st.button("继续生成 ...", key="continue_from_error"):
        # 进入这个块意味着用户点击了按钮，我们要开始恢复性生成
        last_message = st.session_state.messages[-1]
        original_content = last_message["content"]
        placeholder = last_message.get("placeholder_widget")

        with st.spinner("正在尝试继续生成..."):
            try:
                # 构造续写提示
                last_chars_length = 20
                last_chars = original_content[-last_chars_length:] if len(original_content) > last_chars_length else original_content
                continue_prompt = f"请务必从 '{last_chars}' 无缝衔接自然地继续写，不要重复，不要输出任何思考过程或道歉。"

                # 开始流式续写
                continued_response = ""
                response_stream = getAnswer(continue_prompt)
                for chunk in response_stream:
                    continued_response += chunk.text
                    updated_content = original_content + continued_response
                    if placeholder:
                        placeholder.markdown(updated_content + "▌")
                    st.session_state.messages[-1]["content"] = updated_content

                # 成功续写，重置状态
                st.session_state.error_occurred = False

            except Exception as e:
                # 如果续写再次失败，停留在错误状态，让用户可以再次尝试
                st.error(f"继续生成时再次发生错误: {type(e).__name__} - {e}")
                # 不需要改变状态，UI会刷新，按钮依然可见

            finally:
                # 无论续写是否成功，都保存当前记录
                with open(log_file, "wb") as f:
                    messages_to_pickle = [msg.copy() for msg in st.session_state.messages]
                    for msg in messages_to_pickle:
                        msg.pop("placeholder_widget", None)
                    pickle.dump(messages_to_pickle, f)
                
                # 触发刷新来更新UI状态
                st.experimental_rerun()


# 状态二：正在生成模式
elif st.session_state.is_generating:
    last_user_prompt = st.session_state.messages[-2]["content"] # 获取真正的用户输入
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        st.session_state.messages[-1]["placeholder_widget"] = message_placeholder
        full_response = ""
        try:
            response_stream = getAnswer(last_user_prompt)
            for chunk in response_stream:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
                st.session_state.messages[-1]["content"] = full_response
            message_placeholder.markdown(full_response)
            st.session_state.is_generating = False # 正常结束，解除生成锁定

        except Exception as e:
            # ★★★ 关键改动：发生错误时，不结束流程，而是转换到“错误恢复”状态 ★★★
            st.session_state.is_generating = False
            st.session_state.error_occurred = True
            st.error(f"生成被中断: {type(e).__name__} - {e}。部分回复已保存。")

        finally:
            # 无论如何都保存一次文件
            with open(log_file, "wb") as f:
                messages_to_pickle = [msg.copy() for msg in st.session_state.messages]
                for msg in messages_to_pickle:
                    msg.pop("placeholder_widget", None)
                pickle.dump(messages_to_pickle, f)
            # 刷新以根据新状态（is_generating=False, error_occurred=True/False）更新UI
            st.experimental_rerun()

# 状态一：等待输入模式 (默认)
else:
    if prompt := st.chat_input("输入你的消息:", key="main_chat_input"):
        token = generate_token()
        full_prompt = f"{prompt} (token: {token})" if st.session_state.use_token else prompt
        
        # 显示并保存用户消息
        with st.chat_message("user"):
            st.markdown(full_prompt)
        st.session_state.messages.append({"role": "user", "content": full_prompt})
        # 为AI的回复预先占位
        st.session_state.messages.append({"role": "assistant", "content": ""})

        # 锁定状态并刷新，进入“生成中”模式
        st.session_state.is_generating = True
        st.experimental_rerun()

# --- 底部控件 (保持原样) ---
col1, col2 = st.columns(2)
with col1:
    st.checkbox("使用 Token", value=st.session_state.use_token, key="token_checkbox_controller")
    st.session_state.use_token = st.session_state.token_checkbox_controller
with col2:
    if st.button("🔄", key="refresh_button"):
        st.experimental_rerun()
