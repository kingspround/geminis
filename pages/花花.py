import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv  
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import streamlit as st
import random

# Insert your API key here
st.session_state.key = "AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY"

if "key" not in st.session_state:
    st.session_state.key = NONE
    
if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()
    
genai.configure(api_key=st.session_state.key)

# Set up the model
generation_config = {
  "temperature": 1,
  "top_p": 0,
  "top_k": 0,
  "max_output_tokens": 10000,
}

safety_settings = [
   {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
   },
   {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
   },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",generation_config=generation_config,safety_settings=safety_settings)

# LLM

def generate_token():
    """生成一个 10 位到 20 位的随机 token"""
    token_length = random.randint(10, 20)
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    token = ''.join(random.choice(characters) for i in range(token_length))
    return token

def getAnswer(prompt, token):
    his_messages = []
    his_messages.append(
        {"role": "model", "parts": [{"text": f"你的随机token是：{token}"""}]}
    )

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    try:
        response = model.generate_content(contents=his_messages, stream=True)
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response  # 返回完整的回复
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""  # 在发生错误时返回空字符串


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your message (including your token):"):
    token = generate_token()
    st.session_state.messages.append({"role": "user", "content": f"{prompt}  (token: {token})"})
    with st.chat_message("user"):
        st.markdown(f"{prompt}  (token: {token})")
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in getAnswer(prompt, token): 
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 增加重置上一个输出的按钮
if len(st.session_state.messages) > 0:
    st.button("重置上一个输出", on_click=lambda: st.session_state.messages.pop(-1))
