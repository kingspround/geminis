import openai
import streamlit as st
import pickle
import os

# 设置 OpenAI API 密钥
api_key ="sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA" 
openai.api_key = api_key

# 初始化聊天历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 函数定义 ---
def generate_response(messages):
    """使用 OpenAI API 和 gpt-4-1106-preview 模型生成回复"""
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=messages,
    )
    return response.choices[0].message.content

# --- 主聊天界面 ---
st.title("ChatGPT 对话")

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
        full_response = generate_response(st.session_state.messages)
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
