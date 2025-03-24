
请根据场景和角色, **选择合适的脚本**, 并**决定它们的执行顺序**, 生成这样的剧本指令.
如果某些脚本不适合当前场景, 可以不用。 至少选择一个脚本。
生成的指令文本只需要包含 "使用脚本:" 和 "执行顺序:" 两部分，以及脚本文件名列表和执行步骤。
"""

    response_content = ""
    for chunk in getAnswer(prompt): # 使用你现有的 getAnswer 函数
        response_content += chunk
    return response_content

def execute_script_instructions(script_instructions, pages_dir=PAGES_DIR):
    """
    执行剧本指令，按照顺序运行指定的 XXX.py 脚本。

    Args:
        script_instructions (str): 剧作家生成的剧本指令文本。
        pages_dir (str):  pages 目录路径。

    Returns:
        list:  包含每个脚本执行结果的列表 (可以根据脚本输出调整)。
    """
    script_names_to_execute = []
    execution_order = []

    # 解析剧本指令 (简单的文本解析)
    lines = script_instructions.strip().split('\n')
    for line in lines:
        if line.startswith("使用脚本:"):
            script_names_line = line.split("使用脚本:")[1].strip()
            script_names_to_execute = [name.strip() for name in script_names_line.split(",") if name.strip()]
        elif line.startswith("执行顺序:"):
            execution_order_start_index = lines.index(line) + 1
            for i in range(execution_order_start_index, len(lines)):
                order_line = lines[i].strip()
                if order_line.startswith(str(i - execution_order_start_index + 1) + "."): # 简单判断序号
                    script_file_name = order_line.split(".")[1].strip()
                    if script_file_name in script_names_to_execute: # 验证脚本是否在 "使用脚本" 列表中
                        execution_order.append(script_file_name)

    execution_results = []
    if not execution_order:
        return ["没有有效的执行脚本指令。"]

    for script_file in execution_order:
        script_path = os.path.join(pages_dir, script_file)
        if os.path.exists(script_path) and os.path.isfile(script_path):
            st.info(f"执行脚本: {script_file}")
            try:
                # 方法一: 使用 subprocess 运行 (更安全，隔离性更好)
                command = [sys.executable, script_path] # 使用当前 Python 解释器
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate(timeout=30) # 设置超时时间，防止脚本无限期运行

                if process.returncode == 0:
                    script_output = stdout
                    st.code(script_output, language="python") # 显示脚本输出
                    execution_results.append(f"{script_file} 执行成功:\n{script_output}")
                else:
                    error_message = stderr
                    st.error(f"{script_file} 执行出错:\n{error_message}")
                    execution_results.append(f"{script_file} 执行出错:\n{error_message}")

                # 方法二: 使用 importlib 动态导入和执行 (更灵活，但需注意安全风险)
                # spec = importlib.util.spec_from_file_location(script_file, script_path)
                # module = importlib.util.module_from_spec(spec)
                # sys.modules[script_file] = module
                # spec.loader.exec_module(module)
                # execution_results.append(f"{script_file} 执行 (使用 importlib，输出捕获需要脚本自身实现)")

            except subprocess.TimeoutExpired:
                st.error(f"{script_file} 执行超时!")
                execution_results.append(f"{script_file} 执行超时!")
            except Exception as e:
                st.error(f"执行脚本 {script_file} 发生错误: {e}")
                execution_results.append(f"执行脚本 {script_file} 发生错误: {e}")
        else:
            st.warning(f"脚本文件 {script_file} 不存在或无法访问。")
            execution_results.append(f"脚本文件 {script_file} 不存在或无法访问。")
    return execution_results

def generate_playwright_script(scene_description, characters_description, api_key_variable_name="YOUR_API_KEY"):
    """
    生成 Python 剧本代码，使用 Gemini API 进行对话和场景模拟。

    Args:
        scene_description (str): 场景描述。
        characters_description (str): 角色描述。
        api_key_variable_name (str):  在生成的脚本中，API 密钥占位符的变量名。

    Returns:
        str: 生成的 Python 剧本代码。
    """

    prompt = f"""
你是一位AI剧作家，请编写一个Python脚本，文件名为 `play.py`。
这个脚本的功能是使用 `google.generativeai` 库和 Gemini 模型来创作一个剧本场景。

场景描述:
{scene_description}

角色描述:
{characters_description}

剧本脚本需要完成以下任务：

