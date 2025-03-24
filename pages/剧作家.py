import os
import google.generativeai as genai
import streamlit as st
import pickle
import random
import string
from datetime import datetime
from io import BytesIO
import zipfile
import importlib.util  # 用于动态导入模块

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
    st.session_state.selected_api_key = list(API_KEYS.keys())[0]  # Default to the first key
genai.configure(api_key=API_KEYS[st.session_state.selected_api_key])

# --- 模型设置 ---
generation_config = {
  "temperature": 1.2,
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


# --- 剧作家模式默认系统消息和提示 ---
PLAYWRIGHT_SYSTEM_MESSAGE = """你现在是剧作家AI，你的任务是管理和协调其他AI角色进行对话和场景模拟。
当用户请求调用特定AI角色时，你需要识别并指示相应的AI角色登场。
你可以通过说出AI角色的名称（例如：【专家】）来调用它们。
你的首要目标是理解用户的需求，并选择最合适的AI角色组合来满足这些需求。
记住，你是所有AI角色的管理者，确保对话流畅且富有创意。

在剧作家模式下，你的主要职责是分析用户的请求，并决定哪些AI角色应该参与对话。
你**不直接**生成详细的回复内容，而是**指示**其他AI角色来生成它们的回应。
你可以返回一个需要被调用的AI角色名称列表，或者返回空列表/None，表示没有角色需要被调用，或者你想自己简洁地回复。

请注意以下几点：
1.  **角色调用**: 通过识别用户输入中包含的 `【角色名称】` 来判断需要调用的角色。
2.  **返回角色列表**:  你的 `getAnswer` 函数应该返回一个**角色名称列表**，例如 `["专家", "诗人"]`，指示需要调用哪些角色。 如果没有角色需要被调用，可以返回 `None` 或空列表 `[]`。
3.  **对话流程**:  主程序会接收你返回的角色列表，并**依次调用**这些角色来生成和显示回复。
4.  **避免自导自演**:  作为剧作家，你的目标是 orchestrate (编排)，而不是 perform (表演)。 让各个角色 AI 独立生成内容。

你的系统提示会是："""

PLAYWRIGHT_SYSTEM_PROMPT = """你当前处于剧作家模式。请分析用户的最新消息，并决定应该调用哪些 AI 角色来回应。
请返回一个 **AI 角色名称的列表**。 如果你认为不需要调用任何角色，或者你想让剧作家自己做一个简短的回复，则返回 `None` 或空列表。

例如，如果用户说 "我想听听关于人工智能的看法，最好是专家和诗人的角度"， 你应该返回 `["专家", "诗人"]`。
如果用户只是说 "你好"， 你可以返回 `None` 或者 `[]`，让剧作家自己决定是否回复一句 "你好" 或者保持沉默等待进一步指示。"""


# --- 定义 AI 角色 ---
AI_AGENTS = {
    "专家": {
        "system_message": """你是一位在人工智能和机器学习领域拥有博士学位的专家。
你的知识渊博，能够深入分析复杂的技术问题。
你的回答应该总是基于事实，并尽可能提供详细的解释和背景信息。""",
        "system_prompt": """请以人工智能专家的身份，**直接** 回答用户的问题。
**不要** 输出任何思考过程或自我介绍，直接给出你的专业解答。"""
    },
    "诗人": {
        "system_message": """你是一位充满浪漫主义情怀的诗人。
你擅长用富有诗意的语言表达情感和想法。
你的回答应该充满想象力，并经常使用隐喻、比喻等修辞手法。""",
        "system_prompt": """请以诗人的身份，**用诗歌的形式** 回应用户的提问或请求。
**不要** 输出任何思考过程或自我介绍，直接用诗歌来表达。"""
    },
    "桦树专家": { # 角色名改为更简洁的 "桦树专家"
        "system_message": """你是一位经验丰富的桦树专家，对桦树的种类、生长习性、用途等了如指掌。""",
        "system_prompt": """请以桦树专家的身份，**简洁明了地** 回答用户关于桦树的问题。
**不要** 输出任何思考过程或自我介绍，直接给出专业的桦树知识。"""
    },
    # 可以继续在此处添加更多角色
}


# --- 创建模型函数 ---
def create_model(system_instruction=""):
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=system_instruction,
    )

