import streamlit as st
from google import genai
import os

# ==========================================
# 1. 页面配置与 API Key 安全管理 (侧边栏输入)
# ==========================================
st.set_page_config(page_title="Gemini 2.5 Chat", page_icon="✨")
st.title("✨ Gemini 2.5 Flash Chatbot")

with st.sidebar:
    st.header("🔑 API 配置")
    # 让用户在网页侧边栏输入 Key，而不是写死在代码里（安全第一！）
    api_key_input = st.text_input("请输入你的 Gemini API Key", type="password")
    st.markdown("[获取免费 API Key](https://aistudio.google.com/app/apikey)")

if not api_key_input:
    st.info("👈 请在左侧边栏输入你的 API Key 以开始聊天。")
    st.stop()

# ==========================================
# 2. 初始化最新的 Google GenAI 客户端
# ==========================================
# 使用你查到的最新方法初始化 Client
client = genai.Client(api_key=api_key_input)

# ==========================================
# 3. 初始化聊天历史记录
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# 在界面上渲染过去的聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 4. 核心逻辑：构造请求并流式生成回答
# ==========================================
def stream_gemini_response(user_prompt):
    """
    使用最新的 SDK 构造上下文并获取流式返回
    """
    # 构造符合最新 API 格式的上下文列表
    contents = []
    
    # 取最近 20 条记录作为上下文
    for msg in st.session_state.messages[-20:]:
        # ⚠️ 注意：Streamlit 里的 AI 叫 "assistant"，但 Gemini 里必须叫 "model"
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
    
    # 把当前用户的新问题加进去
    contents.append({
        "role": "user",
        "parts": [{"text": user_prompt}]
    })
    
    # 💡 官方最新提示：使用 client.models.generate_content_stream 进行流式输出
    # 注意：你的官方文档里甚至出现了 gemini-3-flash-preview，
    # 但目前最稳定且开放的新版本是 gemini-2.5-flash
    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash", 
            contents=contents
        )
        
        # 这是一个生成器，Streamlit 的 st.write_stream 会自动处理它
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"⚠️ API 请求发生错误 (请检查模型是否对您开放或网络代理是否为美国节点):\n\n {str(e)}"

# ==========================================
# 5. 聊天输入框处理
# ==========================================
if prompt := st.chat_input("说点什么吧..."):
    # 1. 显示用户输入
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. 调用 API 并显示 AI 回复
    with st.chat_message("assistant"):
        # 使用 Streamlit 最新的原生流式输出组件 (比之前的空占位符 lambda 函数优雅很多)
        full_response = st.write_stream(stream_gemini_response(prompt))
        
    # 3. 将 AI 回复存入历史记录
    st.session_state.messages.append({"role": "assistant", "content": full_response})
```

### 💡 这版代码的亮点（结合了最新官方文档）：
1. **彻底移除了旧库 `google.generativeai`**，全面采用了你提供的最新库 `from google import genai` 和 `client = genai.Client()`。
2. **安全第一**：不再把 Key 强行写在代码里，而是通过 Streamlit 的侧边栏 (`st.sidebar.text_input`) 输入，这样你发给任何人看都不会泄露。
3. **极简流式输出**：废弃了之前你代码里复杂的 `lambda` 回调函数和 `st.empty()`，直接使用了 Streamlit 原生提供的 `st.write_stream(generator)`，代码行数更少，运行更流畅。
4. **历史记录格式严格对齐**：把 `assistant` 严格转换成了 Gemini 要求的 `model`，并采用了最新文档里的嵌套格式 `{"role": "...", "parts": [{"text": "..."}]}`。

你可以运行这段代码试试看！**如果还是报 `429` 且带有 `limit 0`，请记得一定要把你的梯子（代理）切换到美国节点，并开启全局模式！**