1. **导入必要的库**: 导入 `google.generativeai` 和 `os` 库。
2. **配置 Gemini API**:  使用环境变量 `{api_key_variable_name}` 作为 Gemini API 密钥。
3. **设定场景和角色**: 在脚本中明确场景和角色设定，可以基于用户描述进行扩展。
4. **编写对话和场景模拟逻辑**:
    -  设计一个简单的对话流程，例如让角色轮流对话。
    -  使用 Gemini 模型生成对话内容和场景描述。
    -  脚本需要决定何时以及如何调用 Gemini 模型，可以根据场景发展或角色互动来决定。
    -  可以多次调用 Gemini 模型来推进剧情或丰富对话。
5. **输出剧本**: 将生成的剧本内容（包括对话和场景描述）打印到控制台。
6. **添加注释**:  在代码中添加清晰的注释，解释每个部分的功能。
7. **错误处理**:  简单处理 API 调用可能出现的错误。

请提供完整的 `play.py` 脚本代码，确保代码可以直接运行（用户需要替换 API 密钥）。
脚本应该展示如何使用 Gemini 进行对话和场景模拟，并体现一定的“自我判断”来决定 AI 的调用次数和顺序。

**请注意：** 生成的脚本只需要是一个可以运行的示例，不需要非常复杂或完美。重点是展示如何使用 Gemini API 在 Python 脚本中进行剧本创作。
"""

    response_content = ""
    for chunk in getAnswer(prompt): # 使用你现有的 getAnswer 函数
        response_content += chunk
    return response_content


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

    # --- 新增 AI 剧作家 功能区 ---
    with st.expander("AI 剧作家 (脚本编排) 🎬"):
        st.subheader("生成剧本指令并执行")
        scene_input = st.text_area("场景描述:", placeholder="例如：未来城市，两个AI角色在争论谁应该控制能源系统。")
        characters_input = st.text_area("角色描述:", placeholder="例如：角色A：能源管理AI；角色B：城市安全AI。")

        available_scripts = get_available_scripts() # 获取可用脚本列表
        st.write(f"可用脚本: {', '.join(available_scripts) or 'pages 目录下没有找到 Python 脚本'}")

        if available_scripts: # 只有当有可用脚本时才显示生成按钮
            if st.button("生成剧本指令"):
                if scene_input and characters_input:
                    with st.spinner("正在生成剧本指令..."):
                        script_instructions = generate_playwright_script_instructions(scene_input, characters_input, available_scripts)
                        st.session_state.script_instructions = script_instructions # 保存指令
                    st.success("剧本指令生成完成！")
                else:
                    st.warning("请填写场景描述和角色描述。")

            if "script_instructions" in st.session_state:
                st.subheader("剧本指令:")
                st.code(st.session_state.script_instructions, language="plaintext")

                if st.button("执行剧本"):
                    with st.spinner("正在执行剧本..."):
                        execution_results = execute_script_instructions(st.session_state.script_instructions)
                        st.session_state.execution_results = execution_results # 保存执行结果
                    st.success("剧本执行完成！")

        if "execution_results" in st.session_state:
            st.subheader("剧本执行结果:")
            for result in st.session_state.execution_results:
                st.write(result) # 逐个显示执行结果

    # --- 新增 剧本脚本生成 功能区 ---
    with st.expander("AI 剧本脚本生成 🎬"):
        st.subheader("生成剧本脚本 (play.py)")
        script_scene_input = st.text_area("脚本场景描述:", placeholder="例如：两个人在咖啡馆里讨论一个秘密计划。")
        script_characters_input = st.text_area("脚本角色描述:", placeholder="例如：角色A：一位紧张的年轻记者；角色B：一位冷静的老练的侦探。")

        if st.button("生成剧本脚本 (play.py)"):
            if script_scene_input and script_characters_input:
                with st.spinner("正在生成剧本脚本..."):
                    script_code = generate_playwright_script(script_scene_input, script_characters_input)
                    st.session_state.generated_script = script_code # 保存生成的脚本到 session_state
                st.success("剧本脚本生成完成！")
            else:
                st.warning("请填写场景描述和角色描述。")

        if "generated_script" in st.session_state:
            st.download_button(
                label="下载剧本脚本 (play.py) ⬇️",
                data=st.session_state.generated_script,
                file_name="play.py",
                mime="text/plain",
            )
            st.code(st.session_state.generated_script, language="python") # 显示生成的代码


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
