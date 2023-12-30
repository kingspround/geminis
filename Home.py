import streamlit as st
st.config.session_state_persistence = True        
st.set_page_config(
    page_title="Gemini",
    page_icon="👋",
    # key="AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8" # 你可以在这里添加一个key参数，用来区分不同的页面配置
)


st.sidebar.success("Select a demo above.")
st.write("# Welcome to Gemini Streamlit! 👋")



st.markdown(
'''    
    Gemini demo
'''
)

if "key" not in st.session_state:
    st.session_state.key = None
    

key = st.sidebar.text_input("Your key", type="password", key="AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8") # 你可以在这里添加一个key参数，用来区分不同的文本输入框   
if key:
    st.session_state.key =key
    
if not st.session_state.key: 
    st.info("Please add your key to continue.")
    st.stop()
    
