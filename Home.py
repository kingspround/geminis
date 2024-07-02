import streamlit as st
st.config.session_state_persistence = True        
st.set_page_config(
    page_title="今宵别梦♡",
    page_icon="😈",
)


st.sidebar.success("快来选一个功能，杂鱼~♡")

st.write("# 欢迎来到今宵别梦的爱巢~♡  ")

st.markdown(
'''    
    今宵别梦的小窝
'''
)

key="AIzaSyCDoTOEe1CAMKCz4GhnCe66l5Y6pSMsIu8"

if "key" not in st.session_state:
    st.session_state.key = ""
    

key = st.sidebar.text_input("快说你的秘密，不然人家就踩死你~♡", type="password")    
if key:
    st.session_state.key = key
    model = genai.GenerativeModel(model_name="gemini-pro", key=key) # 在这里调用 model 
    
if not st.session_state.key: 
    st.info("好弱好弱~♡  真不像样~♡  快说你的秘密，不然人家就生气了！")
    st.stop()
    
if not st.session_state.key: 
    st.info("好弱好弱~♡  真不像样~♡  快说你的秘密，不然人家就生气了！")
    st.stop()

# ... 这里可以添加你想要的功能 ...