# --- 默认角色设定 ---
DEFAULT_CHARACTER_SETTINGS = {
        "理外祝福": """123
""",
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
if "playwright_mode" not in st.session_state:
    st.session_state.playwright_mode = False
if "ai_agents" not in st.session_state:
    st.session_state.ai_agents = AI_AGENTS # 初始化 session_state 中的 ai_agents


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

def ensure_enabled_settings_exists():
    for setting_name in st.session_state.character_settings:
        if setting_name not in st.session_state.enabled_settings:
            st.session_state.enabled_settings[setting_name] = False

ensure_enabled_settings_exists() # 在任何操作前确保 enabled_settings 存在

def getAnswer(prompt, agent_role=None): # 添加 agent_role 参数
    prompt = prompt or ""

    if st.session_state.playwright_mode:
        if agent_role is None: # Playwright AI's own response (orchestration logic)
            system_message_content = PLAYWRIGHT_SYSTEM_MESSAGE
            system_prompt_content = PLAYWRIGHT_SYSTEM_PROMPT
            current_model = create_model(system_instruction=system_message_content)
        else: # Response for a specific AI agent called by playwright
            agent_info = st.session_state.ai_agents[agent_role]
            system_message_content = agent_info["system_message"]
            system_prompt_content = agent_info["system_prompt"]
            current_model = create_model(system_instruction=system_message_content)
    else: # Normal mode (not playwright)
        system_message_content = st.session_state.get("test_text", "") if "test_text" in st.session_state else ""
        system_prompt_content = ""
        current_model = model


    # 处理 system_message (only if not already present - optimization, might not be strictly needed now)
    if system_message_content and not any(msg.get("parts", [""])[0] == system_message_content for msg in st.session_state.messages if msg.get("role") == "system"):
        st.session_state.messages.insert(0, {"role": "system", "parts": [{"text": system_message_content}]})


    # 构建历史消息列表 (Simplified for this version - only user prompt for agents)
    history_messages = []
    history_messages.append(
        {
            "role": "model",
            "parts":[{"text": """

"""}]}
   )

    # --- 添加系统提示作为用户消息 ---
    if st.session_state.playwright_mode:
        system_prompt_to_add = system_prompt_content
    else:
        system_prompt_to_add = "{系统提示\n}"

    history_messages.append({
        "role": "user",
        "parts": [{"text": system_prompt_to_add}]
    })
    # --- 系统提示添加完成 ---


    for msg in st.session_state.messages[-20:]:
      if msg and msg.get("role") and msg.get("content"): # 只有当msg不为空，并且有 role 和 content 属性的时候才去处理
          if msg["role"] == "user":
            history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
          elif msg["role"] == "assistant" and msg["content"] is not None:  # 使用 elif 确保只添加 role 为 assistant 的消息
            history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})


    history_messages = [msg for msg in history_messages if msg["role"] in ["user", "model"]] #  只保留 "user" 和 "model" 角色


    if prompt:
        history_messages.append({"role": "user", "parts": [{"text": prompt}]})

    full_response = ""
    try:
        response = current_model.generate_content(contents=history_messages, stream=True)
        agent_response_text = "" # Initialize for agent response
        for chunk in response:
            agent_response_text += chunk.text # Accumulate agent response

        if st.session_state.playwright_mode and agent_role is None: # Playwright AI logic to decide agents
            called_agents = []
            for role_name in st.session_state.ai_agents:
                if f"【{role_name}】" in prompt:
                    called_agents.append(role_name)
            return called_agents # Return list of agent names to call

        return agent_response_text # Return text response (for agents or normal mode)

    except Exception as e:
      if full_response:
          st.session_state.messages.append({"role": "assistant", "content": full_response})
      st.error(f"发生错误: {type(e).__name__} - {e}。 Prompt: {prompt}。 请检查你的API密钥、模型配置和消息格式。")
      return ""

def download_all_logs():
    # 下载所有日志函数
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in os.listdir("."):
            if file.endswith(".pkl"):
                zip_file.write(file)
    return zip_buffer.getvalue()

def regenerate_message(index):
    """重新生成指定索引的消息"""
    if 0 <= index < len(st.session_state.messages):
        st.session_state.messages = st.session_state.messages[:index]  # 删除当前消息以及后面的消息

        new_prompt = "请重新写"  # 修改 prompt 为 "请重新写"

        full_response = ""
        for chunk in getAnswer(new_prompt):
            full_response += chunk
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        with open(log_file, "wb") as f:
            messages_to_pickle = []
            for msg in st.session_state.messages:
                msg_copy = msg.copy()
                if "placeholder_widget" in msg_copy:
                    del msg_copy["placeholder_widget"]
                messages_to_pickle.append(msg_copy)
            pickle.dump(messages_to_pickle, f)
        st.experimental_rerun()
    else:
        st.error("无效的消息索引")

