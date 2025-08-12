import os
import google.generativeai as genai
import streamlit as st
import pickle
import random
import string
from io import BytesIO
from PIL import Image

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Gemini Chatbot with Vision",
    layout="wide"
)

# --- API 密钥设置 (保持不变) ---
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

# --- 初始化 Session State (保持不变) ---
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'character_settings' not in st.session_state:
    st.session_state.character_settings = {}
if 'enabled_settings' not in st.session_state:
    st.session_state.enabled_settings = {}
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "use_token" not in st.session_state:
    st.session_state.use_token = True
# ... 其他 session state 保持不变 ...

# --- API配置和模型定义 (保持不变) ---
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])
generation_config = { "temperature": 1.0, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192, "response_mime_type": "text/plain" }
safety_settings = [ {"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"] ]
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""(您的超长system_instruction在此处保持不变)"""
)
# --- 默认角色设定 (保持不变) ---
DEFAULT_CHARACTER_SETTINGS = { "理外祝福": """【理外祝福】的核心概念：\n\n""" }

# --- 文件操作与功能函数 (保持不变, 但send_images_to_chat是新的) ---
file, filename = os.path.abspath(__file__), os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)
if not os.path.exists(log_file):
    with open(log_file, "wb") as f: pass

def _prepare_messages_for_save(messages):
    # 此函数逻辑不变
    picklable_messages = []
    for msg in messages:
        new_msg = msg.copy()
        if isinstance(new_msg.get("content"), list):
            new_content = []
            for part in new_msg["content"]:
                if isinstance(part, Image.Image):
                    with BytesIO() as buffered:
                        part.save(buffered, format="PNG")
                        img_bytes = buffered.getvalue()
                    new_content.append({"type": "image", "data": img_bytes, "format": "PNG"})
                else: new_content.append(part)
            new_msg["content"] = new_content
        new_msg.pop("placeholder_widget", None)
        picklable_messages.append(new_msg)
    return picklable_messages

def _reconstitute_messages_after_load(messages):
    # 此函数逻辑不变
    reconstituted_messages = []
    for msg in messages:
        new_msg = msg.copy()
        content = new_msg.get("content")
        if isinstance(content, str): new_msg["content"] = [content]
        elif isinstance(content, list):
            new_content = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image":
                    try: new_content.append(Image.open(BytesIO(part["data"])))
                    except Exception as e: new_content.append(f"[图片加载失败: {e}]")
                else: new_content.append(part)
            new_msg["content"] = new_content
        reconstituted_messages.append(new_msg)
    return reconstituted_messages

def generate_token():
    # 此函数逻辑不变
    random.seed()
    token_length = random.randint(10, 15)
    characters = "一乙二十丁厂七卜人入八"
    hanzi_token = "".join(random.choice(characters) for _ in range(token_length - 1))
    probability = random.random()
    digit_count = 1 if probability < 0.4 else 2 if probability < 0.7 else 3
    digit_token = "、".join(random.choice(string.digits) for _ in range(digit_count))
    return f"({hanzi_token})({digit_token})"

def load_history(log_file):
    try:
        if os.path.exists(log_file):
            with open(log_file, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    st.session_state.messages = _reconstitute_messages_after_load(data)
    except Exception as e: st.error(f"读取历史记录失败：{e}")

def clear_history(log_file):
    st.session_state.messages.clear()
    if os.path.exists(log_file): os.remove(log_file)
    st.success("历史记录已清除！")

def ensure_enabled_settings_exists():
    for setting_name in st.session_state.character_settings:
        if setting_name not in st.session_state.enabled_settings:
            st.session_state.enabled_settings[setting_name] = False
ensure_enabled_settings_exists()

def getAnswer():
    # 此函数逻辑不变
    history_messages = []
    fixed_prompt = {"role": "user", "parts": [{"text": """(您的超长Creative_Requirements在此处保持不变)"""}]}
    history_messages.extend([{"role": "model", "parts":[{"text": "\n\n"}]}, fixed_prompt])
    for msg in st.session_state.messages[-20:]:
      if msg and msg.get("role") and msg.get("content"):
          history_messages.append({"role": "model" if msg["role"] == "assistant" else "user", "parts": msg["content"]})
    if any(st.session_state.enabled_settings.values()):
        enabled_content = "```system\n# Active Settings:\n" + "".join(f"- {name}: {st.session_state.character_settings[name]}\n" for name, enabled in st.session_state.enabled_settings.items() if enabled) + "```\n"
        history_messages.append({"role": "user", "parts": [enabled_content]})
    final_contents = [msg for msg in history_messages if msg.get("parts")]
    response = model.generate_content(contents=final_contents, stream=True)
    for chunk in response: yield chunk.text

def regenerate_message(index):
    if 0 <= index < len(st.session_state.messages) and st.session_state.messages[index]["role"] == "assistant":
        st.session_state.messages = st.session_state.messages[:index]
        st.session_state.is_generating = True
        st.experimental_rerun()

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★ 已修正的、无报错的回调函数 ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
def send_images_to_chat():
    """
    处理侧边栏图片上传并发送到聊天记录的回调函数。
    此函数在 on_click 中被调用，可以安全地修改 session_state。
    """
    # 1. 从 session_state 中获取上传的文件列表
    uploaded_files = st.session_state.get("sidebar_image_uploader", [])
    if not uploaded_files:
        st.warning("请先上传图片再发送。")
        return

    # 2. 将上传的文件转换为 PIL Image 对象
    image_parts = []
    for uploaded_file in uploaded_files:
        try:
            image_parts.append(Image.open(uploaded_file))
        except Exception as e:
            st.error(f"处理图片 {uploaded_file.name} 失败: {e}")
            return # 如果有文件处理失败，则中止

    # 3. 如果成功处理了至少一张图片，就创建一条新消息
    if image_parts:
        st.session_state.messages.append({"role": "user", "content": image_parts})
        st.success(f"已将 {len(image_parts)} 张图片添加到对话中！")

        # 4. ★★★ 关键修复 ★★★
        # 删除 session_state 中与 file_uploader 关联的键。
        # 这是强制重置 file_uploader 的唯一正确方法，可避免 StreamlitAPIException。
        # 此操作必须在回调函数内部完成。
        if 'sidebar_image_uploader' in st.session_state:
            del st.session_state['sidebar_image_uploader']

# --- UI 侧边栏 ---
with st.sidebar:
    st.session_state.selected_api_key = st.selectbox("选择 API Key:", options=list(API_KEYS.keys()), index=list(API_KEYS.keys()).index(st.session_state.selected_api_key), key="api_selector")
    genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

    with st.expander("文件操作", expanded=True):
        if st.button("清除历史记录 🗑️", use_container_width=True): st.session_state.clear_confirmation = True
        if st.session_state.get("clear_confirmation"):
            c1, c2 = st.columns(2)
            if c1.button("确认清除", key="clear_confirm"): clear_history(log_file); st.session_state.clear_confirmation = False; st.experimental_rerun()
            if c2.button("取消", key="clear_cancel"): st.session_state.clear_confirmation = False
        st.download_button("下载聊天记录 ⬇️", pickle.dumps(_prepare_messages_for_save(st.session_state.messages)), os.path.basename(log_file), "application/octet-stream", use_container_width=True)
        uploaded_pkl = st.file_uploader("读取pkl文件 📁", type=["pkl"], key="pkl_uploader")
        if uploaded_pkl:
            try:
                st.session_state.messages = _reconstitute_messages_after_load(pickle.load(uploaded_pkl))
                st.success("成功读取pkl文件！"); st.experimental_rerun()
            except Exception as e: st.error(f"读取pkl文件失败：{e}")
        
        # --- 图片发送功能 ---
        st.markdown("---")
        st.markdown("**发送图片到对话**")
        st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="sidebar_image_uploader", label_visibility="collapsed")
        
        # ★★★ 修正后的按钮，使用 on_click ★★★
        st.button("发送图片到对话 ↗️", use_container_width=True, on_click=send_images_to_chat, key="send_images_button")

    with st.expander("角色设定"):
        # 角色设定模块已恢复
        uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt) 📝", type=["txt"])
        if uploaded_setting_file:
            try:
                name, content = os.path.splitext(uploaded_setting_file.name)[0], uploaded_setting_file.read().decode("utf-8")
                st.session_state.character_settings[name] = content
                st.session_state.enabled_settings[name] = False
                st.experimental_rerun()
            except Exception as e: st.error(f"读取文件失败: {e}")
        for name in DEFAULT_CHARACTER_SETTINGS:
            if name not in st.session_state.character_settings:
                st.session_state.character_settings[name] = DEFAULT_CHARACTER_SETTINGS[name]
            st.session_state.enabled_settings[name] = st.checkbox(name, st.session_state.enabled_settings.get(name, False), key=f"cb_{name}")
        st.session_state.test_text = st.text_area("System Message (Optional):", st.session_state.get("test_text", ""), key="system_message")
        if any(st.session_state.enabled_settings.values()):
            st.write("已加载设定:", ", ".join([name for name, enabled in st.session_state.enabled_settings.items() if enabled]))
        if st.button("刷新 🔄", key="sidebar_refresh", use_container_width=True): st.experimental_rerun()

# --- 加载和显示聊天记录 ---
if not st.session_state.messages and not st.session_state.is_generating:
    load_history(log_file)

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        for part in message.get("content", []):
            if isinstance(part, str): st.markdown(part, unsafe_allow_html=True)
            elif isinstance(part, Image.Image): st.image(part, width=400)

# --- 续写/重生成按钮逻辑 ---
if len(st.session_state.messages) >= 1 and not st.session_state.is_generating:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        with st.container():
            cols = st.columns(20)
            cols[0].button("♻️", key=f"regen_{len(st.session_state.messages)}", help="重新生成", use_container_width=True, on_click=regenerate_message, args=(len(st.session_state.messages) - 1,))

# --- 核心交互逻辑 ---
if not st.session_state.is_generating:
    if prompt := st.chat_input("输入你的消息...", key="main_chat_input"):
        st.session_state.messages.append({"role": "user", "content": [f"{prompt} (token: {generate_token()})" if st.session_state.use_token else prompt]})
        st.session_state.is_generating = True
        st.experimental_rerun()

# --- 核心生成逻辑 ---
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        placeholder = st.empty()
        if st.session_state.messages[-1]["role"] != "assistant":
            st.session_state.messages.append({"role": "assistant", "content": [""]})
        full_response = ""
        try:
            for chunk in getAnswer():
                full_response += chunk
                st.session_state.messages[-1]["content"][0] = full_response
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            error_msg = f"\n\n**发生错误**: {type(e).__name__} - {e}"
            placeholder.error(error_msg.strip())
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                 st.session_state.messages[-1]["content"][0] += error_msg
        finally:
            if st.session_state.messages and not st.session_state.messages[-1].get("content", [""])[0].strip():
                st.session_state.messages.pop()
            with open(log_file, "wb") as f:
                pickle.dump(_prepare_messages_for_save(st.session_state.messages), f)
            st.session_state.is_generating = False
            st.experimental_rerun()

# --- 底部控件 ---
c1, c2 = st.columns([1, 8])
st.session_state.use_token = c1.checkbox("Token", value=st.session_state.use_token, key="token_cb", help="在提问时附加随机Token")
if c2.button("🔄", key="main_refresh", help="刷新页面"):
    st.experimental_rerun()
