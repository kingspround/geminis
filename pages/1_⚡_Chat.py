import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import json
from google.api_core.exceptions import InvalidArgument

if "key" not in st.session_state:
    st.session_state.key = "AIzaSyC7vfMxqZQJVNq0rUhzpOKu1m84y737Tak"  # 请替换为你的实际密钥

if not st.session_state.key:
    st.info("Please add your key to continue.")
    st.stop()

genai.configure(api_key=st.session_state.key)

# Set up the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=safety_settings,
)


# LLM
def getAnswer(prompt, feedback):
    his_messages = []
    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            his_messages.append({"role": "user", "parts": msg["content"]})
        elif msg is not None and msg["content"] is not None:
            his_messages.append({"role": "model", "parts": msg["content"]})

    print("发送给 API 的消息:", json.dumps(his_messages, indent=2))

    try:
        response = model.generate_content(contents=his_messages, stream=True)
        ret = ""
        for chunk in response:
            print("API 返回的片段:", chunk.text)
            print("_" * 80)
            ret += chunk.text
            feedback(ret)
        return ret
    except InvalidArgument as e: #  修改这里
        st.error(f"Gemini API 参数无效: {e}")
        st.write(f"请求 JSON: {json.dumps(his_messages, indent=2)}")
        return ""
    except Exception as e:
        st.error(f"发生意外错误: {e}")
        return ""


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def writeReply(cont, msg):
    cont.write(msg)


if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty()
        re = getAnswer(prompt, lambda x: writeReply(p, x))
        if re:  # 仅当 re 不为空字符串（即没有错误）时才追加消息
            st.session_state.messages.append({"role": "assistant", "content": re})
