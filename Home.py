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

if "key" not in st.session_state:
    st.session_state.key = None
    

key = st.sidebar.text_input("Your key", type="password")    
if key:
    st.session_state.key =key
    
if not st.session_state.key: 
    st.info("Please add your key to continue.")
    st.stop()
    
if not st.session_state.key: 
    st.info("Please add your key to continue.")
    st.stop()
    
