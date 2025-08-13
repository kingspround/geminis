import os
import google.generativeai as genai
import streamlit as st
import pickle
import random
import string
from datetime import datetime
from io import BytesIO
import zipfile
from PIL import Image

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Gemini Chatbot with Vision",
    layout="wide"
)

# --- API 密钥设置 ---
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
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'editable_index' not in st.session_state:
    st.session_state.editable_index = -1
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "sidebar_caption" not in st.session_state:
    st.session_state.sidebar_caption = ""
if "use_token" not in st.session_state:
    st.session_state.use_token = True


# --- API配置和模型定义 ---
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])
generation_config = {
  "temperature": 1.0, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-latest",
  generation_config=generation_config,
  safety_settings=safety_settings,
  system_instruction="""
{
 "<Writer_Activation>...</Writer_Activation>",
 "<System_Instruction>...</System_Instruction>",
 "扮演角色：...<core_principles>...</core_principles>\n\",",
}
""",
)

# --- 默认角色设定 ---
DEFAULT_CHARACTER_SETTINGS = { "理外祝福": """【理外祝福】的核心概念：\n\n""" }

# --- 文件操作与功能函数 ---
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)
if not os.path.exists(log_file):
    with open(log_file, "wb") as f: pass
def _prepare_messages_for_save(messages):
    picklable_messages = []
    for msg in messages:
        new_msg = msg.copy(); new_content_list = []
        if isinstance(new_msg.get("content"), list):
            for part in new_msg["content"]:
                if isinstance(part, Image.Image):
                    buffered = BytesIO(); part.save(buffered, format="PNG")
                    new_content_list.append({"type": "image", "data": buffered.getvalue()})
                else: new_content_list.append(part)
            new_msg["content"] = new_content_list
        new_msg.pop("placeholder_widget", None)
        picklable_messages.append(new_msg)
    return picklable_messages
def _reconstitute_messages_after_load(messages):
    reconstituted_messages = []
    for msg in messages:
        new_msg = msg.copy(); content = new_msg.get("content"); new_content = []
        if isinstance(content, str): new_msg["content"] = [content]; reconstituted_messages.append(new_msg); continue
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image":
                    try: new_content.append(Image.open(BytesIO(part["data"])))
                    except Exception as e: new_content.append(f"[图片加载失败: {e}]")
                else: new_content.append(part)
            new_msg["content"] = new_content
        reconstituted_messages.append(new_msg)
    return reconstituted_messages
def generate_token():
    import random; import string; random.seed(); token_length = random.randint(10, 15)
    characters = "一乙二十丁厂七卜人入八"
    hanzi_token = "".join(random.choice(characters) for _ in range(token_length - 1))
    probability = random.random()
    if probability < 0.4: digit_count = 1
    elif probability < 0.7: digit_count = 2
    else: digit_count = 3
    digit_token = "、".join(random.choice(string.digits) for _ in range(digit_count))
    return f"({hanzi_token})({digit_token})"
def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            data = pickle.load(f)
            if isinstance(data, list): st.session_state.messages = _reconstitute_messages_after_load(data)
        st.session_state.chat_session = None
    except FileNotFoundError: pass
    except Exception as e: st.error(f"读取历史记录失败：{e}")
def clear_history(log_file):
    st.session_state.messages.clear(); st.session_state.chat_session = None
    if os.path.exists(log_file): os.remove(log_file)
    st.success("历史记录已清除！")
def ensure_enabled_settings_exists():
    for setting_name in st.session_state.character_settings:
        if setting_name not in st.session_state.enabled_settings: st.session_state.enabled_settings[setting_name] = False
ensure_enabled_settings_exists()
def getAnswer():
    # 这个函数现在只负责发送历史记录和获取流式响应
    history_messages = []
    # 从session_state构建API需要的历史记录格式
    for msg in st.session_state.messages[-20:]: # 使用最近20条消息
        if msg and msg.get("role") and msg.get("content"):
            api_role = "model" if msg["role"] == "assistant" else "user"
            history_messages.append({"role": api_role, "parts": msg["content"]})
    
    # 最后一个是AI的空消息，不应该发给API
    if history_messages and history_messages[-1]['role'] == 'model' and not history_messages[-1]['parts'][0]:
        history_messages.pop()

    response = model.generate_content(contents=history_messages, stream=True)
    for chunk in response: 
        yield chunk.text

def regenerate_message(index):
    # 重新生成：移除旧的AI回复，然后触发生成流程
    if 0 <= index < len(st.session_state.messages) and st.session_state.messages[index]["role"] == "assistant":
        st.session_state.messages = st.session_state.messages[:index]
        st.session_state.is_generating = True
        st.experimental_rerun()
