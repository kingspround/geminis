import os
import google.generativeai as genai
import streamlit as st
import pickle
from io import BytesIO
from PIL import Image

# ==============================================================================
# 1. 所有常量定义 (Constants)
# ==============================================================================

# --- API 密钥设置 ---
# 【请在这里填入您的API Keys】
API_KEYS = {
    "04 1号20270168962": "AIzaSyDGjLL0nJWkqDYj2KDWJdAh3zPwLPmIA_E",
    "04 2号371111309083": "AIzaSyAQIz1pb84NzSzDwbtM2vB04zhLw8zVqdA",
    "04 3号622662315859":"AIzaSyD9JGoGhibXPWdNmpcfmrqZ-zxpEyg67EQ",
	"04 5号375090949096":"AIzaSyCLuGSiCE-3lxciVRiD28aBBFROMPoFU3M",
	"04 6号340384272853":"AIzaSyDp6qJunrZ37Nc9ucbItUJB-L8lYXDdGgs",
	"04 7号371111309083":"AIzaSyAQIz1pb84NzSzDwbtM2vB04zhLw8zVqdA",
	
    "1 1号799638464939":"AIzaSyA5fPQo1F4qlywciLyZQknpCq0ScuOTpv4",
	
    "2 1号866575601521":"AIzaSyD9_DVaXprbjlM6pqhbcpznrOPYib_OLcc",
	"2 3号961280537667":"AIzaSyClCCaPvJ8uqM23fQ_ZxpbA_EqA4g1i2V8",

	"01 1号227514221200":"AIzaSyBTyNjfDMw5tX5kOMi9i3g9OOnwDovMtQI",
	
	"02 1号163679758614":"AIzaSyCEoSXnALUnxMSvWpK4AWYre99mxNydKZY",

	"03 1号702122391294":"AIzaSyBQodu9EWd8VlLteNTiL0pXfSDPI_WobHI",

	"05 1号668014237032":"AIzaSyAMR-NyB5TA2IFzJr1sgdvCqrpSBIzkkdI",
	"05 2号851244762061":"AIzaSyAV6awcQC4NUQaX241EM72zxsGdwSEFMm0",
	
}

# --- 模型配置 ---
MODELS = {
    "gemini-2.5-flash-preview-05-20 (默认)": "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-pro": "gemini-2.5-pro",
}
DEFAULT_MODEL_NAME = "gemini-2.5-flash-preview-05-20 (默认)"

# --- 模型核心配置 ---
GENERATION_CONFIG = {
  "temperature": 1.0, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192,
}
SAFETY_SETTINGS = [
    {"category": c, "threshold": "BLOCK_NONE"} for c in [
        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
    ]
]

# ==============================================================================
# 2. Session State 初始化
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]
if "selected_model_name" not in st.session_state:
    st.session_state.selected_model_name = DEFAULT_MODEL_NAME

# ==============================================================================
# 3. 核心功能函数
# ==============================================================================

# --- 文件与历史记录操作 ---
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history_simple.pkl")

def _prepare_messages_for_save(messages):
    picklable_messages = []
    for msg in messages:
        # 简化版：只处理文本和图片
        if msg.get("role") in ["user", "assistant"]:
            new_msg = {"role": msg["role"], "content": []}
            content = msg.get("content", [])
            for part in content:
                if isinstance(part, str):
                    new_msg["content"].append(part)
                elif isinstance(part, Image.Image):
                    buffered = BytesIO()
                    part.save(buffered, format="PNG")
                    new_msg["content"].append({"type": "image", "data": buffered.getvalue()})
            picklable_messages.append(new_msg)
    return picklable_messages

def _reconstitute_messages_after_load(messages):
    reconstituted_messages = []
    for msg in messages:
        new_msg = {"role": msg["role"], "content": []}
        for part in msg.get("content", []):
            if isinstance(part, str):
                new_msg["content"].append(part)
            elif isinstance(part, dict) and part.get("type") == "image":
                try:
                    new_msg["content"].append(Image.open(BytesIO(part["data"])))
                except Exception:
                    new_msg["content"].append("[图片加载失败]")
        reconstituted_messages.append(new_msg)
    return reconstituted_messages

