import streamlit as st
import openai
import os

# 1. 设置模拟 API 密钥 (请在实际应用中使用更安全的方案)
openai.api_key = "sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA"  # 替换为你的实际 API 密钥

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 显示标题和输入框
st.title("ChatGPT 对话助手")
st.subheader("使用 gpt-4-mini 模型")

# 用户输入
user_input = st.text_input("请输入您的问题：", key="input")

# 处理用户输入并生成响应
if user_input:
    with st.spinner("生成回复中..."):
        st.session_state["messages"].append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-4-mini",
            messages=st.session_state["messages"]
        )
        reply = response.choices[0].message["content"]
        st.session_state["messages"].append({"role": "assistant", "content": reply})

# 显示对话历史
if st.session_state["messages"]:
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.text_area("用户：", message["content"], key=f"user_{message['content']}")
        else:
            st.text_area("助手：", message["content"], key=f"assistant_{message['content']}")

# 清除对话按钮
if st.button("清除对话"):
    st.session_state["messages"] = []