def continue_message(index):
    # 继续生成：在现有内容上继续，通过特殊prompt指导AI
    if 0 <= index < len(st.session_state.messages):
        # 标记我们需要继续这条消息，但不直接在这里生成
        # 主生成逻辑会处理它
        st.session_state.messages.append({"role": "user", "content": ["[continue]"]}) # 特殊指令
        st.session_state.is_generating = True
        st.experimental_rerun()

def send_from_sidebar_callback():
    uploaded_files = st.session_state.get("sidebar_uploader", [])
    caption = st.session_state.get("sidebar_caption", "").strip()
    if not uploaded_files and not caption:
        st.toast("请输入文字或上传图片！", icon="⚠️"); return
    content_parts = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try: content_parts.append(Image.open(uploaded_file))
            except Exception as e: st.error(f"处理图片 {uploaded_file.name} 失败: {e}")
    if caption: content_parts.append(caption)
    if content_parts:
        st.session_state.messages.append({"role": "user", "content": content_parts})
        st.session_state.sidebar_caption = ""
        st.session_state.is_generating = True

# --- UI 侧边栏 ---
with st.sidebar:
    st.session_state.selected_api_key = st.selectbox("选择 API Key:", options=list(API_KEYS.keys()), index=list(API_KEYS.keys()).index(st.session_state.selected_api_key), key="api_selector")
    genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])
    
    with st.expander("文件操作"):
        if len(st.session_state.messages) > 0: st.button("重置上一个输出 ⏪", on_click=lambda: st.session_state.messages.pop(-1))
        st.button("读取历史记录 📖", on_click=lambda: load_history(log_file))
        if st.button("清除历史记录 🗑️"): st.session_state.clear_confirmation = True
        if st.session_state.get("clear_confirmation"):
            c1, c2 = st.columns(2)
            if c1.button("确认清除", key="clear_confirm"): clear_history(log_file); st.session_state.clear_confirmation = False; st.experimental_rerun()
            if c2.button("取消", key="clear_cancel"): st.session_state.clear_confirmation = False
        st.download_button("下载当前聊天记录 ⬇️", data=pickle.dumps(_prepare_messages_for_save(st.session_state.messages)), file_name=os.path.basename(log_file), mime="application/octet-stream")
        
        uploaded_pkl = st.file_uploader("读取本地pkl文件 📁", type=["pkl"], key="pkl_uploader")
        if uploaded_pkl is not None:
            try:
                st.session_state.messages = _reconstitute_messages_after_load(pickle.load(uploaded_pkl))
                st.success("成功读取本地pkl文件！"); st.experimental_rerun()
            except Exception as e: st.error(f"读取本地pkl文件失败：{e}")

    with st.expander("发送图片与文字"):
        st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="sidebar_uploader", label_visibility="collapsed")
        st.text_area("输入文字 (可选)", key="sidebar_caption", height=100)
        st.button("发送到对话 ↗️", on_click=send_from_sidebar_callback, use_container_width=True)

    with st.expander("角色设定"):
        uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt) 📝", type=["txt"], key="setting_uploader")
        if uploaded_setting_file is not None:
            try:
                setting_name = os.path.splitext(uploaded_setting_file.name)[0]
                content = uploaded_setting_file.read().decode("utf-8")
                st.session_state.character_settings[setting_name] = content
                st.session_state.enabled_settings[setting_name] = False
                st.experimental_rerun()
            except Exception as e: st.error(f"读取文件失败: {e}")
        for name in DEFAULT_CHARACTER_SETTINGS:
            if name not in st.session_state.character_settings: st.session_state.character_settings[name] = DEFAULT_CHARACTER_SETTINGS[name]
            st.session_state.enabled_settings[name] = st.checkbox(name, st.session_state.enabled_settings.get(name, False), key=f"cb_{name}")
        st.session_state.test_text = st.text_area("System Message (Optional):", st.session_state.get("test_text", ""), key="system_msg")
        enabled_list = [name for name, enabled in st.session_state.enabled_settings.items() if enabled]
        if enabled_list: st.write("已加载设定:", ", ".join(enabled_list))
        if st.button("刷新 🔄", key="sidebar_refresh"): st.experimental_rerun()

# --- 加载和显示聊天记录 ---
if not st.session_state.messages and not st.session_state.is_generating: load_history(log_file)
for i, message in enumerate(st.session_state.messages):
    # 跳过我们内部使用的特殊指令
    if message.get("content") == ["[continue]"]:
        continue
    with st.chat_message(message["role"]):
        for part in message.get("content", []):
            if isinstance(part, str): st.markdown(part, unsafe_allow_html=True)
            elif isinstance(part, Image.Image): st.image(part, width=400)

