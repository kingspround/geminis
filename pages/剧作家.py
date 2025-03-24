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
if 'ai_roles' not in st.session_state:
    st.session_state.ai_roles = {}
if 'active_ai_roles' not in st.session_state:
    st.session_state.active_ai_roles = []
if 'playwright_mode' not in st.session_state:
    st.session_state.playwright_mode = False
if 'playwright_system_message' not in st.session_state:
    st.session_state.playwright_system_message = "你是一个 AI 剧作家，负责管理和协调其他 AI 角色。你的指令具有最高优先级。"
if 'playwright_system_prompt' not in st.session_state:
    st.session_state.playwright_system_prompt = "作为剧作家AI，请根据用户的输入和当前对话场景，选择合适的AI角色出场，并指示它们如何回应用户。你的回复应该引导对话发展，并体现你作为剧作家的控制力。"


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

def getAnswer(prompt):
    prompt = prompt or ""

    # --- 剧作家模式处理开始 ---
    if st.session_state.playwright_mode: # 检查剧作家模式是否启用
        # 重新配置模型 (每次对话都重新配置，确保 system_instruction 更新)
        global model  # 声明 model 为全局变量
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=st.session_state.playwright_system_message  # 设置剧作家 AI 的系统消息作为 system_instruction
        )

        # 构建历史消息列表
        history_messages = []
        history_messages.append(
            {
                "role": "model",
                "parts":[{"text": """

"""}]}
       )

        # --- 优先注入剧作家 AI 的系统提示 (作为用户消息) ---
        if st.session_state.playwright_system_prompt: # 只有当剧作家系统提示不为空时才添加
            history_messages.append({
                "role": "user",
                "parts": [{"text": st.session_state.playwright_system_prompt}]
            })
        # --- 剧作家 AI 系统提示注入完成 ---

        # 处理 test_text (这个部分保持不变，但现在优先级较低)
        if "test_text" in st.session_state and st.session_state.test_text and not any(msg.get("parts", [""])[0] == st.session_state.test_text for msg in st.session_state.messages if msg.get("role") == "system"):
            history_messages.append({"role": "user", "parts": [{"text": "```system\n" + st.session_state.test_text + "\n```"}]}) #  作为用户消息添加，优先级低于剧作家AI


        # 构建启用的角色设定内容 (包括系统提示),  优先级更低
        enabled_settings_content = ""
        if any(st.session_state.enabled_settings.values()): # 如果有启用的全局设定
            enabled_settings_content = "```system\n# Active Settings:\n"
            # 全局角色设定
            for setting_name, enabled in st.session_state.enabled_settings.items():
                if enabled:
                    enabled_settings_content += f"- {setting_name}: {st.session_state.character_settings[setting_name]}\n"
            enabled_settings_content += "```\n"
        if enabled_settings_content: # 角色设定内容作为用户消息添加，优先级低于剧作家AI
            history_messages.append({"role": "user", "parts": [{"text": enabled_settings_content}]})


        role_activation_command = None
        if prompt.endswith(".py"): # 简单的角色激活指令判断 (假设角色名就是文件名，例如 "角色A.py")
            role_name = prompt[:-3] # 去掉 ".py" 后缀
            if role_name in st.session_state.ai_roles:
                role_activation_command = role_name
                prompt = "" # 清空 prompt，因为这只是角色激活指令

        if role_activation_command: # 检测到角色激活指令
            if role_activation_command not in st.session_state.active_ai_roles: # 如果角色尚未激活
                st.session_state.active_ai_roles.append(role_activation_command) # 激活角色
                system_message = st.session_state.ai_roles[role_activation_command]["system_message"]
                if system_message: # 只有当系统消息不为空时才添加
                    st.session_state.messages.append({"role": "system", "parts": [{"text": system_message}]}) # 应用系统消息 (一次性)
                st.info(f"已激活 AI 角色: {role_activation_command}") # 提示信息


        # 激活的 AI 角色系统提示 (作为用户消息添加，优先级低于剧作家AI和全局设定)
        if st.session_state.active_ai_roles:
            ai_roles_prompt_content = "```system\n# Active AI Roles Prompts:\n" # 修改提示文字
            for role_name in st.session_state.active_ai_roles:
                system_prompt = st.session_state.ai_roles[role_name]["system_prompt"]
                if system_prompt: # 只有当系统提示不为空时才添加
                    ai_roles_prompt_content += f"- {role_name}: {system_prompt}\n"
            ai_roles_prompt_content += "```\n"
            history_messages.append({"role": "user", "parts": [{"text": ai_roles_prompt_content}]})


    else: # 非剧作家模式
        # 模型配置恢复默认 system_instruction
        global model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction="""系统消息""", # 恢复默认
        )

        # 处理 test_text (这个部分保持不变)
        if "test_text" in st.session_state and st.session_state.test_text and not any(msg.get("parts", [""])[0] == st.session_state.test_text for msg in st.session_state.messages if msg.get("role") == "system"):
            st.session_state.messages.insert(0, {"role": "system", "parts": [st.session_state.test_text]})

        # 构建启用的角色设定内容 (包括系统提示)
        enabled_settings_content = ""
        if any(st.session_state.enabled_settings.values()):
            enabled_settings_content = "```system\n# Active Settings:\n"
            for setting_name, enabled in st.session_state.enabled_settings.items():
                if enabled:
                    enabled_settings_content += f"- {setting_name}: {st.session_state.character_settings[setting_name]}\n"
            enabled_settings_content += "```\n"


        # 构建历史消息列表
        history_messages = []
        history_messages.append(
            {
                "role": "model",
                "parts":[{"text": """

"""}]}
       )

        # --- 添加额外的提示信息作为用户消息 ---
        history_messages.append({
            "role": "user",  #  使用 "user" 角色
            "parts": [{"text": """{系统提示
"""}] #  提示信息内容
        })
        # --- 提示信息添加完成 ---
        if enabled_settings_content:
            history_messages.append({"role": "user", "parts": [{"text": enabled_settings_content}]})


    # 历史消息 (保持不变，优先级最低)
    for msg in st.session_state.messages[-20:]:
      if msg and msg.get("role") and msg.get("content"): # 只有当msg不为空，并且有 role 和 content 属性的时候才去处理
          if msg["role"] == "user":
            history_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
          elif msg["role"] == "assistant" and msg["content"] is not None:  # 使用 elif 确保只添加 role 为 assistant 的消息
            history_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})


    history_messages = [msg for msg in history_messages if msg["role"] in ["user", "model"]] #  只保留 "user" 和 "model" 角色


    if prompt: # 用户 prompt 优先级最低
        history_messages.append({"role": "user", "parts": [{"text": prompt}]})


    full_response = ""
    try:
        response = model.generate_content(contents=history_messages, stream=True)
        for chunk in response:
            full_response += chunk.text
            yield chunk.text
        return full_response
    except Exception as e:
      if full_response:
          st.session_state.messages.append({"role": "assistant", "content": full_response}) # 保存不完整输出
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
    # 功能区 1: 文件操作
    with st.expander("文件操作"):
        if len(st.session_state.messages) > 0:
            st.button("重置上一个输出 ⏪",
                      on_click=lambda: st.session_state.messages.pop(-1) if len(st.session_state.messages) > 1 and not st.session_state.reset_history else None,
                      key='reset_last')
        # 移除首次加载判断，总是显示 "读取历史记录" 按钮
        st.button("读取历史记录 📖", key="load_history_button", on_click=lambda: load_history(log_file))

        if st.button("清除历史记录 🗑️"):
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
        )

        uploaded_file = st.file_uploader("读取本地pkl文件 📁", type=["pkl"])
        if uploaded_file is not None:
            try:
                loaded_messages = pickle.load(uploaded_file)
                st.session_state.messages = loaded_messages  # 使用 = 替换现有消息
                st.success("成功读取本地pkl文件！")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"读取本地pkl文件失败：{e}")

    # 功能区 2: 角色设定
    with st.expander("角色设定"):
        uploaded_setting_file = st.file_uploader("读取本地设定文件 (txt) 📝", type=["txt"])
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
        if st.button("刷新 🔄"):  # 添加刷新按钮
            st.experimental_rerun()

    # 功能区 3: 剧作家模式
    with st.expander("剧作家模式"):
        st.session_state.playwright_mode = st.checkbox("启用剧作家模式") # 剧作家模式开关
        if st.session_state.playwright_mode:
            st.write("剧作家模式已启用")

            # --- 剧作家 AI 专属配置 ---
            st.subheader("剧作家 AI 配置")
            st.session_state.playwright_system_message = st.text_area(
                "剧作家 AI 系统消息 (System Instruction - 优先级最高, 初始化时设置):",
                st.session_state.playwright_system_message,
                key="playwright_system_message_input"
            )
            st.session_state.playwright_system_prompt = st.text_area(
                "剧作家 AI 系统提示 (User Prompt - 优先级最高, 每次对话注入):",
                st.session_state.playwright_system_prompt,
                key="playwright_system_prompt_input"
            )
            st.write("---")
            # --- 剧作家 AI 配置结束 ---


            # 新建 AI 角色
            if st.button("新建 AI 角色"):
                new_role_name = f"AI角色_{len(st.session_state.ai_roles) + 1}" # 自动生成角色名
                st.session_state.ai_roles[new_role_name] = {
                    "system_message": "我是 AI 角色 " + new_role_name + " 的系统消息，初次收到。",
                    "system_prompt": "我是 AI 角色 " + new_role_name + " 的系统提示，每次对话都收到。",
                }
                st.success(f"已创建 AI 角色: {new_role_name}")
                st.experimental_rerun() # 刷新界面显示新角色

            st.write("---") # 分割线

            # AI 角色列表和编辑
            st.subheader("AI 角色列表")
            for role_name in st.session_state.ai_roles:
                with st.expander(role_name):
                    st.session_state.ai_roles[role_name]["system_message"] = st.text_area(
                        "系统消息 (一次性):",
                        st.session_state.ai_roles[role_name]["system_message"],
                        key=f"system_message_{role_name}"
                    )
                    st.session_state.ai_roles[role_name]["system_prompt"] = st.text_area(
                        "系统提示 (每次对话):",
                        st.session_state.ai_roles[role_name]["system_prompt"],
                        key=f"system_prompt_{role_name}"
                    )
                    # 可以添加删除角色按钮等 (可选)

            # 显示已激活的 AI 角色
            if st.session_state.active_ai_roles:
                st.write("已激活角色:", ", ".join(st.session_state.active_ai_roles))


# 自动加载历史记录 (如果消息列表为空)
if not st.session_state.messages:
    load_history(log_file)

# 显示历史记录和编辑功能
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        message_placeholder = st.empty() # 创建一个占位符
        message_placeholder.write(message["content"], key=f"message_{i}") # 使用占位符显示消息内容
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
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            for chunk in getAnswer(prompt):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"发生错误：{type(e).name} - {e}。  请检查你的 API 密钥和消息格式。")
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
