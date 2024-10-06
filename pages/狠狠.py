import streamlit as st
import openai

# 1. 设置模拟 API 密钥 (请在实际应用中使用更安全的方案)
openai.api_key = "sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA"  # 替换为你的实际 API 密钥

# Streamlit 应用程序标题
st.title('ChatGPT 对话应用')

# 用户输入
user_input = st.text_input('您想说什么？')

# 如果用户输入了内容
if user_input:
    # 调用 OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_input}]
    )
    
    # 获取并显示响应
    chat_response = response.choices[0].message['content']
    st.write(f'ChatGPT: {chat_response}')
