# First
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv  
import os
from PIL import Image
import numpy as np
from io import BytesIO
from io import StringIO
import streamlit as st

if "key" not in st.session_state:
    st.session_state.key = None
    
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
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "NONE"
  }
]

model = genai.GenerativeModel(model_name="gemini-pro",generation_config=generation_config,safety_settings=safety_settings)

# LLM




def getAnswer(prompt,feedback):
    his_messages=[]
    #his_messages.append(SystemMessage(content=f'''你是一个全能的助手。会全面的回答用户的问题。'''))
    messages=[]
    message=None
    for msg in st.session_state.messages[-20:]:
        if msg["role"]=="user":
            #message=[msg["content"],None]
            his_messages.append({ "role": "user","parts": msg["content"]})
        elif msg is not None and msg["content"] is not None:
            #message[1]=msg["content"]
            his_messages.append({ "role": "model", "parts":msg["content"]})
       
    print(his_messages)  
    response = model.generate_content(contents=his_messages, stream=True)
    ret=""
    for chunk in response:
        print(chunk.text)
        print("_"*80)
        ret+=chunk.text
        feedback(ret)
    
    return ret




if "messages" not in st.session_state:
    st.session_state.messages = []

    
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
def writeReply(cont,msg):
    cont.write(msg)
    
if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
            p=st.empty()
            re = getAnswer(prompt,lambda x:writeReply(p,x))
            print(re)
            st.session_state.messages.append({"role": "assistant", "content": re})
