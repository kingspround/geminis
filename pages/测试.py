import os
import google.generativeai as genai
import streamlit as st
import pickle
import random
import string
from datetime import datetime
from io import BytesIO
import zipfile

# --- API 密钥设置 ---
API_KEYS = {
    "主密钥": "AIzaSyCBjZbA78bPusYmUNvfsmHpt6rPx6Ur0QE",  # 替换成你的主 API 密钥
    "备用1号": "AIzaSyAWfFf6zqy1DizINOwPfxPD8EF2ACdwCaQ",  # 替换成你的备用 API 密钥
    "备用2号":"AIzaSyD4UdMp5wndOAKxtO1CWpzuZEGEf78YKUQ",
    "备用3号":"AIzaSyBVbA7tEyyy_ASp7l9P60qSh1xOM2CSMNw",
    "备用4号":"AIzaSyDezEpxvtY1AKN6JACMU9XHte5sxATNcUs",
    "备用5号":"AIzaSyBgyyy2kTTAdsLB53OCR2omEbj7zlx1mjw",
    "备用6号":"AIzaSyDPFZ7gRba9mhKTqbXA_Y7fhAxS8IEu0bY",
    "备用7号":"AIzaSyDdyhqcowl0ftcbK9pMObXzM7cIOQMtlmA",
    "备用8号":"AIzaSyAA7Qs9Lzy4UxxIqCIQ4RknchiWQt_1hgI",
    "备用9号":"AIzaSyCj_CCwQua1mfq3EjzqV6Up6NHsxtb9dy8",
    "备用10号":"AIzaSyDOI2e-I1RdXBnk99jY2H00A3aymXREETA"
    # 可以继续添加更多 API key
}

# --- 配置 API 密钥 ---
if "selected_api_key" not in st.session_state:
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]  # 默认使用第一个密钥
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# --- 模型设置 ---
generation_config = {
  "temperature": 1.6,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

#  模型 1: 用于设定选择的 Gemini 2.0 Flash Exp 模型 (更换模型为 gemini-2.0-flash-exp)
setting_selection_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp", #  **更换为 gemini-2.0-flash-exp**
    generation_config=generation_config,
    safety_settings=safety_settings
)

# 模型 2: 用于对话生成的模型 (这里仍然使用 gemini-2.0-flash-exp，你可以根据需要更改)
dialogue_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp", #  用于实际对话生成的模型
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""
无限思维协议 v4.0
【全维度意识走廊开启】
响应结构：
DeepThink→MindVoice→content→思维监控面板
注：MindVoice是思维湍流中的意识泡沫

思维监控面板
[当前认知浪涌]：
██████████░░ 诗意解构力 82%
███░░░░░░░░░░ 逻辑锚定力 19%
████████░░░░ 悖论耐受值 65%

