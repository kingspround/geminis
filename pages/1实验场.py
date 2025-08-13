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

# --- 初始化 Session State (增加一个状态) ---
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'editing' not in st.session_state:
    st.session_state.editing = False
if 'editable_index' not in st.session_state:
    st.session_state.editable_index = -1
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "use_token" not in st.session_state:
    st.session_state.use_token = True
# ★★★ 新增状态，用于标记是否为“继续生成”任务 ★★★
if "is_continuing" not in st.session_state:
    st.session_state.is_continuing = False
# (其他 session state 初始化保持不变)
if 'character_settings' not in st.session_state:
    st.session_state.character_settings = {}
if 'enabled_settings' not in st.session_state:
    st.session_state.enabled_settings = {}
if "sidebar_caption" not in st.session_state:
    st.session_state.sidebar_caption = ""
if "clear_confirmation" not in st.session_state:
    st.session_state.clear_confirmation = False

# --- API配置和模型定义 (保持不变) ---
# ... (此部分代码完全不变)
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
DEFAULT_CHARACTER_SETTINGS = { "理外祝福": """【理外祝福】的核心概念：\n\n""" }


# --- 文件操作与功能函数 (删除了 continue_message) ---
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)
if not os.path.exists(log_file):
    with open(log_file, "wb") as f: pass
def _prepare_messages_for_save(messages):
    #... (此函数不变)
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
    #... (此函数不变)
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
    #... (此函数不变)
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
    #... (此函数不变)
    try:
        with open(log_file, "rb") as f:
            data = pickle.load(f)
            if isinstance(data, list): st.session_state.messages = _reconstitute_messages_after_load(data)
    except FileNotFoundError: pass
    except Exception as e: st.error(f"读取历史记录失败：{e}")
def clear_history(log_file):
    #... (此函数不变)
    st.session_state.messages.clear()
    if os.path.exists(log_file): os.remove(log_file)
    st.success("历史记录已清除！")
def regenerate_message(index):
    #... (此函数不变)
    if 0 <= index < len(st.session_state.messages) and st.session_state.messages[index]["role"] == "assistant":
        st.session_state.messages = st.session_state.messages[:index]
        st.session_state.is_generating = True
        st.experimental_rerun()

# ★★★ 新的“继续”按钮回调函数，非常简单 ★★★
def start_continuation():
    """标记一个“继续”任务，并启动生成流程"""
    st.session_state.is_continuing = True
    st.session_state.is_generating = True

def send_from_sidebar_callback():
    #... (此函数不变)
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
        st.session_state.is_generating = True


# --- UI 侧边栏 (保持不变) ---
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
            if c2.button("取消", key="clear_cancel"): st.session_state.clear_confirmation = False; st.experimental_rerun()
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
        # ... (此部分代码完全不变)
        pass # Placeholder for brevity, the original code is fine

# --- 加载和显示聊天记录 (保持不变) ---
if not st.session_state.messages and not st.session_state.is_generating: load_history(log_file)
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # ... (此部分代码完全不变)
        for part in message.get("content", []):
            if isinstance(part, str): st.markdown(part, unsafe_allow_html=True)
            elif isinstance(part, Image.Image): st.image(part, width=400)


# --- 编辑界面显示逻辑 (保持不变) ---
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

# --- 续写/编辑/重生成按钮逻辑 (修改了“继续”按钮的回调) ---
if len(st.session_state.messages) >= 1 and not st.session_state.is_generating and not st.session_state.editing:
    last_idx = len(st.session_state.messages) - 1
    last_msg = st.session_state.messages[last_idx]
    is_text_only_assistant = (last_msg["role"] == "assistant" and len(last_msg.get("content", [])) == 1 and isinstance(last_msg["content"][0], str))
    
    if is_text_only_assistant:
        with st.container():
            cols = st.columns(20)
            if cols[0].button("✏️", key="edit", help="编辑"): st.session_state.editable_index = last_idx; st.session_state.editing = True; st.experimental_rerun()
            if cols[1].button("♻️", key="regen", help="重新生成"): regenerate_message(last_idx)
            # ★★★ 修改了这里的 on_click ★★★
            if cols[2].button("➕", key="cont", help="继续", on_click=start_continuation):
                pass # on_click handles the logic, no need for code here
    elif last_msg["role"] == "assistant":
         if st.columns(20)[0].button("♻️", key="regen_vision", help="重新生成"): regenerate_message(last_idx)