def load_history():
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            with open(log_file, "rb") as f:
                st.session_state.messages = _reconstitute_messages_after_load(pickle.load(f))
    except Exception as e:
        st.error(f"读取历史记录失败: {e}")

def save_history():
    try:
        with open(log_file, "wb") as f:
            pickle.dump(_prepare_messages_for_save(st.session_state.messages), f)
    except Exception as e:
        st.error(f"保存历史记录失败: {e}")

def clear_history():
    st.session_state.messages.clear()
    if os.path.exists(log_file):
        os.remove(log_file)
    st.toast("历史记录已清除！", icon="🗑️")

# --- AI 生成逻辑 ---
def get_ai_response(model, history):
    """一个简化的生成函数"""
    try:
        response = model.generate_content(contents=history, stream=True)
        for chunk in response:
            yield chunk.text
    except Exception as e:
        # 直接在生成器中抛出错误，以便主逻辑捕获
        yield f"**生成时出错：**\n\n`{type(e).__name__}: {e}`"
        # 打印完整的追溯到控制台，供开发者调试
        import traceback
        traceback.print_exc()

# ==============================================================================
# 4. Streamlit 界面渲染
# ==============================================================================

st.set_page_config(page_title="极简聊天", layout="centered")

# --- 侧边栏 ---
with st.sidebar:
    st.title("控制面板")

    # API 和模型选择
    st.selectbox(
        "选择API Key:",
        options=list(API_KEYS.keys()),
        key="selected_api_key"
    )
    st.selectbox(
        "选择模型:",
        options=list(MODELS.keys()),
        key="selected_model_name"
    )

    # 文件操作
    with st.expander("文件操作"):
        st.button("读取历史记录 📖", on_click=load_history, use_container_width=True)
        st.button("清除历史记录 🗑️", on_click=clear_history, use_container_width=True)
        # 提供一个下载按钮作为备份
        if st.session_state.messages:
             st.download_button(
                 "下载当前聊天记录 ⬇️",
                 data=pickle.dumps(_prepare_messages_for_save(st.session_state.messages)),
                 file_name="chat_history_backup.pkl",
                 mime="application/octet-stream",
                 use_container_width=True
             )

# --- 主聊天界面 ---
if not st.session_state.messages:
    load_history()

# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        for part in message.get("content", []):
            if isinstance(part, str):
                st.markdown(part)
            elif isinstance(part, Image.Image):
                st.image(part, width=400)

# 核心交互逻辑
prompt = st.chat_input("输入你的消息...", disabled=st.session_state.is_generating)
if prompt:
    st.session_state.messages.append({"role": "user", "content": [prompt]})
    st.session_state.is_generating = True
    st.rerun() # 立即显示用户消息

# 核心生成逻辑
if st.session_state.is_generating:
    with st.chat_message("assistant"):
        # 配置并创建模型实例
        try:
            genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])
            model = genai.GenerativeModel(
                model_name=MODELS[st.session_state.selected_model_name],
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS,
                # 【可选】在这里加入您的系统指令
                # system_instruction="你是一个乐于助人的AI助手。"
            )

            # 准备API历史
            api_history = []
            for msg in st.session_state.messages:
                 # API 需要的格式是 'model' 而不是 'assistant'
                 api_role = "model" if msg["role"] == "assistant" else "user"
                 api_history.append({"role": api_role, "parts": msg["content"]})
            
            # 【极简】直接渲染，不使用 st.spinner
            placeholder = st.empty()
            full_response = ""
            for chunk in get_ai_response(model, api_history):
                full_response += chunk
                placeholder.markdown(full_response + "▌") # 添加闪烁光标
            
            placeholder.markdown(full_response)
            
            # 将完整的回复添加到会话历史
            st.session_state.messages.append({"role": "assistant", "content": [full_response]})
            
        except Exception as e:
            st.error(f"发生严重错误: {e}")
        
        finally:
            # 无论成功或失败，都结束生成状态并保存
            st.session_state.is_generating = False
            save_history()
            st.rerun()
