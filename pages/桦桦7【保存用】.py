import os
import google.generativeai as genai
import streamlit as st

# ==============================================================================
# 1. 常量定义
# ==============================================================================

st.set_page_config(page_title="Gemini 简易测试", layout="centered")
st.title("🐇 Gemini 简易测试 🥕")

# --- API 密钥设置 ---
# 将您的所有API Key放在这里
API_KEYS = {
    "新账号Key-1": "AIza...",
    "旧账号Key-1": "AIza...",
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

# --- 固定的系统指令 ---
# 将您的核心人设指令放在这里，保持简洁
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
    # 模型选择
    selected_model = st.selectbox(
        "选择模型:",
        options=["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] # 使用最新的稳定模型
    )

    # 清除聊天记录的按钮
    if st.button("🗑️ 清除聊天记录"):
        st.session_state.messages = []
        st.success("聊天记录已清除！")
        st.rerun()

# --- 配置Google API ---
# 只有在选择了有效的Key时才进行配置
if selected_key_name and API_KEYS.get(selected_key_name):
    try:
        genai.configure(api_key=API_KEYS[selected_key_name])
        
        # 实例化模型
        model = genai.GenerativeModel(
            model_name=selected_model,
            system_instruction=SYSTEM_INSTRUCTION,
            safety_settings=[ # 安全设置直接内联，保持简洁
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
    except Exception as e:
        st.error(f"API Key 配置失败: {e}")
        st.stop() # 如果Key配置失败，则停止应用运行
else:
    st.warning("请在侧边栏选择一个有效的 API Key。")
    st.stop()


# --- 初始化聊天记录 ---
# 这是唯一需要的 session_state 初始化
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
    # 注意：API需要 "model" 而不是 "assistant"
    api_history = [
        {"role": "model" if msg["role"] == "assistant" else "user", "parts": [msg["content"]]}
        for msg in st.session_state.messages
    ]

    # 3. 调用API并流式显示回复
    with st.chat_message("assistant"):
        try:
            # 使用 st.write_stream，这是处理流式数据的最现代、最简洁的方法
            response_stream = model.generate_content(api_history, stream=True)
            full_response = st.write_stream(response_stream)
            
            # 4. 将完整的AI回复添加到历史记录
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"生成回复时出错: {e}")