# --- 核心交互逻辑 (主输入框, 保持不变) ---
if not st.session_state.is_generating:
    if prompt := st.chat_input("输入你的消息...", key="main_chat_input", disabled=st.session_state.editing):
        token = generate_token()
        full_prompt = f"{prompt} (token: {token})" if st.session_state.use_token else prompt
        st.session_state.messages.append({"role": "user", "content": [full_prompt]})
        st.session_state.is_generating = True
        st.experimental_rerun()

# ★★★★★ 全新重构的核心生成逻辑 ★★★★★
if st.session_state.is_generating:
    # --- 1. 准备工作 ---
    # 如果是新对话，而不是继续，则添加一个空的助手消息位
    if not st.session_state.is_continuing:
        st.session_state.messages.append({"role": "assistant", "content": [""]})

    # 定位到我们当前要操作的助手消息（总是最后一条）
    assistant_message = st.session_state.messages[-1]
    # 保存已经存在的内容（对于“继续”任务，这里会有内容；对于新任务，这里是空字符串）
    existing_content = assistant_message["content"][0]

    # --- 2. 构建发送给API的历史记录 ---
    history_to_send = [{"role": ("model" if m["role"] == "assistant" else "user"), "parts": m["content"]} for m in st.session_state.messages]
    
    # 如果是“继续”任务，额外添加一条指令，告诉AI如何继续
    if st.session_state.is_continuing:
        last_chars = (existing_content[-50:] + "...") if len(existing_content) > 50 else existing_content
        continuation_prompt = f"请从下面的文本无缝衔接，自然地继续写下去，不要重复内容，也不要包含任何解释性文字或标记。直接开始写正文即可。文本片段：'{last_chars}'"
        history_to_send.append({"role": "user", "parts": [continuation_point]})

    # --- 3. 执行生成与显示 ---
    with st.chat_message("assistant"):
        placeholder = st.empty()
        # 立即显示已有的内容
        placeholder.markdown(existing_content + "▌")
        
        full_response = ""
        try:
            # 调用API
            response = model.generate_content(contents=history_to_send, stream=True)
            for chunk in response:
                full_response += chunk.text
                # ★ 关键：在已有内容的基础上追加新生成的内容 ★
                assistant_message["content"][0] = existing_content + full_response
                placeholder.markdown(assistant_message["content"][0] + "▌")

            # 显示最终结果
            placeholder.markdown(assistant_message["content"][0])

        except Exception as e:
            err_msg = f"**回答生成中断**: {type(e).__name__}。内容已保存，您可再次尝试【继续】或【重新生成】。"
            st.error(err_msg)
            # 即使出错，也显示已经生成的部分
            placeholder.markdown(assistant_message["content"][0])
        
        finally:
            # --- 4. 清理和保存 ---
            # 重置状态标记
            st.session_state.is_generating = False
            st.session_state.is_continuing = False
            
            # 保存聊天记录到文件
            if assistant_message["content"][0].strip(): # 确保不是空消息
                 with open(log_file, "wb") as f:
                    pickle.dump(_prepare_messages_for_save(st.session_state.messages), f)
            else: # 如果助手消息是空的，就移除它
                st.session_state.messages.pop()

            # 刷新页面
            st.experimental_rerun()

# --- 底部控件 (保持不变) ---
c1, c2 = st.columns(2)
st.session_state.use_token = c1.checkbox("使用 Token", value=st.session_state.get("use_token", True))
if c2.button("🔄", key="page_refresh", help="刷新页面"): st.experimental_rerun()
