import streamlit as st
import base64
from io import BytesIO
import logging
import tiktoken
import openai

# Set your OpenAI API key
openai.api_key = st.secrets["openai"]["OPENAI_API_KEY"]

# Set the model to use
model = "gpt-3.5-turbo"

st.title("ChatGPT Dialogue")

# Initialize conversation history
messages = []

# User input and chat history display
user_input = st.text_input("Enter your message:")
if user_input:
    messages.append({"role": "user", "content": user_input})
    st.write("**You:** " + user_input)

# Image upload
image_buffer = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])

# Generate response from ChatGPT
if user_input:
    try:
        response = await process_message(user_input, messages, image_buffer)  # Call the async function
        messages.append({"role": "assistant", "content": response})
        st.write("**ChatGPT:** " + response)
    except Exception as e:
        st.error(f"Error: {e}")

# Display conversation history
for i, message in enumerate(messages):
    if message['role'] == 'user':
        st.write(f"**You:** {message['content']}")
    else:
        st.write(f"**ChatGPT:** {message['content']}")

# Define the async function
async def process_message(user_input, messages, image_buffer):
    chatgpt = ChatGPT(model="gpt-3.5-turbo")
    if image_buffer is not None:
        response = await chatgpt.send_vision_message(user_input, messages, image_buffer=image_buffer)
    else:
        response = await chatgpt.send_message(user_input, messages)
    return response

class ChatGPT:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model

    async def send_message(self, message, dialog_messages=[]):
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for dialog_message in dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})
        messages.append({"role": "user", "content": message})

        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=0.7,  # 控制响应的随机性
            max_tokens=1000,  # 控制响应的最大 token 数
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].message["content"]

    async def send_vision_message(self, message, dialog_messages=[], image_buffer: BytesIO = None):
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for dialog_message in dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})

        if image_buffer is not None:
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_buffer.read()).decode('utf-8')}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": message})

        response = await openai.ChatCompletion.acreate(
            model="gpt-4-vision-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].message.content
