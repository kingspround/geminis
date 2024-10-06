import openai
import streamlit as st
import pickle
import os

# 设置 OpenAI API 密钥
openai.api_key ="sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA" 

# 初始化聊天历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 函数定义 ---
def generate_response(messages):
    """使用 OpenAI API 生成回复"""
    openai.api_key = api_key

    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=''.join([f"{m['role']}: {m['content']}\n" for m in messages]),
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

# --- Streamlit 应用程序 ---
st.title("🤖 ChatGPT 聊天机器人")

# --- 侧边栏 ---
st.sidebar.title("操作")

# 加载历史记录
def load_history(log_file):
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.experimental_rerun()
    except FileNotFoundError:
        st.warning(f"{log_file} 不存在。")
    except EOFError:
        st.warning(f"读取历史记录失败：文件可能损坏。")

# 清除历史记录
def clear_history(log_file):
    st.session_state.messages = []
    try:
        os.remove(log_file)
        st.success(f"成功清除 {log_file} 的历史记录！")
    except FileNotFoundError:
        st.warning(f"{log_file} 不存在。")

# 获取文件名
filename = "chat_history.pkl"
log_file = os.path.join(os.path.dirname(__file__), filename)

if st.sidebar.button("读取历史记录"):
    load_history(log_file)

if st.sidebar.button("清除历史记录"):
    clear_history(log_file)

# --- 主聊天界面 ---
# 显示聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 注意：这里不再需要逐块处理回复
        full_response = generate_response(st.session_state.messages)
        
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 保存聊天记录
with open(log_file, "wb") as f:
    pickle.dump(st.session_state.messages, f)