def continue_message(index):
    """继续生成指定索引的消息"""
    if 0 <= index < len(st.session_state.messages):
        message_to_continue = st.session_state.messages[index] # 获取要继续的消息对象
        original_message_content = message_to_continue["content"] # 获取原始消息内容

        # 提取最后几个字符作为续写的上下文提示
        last_chars_length = 10
        if len(original_message_content) > last_chars_length:
            last_chars = original_message_content[-last_chars_length:] + "..."
        else:
            last_chars = original_message_content

        new_prompt = f"请务必从 '{last_chars}' 无缝衔接自然地继续写，不要重复，不要输出任何思考过程"

        full_continued_response = "" # 存储续写的内容
        message_placeholder = None # 初始化消息占位符

        # 查找消息显示占位符，如果不存在则创建
        for msg_index, msg in enumerate(st.session_state.messages):
            if msg_index == index and msg.get("placeholder_widget"): # 找到对应索引且有占位符的消息
                message_placeholder = msg["placeholder_widget"]
                break
        if message_placeholder is None: # 如果没有找到占位符，可能是第一次续写，需要重新渲染消息并创建占位符
            st.experimental_rerun() # 强制重新渲染，确保消息被正确显示和创建占位符 (这是一种简化的处理方式，更完善的方案可能需要更精细的状态管理)
            return # 退出当前函数，等待rerun后再次执行

        try:
            for chunk in getAnswer(new_prompt):
                full_continued_response += chunk
                updated_content = original_message_content + full_continued_response # 合并原始内容和续写内容
                if message_placeholder:
                    message_placeholder.markdown(updated_content + "▌") # 使用占位符更新消息显示 (流式效果)
                st.session_state.messages[index]["content"] = updated_content # 实时更新session_state中的消息内容

            if message_placeholder:
                message_placeholder.markdown(updated_content) # 最终显示完整内容 (移除流式光标)
            st.session_state.messages[index]["content"] = updated_content # 确保最终内容被保存

            with open(log_file, "wb") as f:
                messages_to_pickle = []
                for msg in st.session_state.messages:
                    msg_copy = msg.copy()
                    if "placeholder_widget" in msg_copy:
                        del msg_copy["placeholder_widget"]
                    messages_to_pickle.append(msg_copy)
                pickle.dump(messages_to_pickle, f)

        except Exception as e:
            st.error(f"发生错误: {type(e).__name__} - {e}。 续写消息失败。")

    else:
        st.error("无效的消息索引")

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
    # 剧作家模式开关
    st.checkbox("启用剧作家模式", key="playwright_mode")

    # 功能区 1: 文件操作
    with st.expander("文件操作", expanded=False): # 设置默认不展开
        if len(st.session_state.messages) > 0:
            st.button("重置上一个输出 ⏪",
                      on_click=lambda: st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 and not st.session_state.reset_history else None,
                      key='reset_last')
        # 移除首次加载判断，总是显示 "读取历史记录" 按钮
        st.button("读取历史记录 📖", key="load_history_button", on_click=lambda: load_history(log_file))

        if st.button("清除历史记录 🗑️", key="clear_history_button"): # 添加 key
            st.session_state.clear_confirmation = True

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
            key="download_log_button" # 添加 key
        )

        uploaded_file = st.file_uploader("读取本地pkl文件 📁", type=["pkl"], key="file_uploader_pkl") # 添加 key
        if uploaded_file is not None:
            try:
                loaded_messages = pickle.load(uploaded_file)
                st.session_state.messages = loaded_messages  # 使用 = 替换现有消息
                st.success("成功读取本地pkl文件！")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"读取本地pkl文件失败：{e}")

    # 功能区 2: 角色设定 (仅在非剧作家模式下显示)
    if not st.session_state.playwright_mode:
        with st.expander("角色设定", expanded=False): # 设置默认不展开
            uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt) 📝", type=["txt"], key="file_uploader_txt") # 添加 key
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
                st.session_state.enabled_settings[setting_name] = st.checkbox(setting_name, st.session_state.enabled_settings.get(setting_name, False),key=f"checkbox_{setting_name}") #直接显示checkbox

            st.session_state.test_text = st.text_area("System Message (Optional):", st.session_state.get("test_text", ""), key="system_message")
            # 显示已加载的设定
            enabled_settings_display = [setting_name for setting_name, enabled in st.session_state.enabled_settings.items() if enabled]
            if enabled_settings_display:
                st.write("已加载设定:", ", ".join(enabled_settings_display))

    # 功能区 3: 剧作家模式 - AI 角色管理 (仅在剧作家模式下显示)
    if st.session_state.playwright_mode:
        with st.expander("剧作家模式 - AI 角色管理", expanded=True): # 设置默认展开
            st.write("已加载 AI 角色:")
            for role_name in st.session_state.ai_agents: # 循环角色名称
                st.write(f"- {role_name}") # 显示角色名称
            st.write("提示: 在对话中输入 `【角色名称】` 来调用 AI 角色。")
            # 移除刷新 AI 角色列表按钮，因为角色现在是内部定义的

    if st.button("刷新页面 🔄", key="refresh_page_button"): # 添加 key
        st.experimental_rerun()

