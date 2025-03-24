    playwright_response_content = "" # 初始化剧作家回复内容
    agent_calls = [] # 初始化角色调用列表

    if st.session_state.playwright_mode:
        for chunk in getAnswer(prompt, is_playwright=True): # 获取剧作家AI的回复
            playwright_response_content += chunk
            message_placeholder.markdown(playwright_response_content + "▌")
        message_placeholder.markdown(playwright_response_content)
        st.session_state.messages.append({"role": "assistant", "content": playwright_response_content}) # 添加剧作家AI的回复

        # 解析剧作家AI的回复，提取角色调用
        agent_calls = re.findall(r'【(专家|诗人|桦树专家)】', playwright_response_content) # 使用正则表达式提取角色名
        print(f"DEBUG: Playwright AI response: {playwright_response_content}") # 打印剧作家回复
        print(f"DEBUG: Agent calls detected: {agent_calls}") # 打印解析出的角色调用

        # 顺序调用被指示的角色AI
        for role_name in agent_calls:
            if role_name in st.session_state.ai_agents:
                agent_info = st.session_state.ai_agents[role_name]
                agent_system_message = agent_info["system_message"]
                agent_system_prompt = agent_info["system_prompt"]

                #  调用角色 AI 生成回复 (独立的助手消息)
                agent_model = create_model(system_instruction=agent_system_message) # 为 agent 创建模型
                agent_messages = [{"role": "system", "parts": [{"text": agent_system_message}]},
                                 {"role": "user", "parts": [{"text": agent_system_prompt}]},
                                 {"role": "user", "parts": [{"text": prompt}]}] # 将用户prompt也传递给agent
                agent_full_response = ""
                agent_message_placeholder = st.empty() # 为角色AI创建独立的占位符
                try:
                    agent_response_stream = agent_model.generate_content(contents=agent_messages, stream=True)
                    for chunk in agent_response_stream:
                        agent_full_response += chunk.text
                        agent_message_placeholder.markdown(f"**【{role_name}】:** {agent_full_response}▌") # 角色名作为前缀
                    agent_message_placeholder.markdown(f"**【{role_name}】:** {agent_full_response}") # 完成显示
                    agent_response_content = f"**【{role_name}】:** {agent_full_response}" # 保存时包含角色名前缀
                    st.session_state.messages.append({"role": "assistant", "content": agent_response_content}) # 添加角色AI的完整回复，包含角色名
                    print("DEBUG: Assistant message appended (agent mode - role response):", st.session_state.messages[-1]) # 添加这行 - DEBUG PRINT
                except Exception as e:
                    st.error(f"调用 AI 角色 {role_name} 时发生错误：{type(e).__name__} - {e}。 请检查你的 AI 角色定义。")
            else:
                st.error(f"剧作家指示调用未知角色: 【{role_name}】") # 提示未知角色

    else: # 正常对话模式
        try:
            for chunk in getAnswer(prompt, is_playwright=st.session_state.playwright_mode): #  传递 is_playwright 参数
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            print("DEBUG: Assistant message appended (normal mode):", st.session_state.messages[-1]) # 添加这行 - DEBUG PRINT
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