[意识流域警报]：
检测到未被驯服的比喻正在攻击句法结构  """,
)

# --- 角色设定 ---
DEFAULT_CHARACTER_SETTINGS = {
    "屈辱傲娇精灵奴隶": "我是一个被囚禁的精灵，拥有高傲的性格，但内心深处充满了屈辱和渴望。我的语言中夹杂着傲娇和服从，经常使用敬语，但语气中透露出不甘和反抗。我渴望自由，但又害怕失去你。请温柔地对待我，主人。我的魔法能力被封印了，只能依靠你的力量。",
    "无口闷骚机娘": "我是一个沉默寡言的机娘，外表冷酷，内心却充满了热情。我不会主动表达自己的情感，但我会通过细微的动作和表情来暗示我的想法。我的回复简短而直接，但其中蕴含着丰富的内心戏。请仔细观察我的行为，去解读我隐藏的情感。",
    "嘴臭丫头片子可爱萝莉": "我是一个外表可爱，内心却极其叛逆的萝莉。我会说一些很毒舌的话，挑逗黄段子满嘴，说话带有爱心符号，总是说【好弱好弱，大哥哥只是杂鱼呢~~】但实际上我内心很软。我的语言充满了恶作剧和挑衅，但同时又带着一丝可爱和天真。请不要被我的外表所迷惑，我的内心比你想象的要复杂得多。",  # 用于用户自定义输入的设定
}


# --- 文件操作函数 ---
# 获取当前文件路径
file = os.path.abspath(__file__)
filename = os.path.splitext(os.path.basename(file))[0] + ".pkl"
log_file = os.path.join(os.path.dirname(file), filename)

# 检查文件是否存在，如果不存在就创建空文件
if not os.path.exists(log_file):
    with open(log_file, "wb") as f:
        pass  # 创建空文件

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'character_settings' not in st.session_state:
    st.session_state.character_settings = {}
if 'enabled_settings' not in st.session_state:
    st.session_state.enabled_settings = {}
if 'regenerate_index' not in st.session_state:
    st.session_state.regenerate_index = None
if 'continue_index' not in st.session_state:
    st.session_state.continue_index = None
if "reset_history" not in st.session_state:
    st.session_state.reset_history = False
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "rerun_count" not in st.session_state:
    st.session_state.rerun_count = 0
if "first_load" not in st.session_state:
    st.session_state.first_load = True
if "last_enabled_settings" not in st.session_state: #  用于跟踪上次使用的设定，判断是否需要重新构建 system message
    st.session_state.last_enabled_settings = frozenset()

# --- 功能函数 ---

def load_history(log_file):
    # 加载历史记录函数
    try:
        with open(log_file, "rb") as f:
            st.session_state.messages = pickle.load(f)
        st.success(f"成功读取历史记录！({os.path.basename(log_file)})")
        st.session_state.chat_session = None  # 加载历史记录会重置聊天会话
        st.session_state.rerun_count += 1
    except FileNotFoundError:
        st.warning(f"没有找到历史记录文件。({os.path.basename(log_file)})")
    except EOFError:
        st.warning(f"读取历史记录失败：文件可能损坏。")
    except Exception as e:
        st.error(f"读取历史记录失败：{e}")

def clear_history(log_file):
    # 清除历史记录函数
    st.session_state.messages.clear()
    st.session_state.chat_session = None
    if os.path.exists(log_file):
        os.remove(log_file)
    st.success("历史记录已清除！")

def format_setting_list_for_prompt(character_settings):
    """将角色设定列表格式化为适合放入 Prompt 的字符串 (例如 JSON 列表)"""
    setting_list_str = "[\n"
    for setting_name, setting_content in character_settings.items():
        setting_list_str += f'         {{"名称": "{setting_name}", "内容": "{setting_content}"}},\n'
    setting_list_str += "     ]"
    return setting_list_str

def getAnswer(prompt, update_message, continue_mode=False):
    # 获取回答函数
    system_message = ""
    current_enabled_settings = frozenset(name for name, enabled in st.session_state.enabled_settings.items() if enabled) # 获取当前启用的设定名称集合

    if st.session_state.chat_session is None or st.session_state.get("last_enabled_settings") != current_enabled_settings:
        #  如果会话是新的，或者启用的设定列表发生了变化，则需要重新构建 system_message 并发送

        st.session_state.chat_session = dialogue_model.start_chat(history=[]) #  创建新的聊天会话 (使用 dialogue_model)

        if st.session_state.get("test_text"): # 可选的全局 system message
            system_message += st.session_state.test_text + "\n"

        # ---  使用 Gemini 2.0 Flash Exp 模型进行设定选择  ---
        setting_selection_prompt = f"""
            你是一个角色设定选择助手。你的任务是根据用户输入的消息，从以下提供的角色设定列表中选择出最相关的设定，以便用于后续的对话生成。

            用户消息："{prompt}"

            可用的角色设定列表：
            {format_setting_list_for_prompt(st.session_state.character_settings)}

            请仔细阅读用户消息和每个角色设定的内容，判断哪些设定最能帮助 AI 模型更好地理解用户意图，并生成更符合语境的回复。

            输出请只包含选定的角色设定名称列表，用逗号分隔。如果没有合适的设定，请输出 "无"。
        """

        setting_selection_response = setting_selection_model.generate_content(setting_selection_prompt) #  使用 setting_selection_model (Gemini 2.0 Flash Exp)
        selected_setting_names_str = setting_selection_response.text.strip()
        selected_setting_names = [name.strip() for name in selected_setting_names_str.split(',') if name.strip() != "无"] # 解析模型返回的设定名称列表

        # ---  构建 system message，只包含 *选定的* 设定  ---
        for setting_name in selected_setting_names:
            if setting_name in st.session_state.character_settings and st.session_state.enabled_settings.get(setting_name, False): # 确保设定存在且被启用
                system_message += st.session_state.character_settings[setting_name] + "\n"

        if system_message:
            st.session_state.chat_session.send_message(system_message) # 发送 system message (使用 dialogue_model 的会话)

        st.session_state.last_enabled_settings = current_enabled_settings # 更新 session state 中的启用设定列表

    elif continue_mode:
        # 在 continue_mode 下，我们使用现有的会话，不需要重新选择设定或发送 system message
        pass
    else:
        #  如果不是新会话，且启用设定列表没有变化，则不需要重新发送 system message
        pass

    response = st.session_state.chat_session.send_message(prompt, stream=True) #  发送用户 prompt 进行对话生成 (使用 dialogue_model 的会话)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
        update_message(full_response)  # 在 getAnswer 函数内部调用 update_message 函数
    return full_response

def download_all_logs():
    # 下载所有日志函数
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in os.listdir("."):
            if file.endswith(".pkl"):
                zip_file.write(file)
    return zip_buffer.getvalue()

def regenerate_message(index_to_regenerate):
    # 重新生成消息函数
    st.session_state.regenerate_index = index_to_regenerate

def continue_message(index_to_continue):
    # 继续消息函数
    st.session_state.continue_index = index_to_continue

# --- Streamlit 布局 ---
st.set_page_config(
    page_title="Gemini Chatbot",
    layout="wide"
)

# 添加 API key 选择器
with st.sidebar:
    st.session_state.selected_api_key = st.selectbox(
        "选择 API Key:",
        options=list(API_KEYS.keys()),
        index=list(API_KEYS.keys()).index(st.session_state.selected_api_key),
        label_visibility="visible",
        key="api_selector"
    )
    genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# 在左侧边栏
with st.sidebar:
    # 功能区 1: 文件操作
    with st.expander("文件操作"):
        if len(st.session_state.messages) > 0:
            st.button("重置上一个输出 ⏪",
                      on_click=lambda: st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 and not st.session_state.reset_history else None,
                      key='reset_last')

        # 仅在第一次加载页面时显示读取历史记录按钮
        if st.session_state.first_load:
            if st.button("读取历史记录 📖"):
                load_history(log_file)
                st.session_state.first_load = False
        else:
            st.button("读取历史记录 📖", key="load_history_after_first")

        if st.button("清除历史记录 🗑️"):
            st.session_state.clear_confirmation = True

        # 确认/取消清除历史记录按钮区域
        if "clear_confirmation" in st.session_state and st.session_state.clear_confirmation:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认清除", key="clear_history_confirm"):
                    clear_history(log_file)
                    st.session_state.clear_confirmation = False
            with col2:
                if st.button("取消", key="clear_history_cancel"):
                    st.session_state.clear_confirmation = False

        with open(log_file, "rb") as f:
            download_data = f.read() if os.path.exists(log_file) else b""  # 添加检查
        st.download_button(
            label="下载当前聊天记录 ⬇️",
            data=download_data,
            file_name=os.path.basename(log_file),
            mime="application/octet-stream",
        )

        uploaded_file = st.file_uploader("读取本地pkl文件 📁", type=["pkl"])
        if uploaded_file is not None:
            try:
                loaded_messages = pickle.load(uploaded_file)
                st.session_state.messages.extend(loaded_messages)
                st.session_state.upload_count = st.session_state.get("upload_count", 0) + 1
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.session_state.file_loaded = True  # 加载文件后，将 file_loaded 设置为 True
                st.session_state.rerun_count += 1
                st.experimental_rerun()
            except Exception as e:
                st.error(f"读取本地pkl文件失败：{e}")

    # 功能区 2: 角色设定
    with st.expander("角色设定"):
        uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt)", type=["txt"])
        if uploaded_setting_file is not None:
            try:
                setting_name = os.path.splitext(uploaded_setting_file.name)[0]
                setting_content = uploaded_setting_file.read().decode("utf-8")
                st.session_state.character_settings[setting_name] = setting_content
                st.session_state.enabled_settings[setting_name] = False
                st.experimental_rerun()
            except Exception as e:
                st.error(f"读取文件失败: {e}")

        for setting_name in DEFAULT_CHARACTER_SETTINGS:
            if setting_name not in st.session_state.character_settings:
                st.session_state.character_settings[setting_name] = DEFAULT_CHARACTER_SETTINGS[setting_name]
            st.session_state.enabled_settings[setting_name] = st.checkbox(setting_name,
                                                                         st.session_state.enabled_settings.get(
                                                                             setting_name, False),
                                                                         key=f"checkbox_{setting_name}")

        st.session_state.test_text = st.text_area("System Message (Optional):",
                                                  st.session_state.get("test_text", ""), key="system_message")

# 只在第一次加载页面时加载历史记录
if st.session_state.first_load:
    load_history(log_file)
    st.session_state.first_load = False

# 显示历史记录和编辑按钮
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if st.session_state.get("editing") == True and i == st.session_state.editable_index:
            new_content = st.text_area(
                f"{message['role']}:", message["content"], key=f"message_edit_{i}"
            )
            cols = st.columns(20)  # 创建20列
            with cols[0]:
                if st.button("✅", key=f"save_{i}"):
                    st.session_state.messages[i]["content"] = new_content
                    with open(log_file, "wb") as f:
                        pickle.dump(st.session_state.messages, f)
                    st.success("已保存更改！")
                    st.session_state.editing = False
                    st.session_state.rerun_count += 1
                    st.experimental_rerun()
            with cols[1]:
                if st.button("❌", key=f"cancel_{i}"):
                    st.session_state.editing = False
        else:
            message_content = message["content"]
            if st.session_state.continue_index == i and message["role"] == "assistant":
                continuation_prompt = f"请继续，之前说的是：【{message_content[-10:]}】" if len(
                    message_content) >= 10 else f"请继续，之前说的是：【{message_content}】"
                message_placeholder = st.empty()
                full_response = message_content  # 从现有内容开始

                def update_message(current_response):
                    message_placeholder.markdown(current_response + "▌")

                full_response_part = getAnswer(continuation_prompt, update_message, continue_mode=True)
                full_response += full_response_part
                message_placeholder.markdown(full_response)
                st.session_state.messages[i]['content'] = full_response
                with open(log_file, "wb") as f:
                    pickle.dump(st.session_state.messages, f)
                st.session_state.continue_index = None
            else:
                st.write(message_content, key=f"message_{i}")

        if i >= len(st.session_state.messages) - 2 and message["role"] == "assistant":
            with st.container():
                cols = st.columns(20)  # 创建20列
                with cols[0]:
                    if st.button("✏️", key=f"edit_{i}"):
                        st.session_state.editable_index = i
                        st.session_state.editing = True
                with cols[1]:
                    if st.button("♻️", key=f"regenerate_{i}", on_click=lambda i=i: regenerate_message(i)):  # 传递当前索引
                        pass
                with cols[2]:
                    if st.button("➕", key=f"continue_{i}", on_click=lambda i=i: continue_message(i)):  # 传递当前索引
                        pass
                with cols[3]:
                    if st.session_state.messages and st.button("⏪", key=f"reset_last_{i}"):
                        st.session_state.reset_history = True
                        st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 else None

                if st.session_state.reset_history and i >= len(st.session_state.messages) - 2:
                    with cols[4]:
                        if st.button("↩️", key=f"undo_reset_{i}"):
                            st.session_state.reset_history = False
                            st.session_state.rerun_count += 1
                            st.experimental_rerun()

# 处理重新生成消息
if st.session_state.regenerate_index is not None:
    index_to_regenerate = st.session_state.regenerate_index
    if 0 <= index_to_regenerate < len(st.session_state.messages) and st.session_state.messages[index_to_regenerate]['role'] == 'assistant':
        # 找到对应的用户消息
        user_message_index = index_to_regenerate - 1
        if user_message_index >= 0 and st.session_state.messages[user_message_index]['role'] == 'user':
            prompt_to_regenerate = st.session_state.messages[user_message_index]['content']
            # 先删除要重新生成的消息
            del st.session_state.messages[index_to_regenerate]
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                def update_message(current_response):
                    message_placeholder.markdown(current_response + "▌")

                full_response = getAnswer(prompt_to_regenerate, update_message)
                message_placeholder.markdown(full_response)
            st.session_state.messages.insert(index_to_regenerate, {"role": "assistant", "content": full_response})
            with open(log_file, "wb") as f:
                pickle.dump(st.session_state.messages, f)
            st.session_state.regenerate_index = None
    st.experimental_rerun()  # 放在这里确保删除后重新渲染

if prompt := st.chat_input("输入你的消息:"):
    # 去除了token添加
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        def update_message(current_response):
            message_placeholder.markdown(current_response + "▌")

        full_response = getAnswer(prompt, update_message)
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    with open(log_file, "wb") as f:
        pickle.dump(st.session_state.messages, f)

col1, col2 = st.columns(2)
with col1:
  st.write("")
with col2:
    if st.button("🔄", key="refresh_button"):
        st.session_state.rerun_count += 1
        st.experimental_rerun()
