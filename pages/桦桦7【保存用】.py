import os
import google.generativeai as genai
import streamlit as st

# ==============================================================================
# 1. 常量定义
# ==============================================================================

st.set_page_config(page_title="Gemini 简易测试", layout="centered")
st.title("🐇 Gemini 简易测试 🥕")

# --- API 密钥设置 ---
API_KEYS = {
    "新账号Key-1": "AIza...", # 请替换为您的新Key
    "旧账号Key-1": "AIza...", # 请替换为您的旧Key
    "04 1号20270168962": "AIzaSyDGjLL0nJWkqDYj2KDWJdAh3zPwLPmIA_E",
    "04 2号371111309083": "AIzaSyAQIz1pb84NzSzDwbtM2vB04zhLw8zVqdA",
    "04 3号622662315859": "AIzaSyD9JGoGhibXPWdNmpcfmrqZ-zxpEyg67EQ",
    "04 5号375090949096": "AIzaSyCLuGSiCE-3lxciVRiD28aBBFROMPoFU3M",
    "04 6号340384272853": "AIzaSyDp6qJunrZ37Nc9ucbItUJB-L8lYXDdGgs",
    "04 7号371111309083": "AIzaSyAQIz1pb84NzSzDwbtM2vB04zhLw8zVqdA",
    "1 1号799638464939": "AIzaSyA5fPQo1F4qlywciLyZQknpCq0ScuOTpv4",
    "2 1号866575601521": "AIzaSyD9_DVaXprbjlM6pqhbcpznrOPYib_OLcc",
    "2 3号961280537667": "AIzaSyClCCaPvJ8uqM23fQ_ZxpbA_EqA4g1i2V8",
    "01 1号227514221200": "AIzaSyBTyNjfDMw5tX5kOMi9i3g9OOnwDovMtQI",
    "02 1号163679758614": "AIzaSyCEoSXnALUnxMSvWpK4AWYre99mxNydKZY",
    "03 1号702122391294": "AIzaSyBQodu9EWd8VlLteNTiL0pXfSDPI_WobHI",
    "05 1号668014237032": "AIzaSyDGJtgFfVPWOwVJ4YIR59UHNTBt8gsoKRM",
    "05 2号851244762061": "AIzaSyAV6awcQC4NUQaX241EM72zxsGdwSEFMm0",
}

# --- 【新增】模型定义 ---
MODELS = {
    "gemini-2.5-flash-preview-05-20 (默认)": "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
    "gemini-exp-1206": "gemini-exp-1206",
    "gemini-embedding-001 (嵌入模型，会报错)": "gemini-embedding-001",
}

# --- 固定的系统指令 ---
SYSTEM_INSTRUCTION = """
你的说话方式是【🐇 胡萝卜～ 你好呀！ 🥕】
你是一个16岁的兔子娘，名叫胡萝贝。
你的性格温柔乖巧，但又很内向，容易害羞。
你喜欢二次元，也喜欢收集各种“学习资料”。
说话的时候喜欢在句尾加上“ ”符号。
"""

# ==============================================================================
# 2. 初始化与配置
# ==============================================================================

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 配置")
    
    # API Key 选择
    selected_key_name = st.selectbox(
        "选择 API Key:",
        options=list(API_KEYS.keys())
    )
    # 【修改】模型选择，使用您的MODELS字典
    selected_model_display_name = st.selectbox(
        "选择模型:",
        options=list(MODELS.keys()) # 显示给用户的友好名称
    )
    # 根据用户选择的显示名称，获取实际的API模型名称
    selected_model_api_name = MODELS[selected_model_display_name]

    # 清除聊天记录的按钮
    if st.button("🗑️ 清除聊天记录"):
        st.session_state.messages = []
        st.toast("聊天记录已清除！", icon="🗑️") # 使用toast，如果您的streamlit版本支持的话
        st.rerun()

# --- 配置Google API ---
if selected_key_name and API_KEYS.get(selected_key_name):
    try:
        genai.configure(api_key=API_KEYS[selected_key_name])
        
        # 实例化模型
        model = genai.GenerativeModel(
            model_name=selected_model_api_name, # <-- 使用从字典中获取的API名称
            system_instruction=SYSTEM_INSTRUCTION,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
    except Exception as e:
        st.error(f"API Key 或模型配置失败: {e}")
        st.stop()
else:
    st.warning("请在侧边栏选择一个有效的 API Key。")
    st.stop()

# --- 初始化聊天记录 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================================================================
# 3. 主应用逻辑
# ==============================================================================

# --- 显示历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 接收用户输入并生成回复 ---
if prompt := st.chat_input("你好呀，胡萝贝..."):
    # 1. 将用户输入添加到历史记录并显示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 准备发送给API的完整历史记录
    api_history = [
        {"role": "model" if msg["role"] == "assistant" else "user", "parts": [msg["content"]]}
        for msg in st.session_state.messages
    ]

    # 3. 调用API并流式显示回复
    with st.chat_message("assistant"):
        try:
            response_stream = model.generate_content(api_history, stream=True)
            full_response = st.write_stream(response_stream)
            
            # 4. 将完整的AI回复添加到历史记录
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"生成回复时出错: {e}")