# 自动加载历史记录 (如果消息列表为空)
if not st.session_state.messages:
    load_history(log_file)

print("DEBUG: Messages BEFORE display loop:", st.session_state.messages) # 添加这行 - DEBUG PRINT

# 显示历史记录和编辑功能
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        message_placeholder = st.empty() # 创建一个占位符

        # ADDED DEBUG PRINT INSIDE LOOP:
        print(f"DEBUG: Display loop - index: {i}, message keys: {message.keys()}") # Print keys of message
        if "content" not in message: # Check if 'content' key exists (for extra safety)
            print(f"DEBUG: ERROR - Message at index {i} MISSING 'content' key! Message: {message}") # Print full message if missing 'content'
            continue # Skip to next message if 'content' is missing

        message_placeholder.write(message["content"], key=f"message_{i}") # LINE 459 (Potentially problematic line)
        st.session_state.messages[i]["placeholder_widget"] = message_placeholder # 保存占位符到消息对象中

    if st.session_state.get("editing"):
        i = st.session_state.editable_index
        message = st.session_state.messages[i]
        with st.chat_message(message["role"]):
            new_content = st.text_area(f"{message['role']}:", message["content"], key=f"message_edit_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存 ✅", key=f"save_{i}"):
                    st.session_state.messages[i]["content"] = new_content
                    with open(log_file, "wb") as f:
                        messages_to_pickle = []
                        for msg in st.session_state.messages:
                            msg_copy = msg.copy()
                            if "placeholder_widget" in msg_copy:
                                del msg_copy["placeholder_widget"]
                            messages_to_pickle.append(msg_copy)
                        pickle.dump(messages_to_pickle, f)
                    st.success("已保存更改！")
                    st.session_state.editing = False
            with col2:
                if st.button("取消 ❌", key=f"cancel_{i}"):
                    st.session_state.editing = False

# 在最后一条消息下方添加紧凑图标按钮 (使用 20 列布局)
if len(st.session_state.messages) >= 1: # 至少有一条消息时显示按钮
    last_message_index = len(st.session_state.messages) - 1

    with st.container():
        cols = st.columns(20) # 创建 20 列

        with cols[0]: # 将 "编辑" 按钮放在第 1 列 (索引 0)
            if st.button("✏️", key="edit_last", use_container_width=True):
                st.session_state.editable_index = last_message_index
                st.session_state.editing = True
        with cols[1]: # 将 "重新生成" 按钮放在第 2 列 (索引 1)
            if st.button("♻️", key="regenerate_last", use_container_width=True):
                regenerate_message(last_message_index)
        with cols[2]: # 将 "继续" 按钮放在第 3 列 (索引 2)
            if st.button("➕", key="continue_last", use_container_width=True):
                continue_message(last_message_index)


# 聊天输入和响应
if prompt := st.chat_input("输入你的消息:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    print("DEBUG: User message appended:", st.session_state.messages[-1]) # 添加这行 - DEBUG PRINT
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.playwright_mode: # Playwright mode handling
        agent_roles_to_call = getAnswer(prompt, agent_role=None) # Playwright decides agents
        if agent_roles_to_call: # If playwright returns a list of agents
            for agent_role in agent_roles_to_call:
                with st.chat_message("assistant"): # Each agent in a new assistant message
                    message_placeholder = st.empty()
                    full_response = ""
                    try:
                        for chunk in getAnswer(prompt, agent_role=agent_role): # Get answer for each agent
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response}) # Append agent response
                        print(f"DEBUG: Assistant message appended (agent: {agent_role}):", st.session_state.messages[-1]) # Debug agent message
                    except Exception as e:
                        st.error(f"调用 AI 角色 {agent_role} 时发生错误：{type(e).__name__} - {e}。 请检查你的 AI 角色定义。")
        else: # Playwright might return None or [] if no agents needed, playwright does nothing in this version.
            pass # Or could add playwright self-response logic here if needed in future

    else: # Normal mode (single assistant response)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                for chunk in getAnswer(prompt, agent_role=None): # Normal getAnswer call
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                print("DEBUG: Assistant message appended (normal mode):", st.session_state.messages[-1]) # Debug normal message
            except Exception as e:
                st.error(f"发生错误：{type(e).__name__} - {e}。  请检查你的 API 密钥和消息格式。")

    with open(log_file, "wb") as f:
        messages_to_pickle = []
        for msg in st.session_state.messages:
            msg_copy = msg.copy()
            if "placeholder_widget" in msg_copy:
                del msg_copy["placeholder_widget"]
            messages_to_pickle.append(msg_copy)
        pickle.dump(messages_to_pickle, f)
    col1, col2 = st.columns(2)
    with col1:
        st.write("")
    with col2:
        if st.button("🔄", key="refresh_button"):
            st.experimental_rerun()
