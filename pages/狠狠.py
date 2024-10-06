import streamlit as st
import openai

# 1. 设置模拟 API 密钥 (请在实际应用中使用更安全的方案)
openai.api_key = "sk-zGzsKlEMKwMgpXPThLcEvOQ9fuDXG0J4oBqz-yepz1T3BlbkFJrGTEp7fUWyY0RU54RfRdLqhfyui7H_gWe76PDVX2UA"  # 替换为你的实际 API 密钥

# Set the model to use
model = "gpt-4o-mini"

st.title("ChatGPT Dialogue")

# Initialize conversation history
messages = []

# User input and chat history display
user_input = st.text_input("Enter your message:")
if user_input:
    messages.append({"role": "user", "content": user_input})
    st.write("**You:** " + user_input)

# Generate response from ChatGPT
if user_input:
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        assistant_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_response})
        st.write("**ChatGPT:** " + assistant_response)
    except Exception as e:
        st.error(f"Error: {e}")

# Display conversation history
for i, message in enumerate(messages):
    if message['role'] == 'user':
        st.write(f"**You:** {message['content']}")
    else:
        st.write(f"**ChatGPT:** {message['content']}")
