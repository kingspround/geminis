import streamlit as st
import openai

# 1. 设置模拟 API 密钥 (请在实际应用中使用更安全的方案)
openai.api_key = "sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA"  # 替换为你的实际 API 密钥

# Streamlit应用标题
st.title("ChatGPT对话应用")

# 用户输入
user_input = st.text_input("你想说什么？")

# 调用ChatGPT API
if user_input:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一个友好的助手。"},
            {"role": "user", "content": user_input}
        ]
    )
    # 显示响应
    st.write(response.choices[0].message['content'])

# 运行Streamlit应用
if __name__ == '__main__':
    st.run()
