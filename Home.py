import streamlit as st
import google.generativeai as genai  # 导入 google.generativeai 库

st.config.session_state_persistence = True
st.set_page_config(
    page_title="今宵别梦♡",
    page_icon="😈",
)

st.sidebar.success("快来选一个功能，杂鱼~♡")

st.write("# 欢迎来到今宵别梦的爱巢~♡  ")

st.markdown(
    """
    今宵别梦的小窝
    """
)

key = ""

if "key" not in st.session_state:
    st.session_state.key = None

key = st.sidebar.text_input("快说你的秘密，不然人家就踩死你~♡", type="password")
if key:
    st.session_state.key = key

if not st.session_state.key:
    st.info("好弱好弱~♡  真不像样~♡  快说你的秘密，不然人家就生气了！")
    st.stop()

# 正确设置 API 密钥
genai.configure(api_key=st.session_state.key)
model = genai.GenerativeModel(model_name="gemini-pro")

# ... 这里可以添加你想要的功能 ...

# 例如，生成文本：
prompt = st.text_input("请输入你的提示：")
if prompt:
    response = model.generate_text(prompt=prompt)
    st.write(response.result)
