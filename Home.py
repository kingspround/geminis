import streamlit as st
st.config.session_state_persistence = True        
st.set_page_config(
    page_title="Gemini",
    page_icon="👋",
)


st.sidebar.success("Select a demo above.")
st.write("# Welcome to Gemini Streamlit! 👋")



st.markdown(
'''    
    Gemini demo
'''
)

key="AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8"

model = genai.GenerativeModel(model_name="gemini-pro", key=AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8)

if "key" not in st.session_state:
    st.session_state.key = AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8
    

key = st.sidebar.text_input("Your key", type="password")    
if key:
    st.session_state.key =AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8
    
if not st.session_state.key: 
    st.info("Please add your key to continue.")
    st.stop()
    
if not st.session_state.key: 
    st.info("Please add your key to continue.")
    st.stop()
    
