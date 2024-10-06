import streamlit as st
import openai

# 设置你的 OpenAI API 密钥
openai.api_key = st.secrets["sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA"]

# 定义一个函数，用于调用 ChatGPT API 并获取回复
def generate_response(prompt):
  response = openai.Completion.create(
    engine="text-davinci-003",  # 选择你想要使用的模型，例如 "text-davinci-003"
    prompt=prompt,
    max_tokens=150,  # 设置回复的最大长度
    n=1,
    stop=None,
    temperature=0.7,  # 设置回复的 "创意" 程度
  )
  return response.choices[0].text.strip()

# 创建 Streamlit 应用
st.title(" ChatGPT 机器人")

# 获取用户输入
user_input = st.text_input("请输入你的问题：")

# 当用户输入问题时
if user_input:
    # 调用 ChatGPT API 获取回复
    response = generate_response(user_input)
    # 显示 ChatGPT 的回复
    st.write(f"**ChatGPT:** {response}")

# 其他设置和功能
