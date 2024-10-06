import os
import openai
import streamlit as st

# Streamlit 应用标题
st.title("ChatGPT 对话")

# 使用 st.secrets 读取 API 密钥
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 用户输入框
user_input = st.text_input("你：")

# 发送按钮
if st.button("发送") and user_input:
    # 将用户消息添加到对话历史
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 调用 ChatGPT API
    response = openai.chat.completions.create(
        model="gpt-4-0314",  # 使用 gpt-4-0314 模型
        messages=st.session_state.messages,
    )

    # 获取 ChatGPT 回复
    assistant_reply = response.choices[0].message.content

    # 将 ChatGPT 回复添加到对话历史
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# 显示对话历史
for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"**你：** {message['content']}")
    else:
        st.write(f"**ChatGPT：** {message['content']}")