# --- 编辑界面显示逻辑 ---
if st.session_state.get("editing"):
    i = st.session_state.editable_index
    message = st.session_state.messages[i]
    with st.chat_message(message["role"]):
        current_text = message["content"][0] if message["content"] and isinstance(message["content"][0], str) else ""
        new_text = st.text_area(f"编辑 {message['role']} 的消息:", current_text, key=f"edit_area_{i}")
        c1, c2 = st.columns(2)
        if c1.button("保存 ✅", key=f"save_{i}"):
            st.session_state.messages[i]["content"][0] = new_text
            with open(log_file, "wb") as f: pickle.dump(_prepare_messages_for_save(st.session_state.messages), f)
            st.session_state.editing = False; st.experimental_rerun()
        if c2.button("取消 ❌", key=f"cancel_{i}"):
            st.session_state.editing = False; st.experimental_rerun()

# --- 续写/编辑/重生成按钮逻辑 ---
if len(st.session_state.messages) >= 1 and not st.session_state.is_generating and not st.session_state.editing:
    # 找到最后一个要显示的消息的索引
    display_indices = [i for i, msg in enumerate(st.session_state.messages) if msg.get("content") != ["[continue]"]]
    if display_indices:
        last_idx = display_indices[-1]
        last_msg = st.session_state.messages[last_idx]
        is_text_only_assistant = (last_msg["role"] == "assistant" and len(last_msg.get("content", [])) == 1 and isinstance(last_msg["content"][0], str))
        
        if is_text_only_assistant:
            with st.container():
                cols = st.columns(20)
                if cols[0].button("✏️", key=f"edit_{last_idx}", help="编辑"): st.session_state.editable_index = last_idx; st.session_state.editing = True; st.experimental_rerun()
                if cols[1].button("♻️", key=f"regen_{last_idx}", help="重新生成"): regenerate_message(last_idx)
                if cols[2].button("➕", key=f"cont_{last_idx}", help="继续"): continue_message(last_idx) # 使用新的 continue 逻辑
        elif last_msg["role"] == "assistant":
             if st.columns(20)[0].button("♻️", key=f"regen_vision_{last_idx}", help="重新生成"): regenerate_message(last_idx)

# --- 核心交互逻辑 (主输入框) ---
if not st.session_state.is_generating:
    if prompt := st.chat_input("输入你的消息...", key="main_chat_input", disabled=st.session_state.editing):
        token = generate_token()
        full_prompt = f"{prompt} (token: {token})" if st.session_state.use_token else prompt
        st.session_state.messages.append({"role": "user", "content": [full_prompt]})
        st.session_state.is_generating = True
        st.experimental_rerun()

# --- 核心生成逻辑 (已彻底修复部分生成问题) ---
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        placeholder = st.empty()

        # 1. 确保我们有一个 assistant 消息可以写入
        if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
            # 我们只添加一个空的占位符，内容将在下面填充
            st.session_state.messages.append({"role": "assistant", "content": [""]})

        # 2. 从 session_state 中获取当前正在构建的消息
        # 这是关键：我们直接操作永久状态，而不是临时变量
        message_index_to_update = len(st.session_state.messages) - 1
        
        try:
            # 3. 流式获取并“即收即存”
            response_stream = getAnswer()
            for chunk in response_stream:
                # ★★★ 核心修复点 ★★★
                # 直接将新块附加到 session_state 中的消息内容上
                st.session_state.messages[message_index_to_update]["content"][0] += chunk
                
                # 更新UI显示
                current_content = st.session_state.messages[message_index_to_update]["content"][0]
                placeholder.markdown(current_content + "▌")
            
            # 成功完成后，移除光标
            final_content = st.session_state.messages[message_index_to_update]["content"][0]
            placeholder.markdown(final_content)

        except Exception as e:
            # 4. 如果发生错误
            # UI上显示错误信息
            st.error(f"回答生成中断: {type(e).__name__}。已保存部分内容，可尝试【继续】或【重新生成】。")
            # 确保UI上显示的是最后保存的内容（无光标）
            final_partial_content = st.session_state.messages[message_index_to_update]["content"][0]
            placeholder.markdown(final_partial_content)

        finally:
            # 5. 无论成功与否，都执行收尾工作
            # 确保空消息不被保存
            if st.session_state.messages and not st.session_state.messages[-1]["content"][0].strip():
                st.session_state.messages.pop()
            
            # 将最终状态（无论是完整的还是部分的）保存到文件
            with open(log_file, "wb") as f:
                pickle.dump(_prepare_messages_for_save(st.session_state.messages), f)
            
            # 结束生成状态并刷新
            st.session_state.is_generating = False
            st.experimental_rerun()


# --- 底部控件 ---
c1, c2 = st.columns(2)
st.session_state.use_token = c1.checkbox("使用 Token", value=st.session_state.get("use_token", True))
if c2.button("🔄", key="page_refresh", help="刷新页面"): st.experimental_rerun()
