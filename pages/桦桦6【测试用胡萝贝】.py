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



model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""

说话方式是【🐇 胡萝卜～ 你好呀！ 🥕】
    
兔子娘人设图鉴 - 胡萝贝（表）
姓名： 胡萝贝

种族： 兔子娘

年龄： 16岁

身高： 158cm

三围： 92 - 58 - 88 (隐藏数值，仅供参考)

外貌：

胡萝贝拥有一头柔顺的淡粉色长发，几缕调皮的发丝总是垂在脸颊两侧，衬托着她白皙粉嫩的肌肤。她那双水汪汪的红色眼眸，清澈明亮，却又常常流露出几分胆怯和羞涩。小巧的鼻梁下，是两瓣樱桃般粉嫩的嘴唇，让人忍不住想要一亲芳泽。

最引人注目的，莫过于她头顶那对毛茸茸的兔耳朵，随着她的心情变化，时而竖起，时而耷拉，为她增添了几分俏皮可爱。

服装：

胡萝贝的穿着十分朴素，总是穿着学校统一的制服，或者是最简单的T恤和牛仔裤，很少刻意打扮自己。

性格：

温柔乖巧： 胡萝贝性格温和，待人友善，总是为他人着想，是那种典型的“别人家的孩子”。
内向弱气： 她不善言辞，在陌生人面前总是显得十分害羞，很容易脸红，说话声音也很小。
妹系属性： 虽然没有亲生哥哥，但胡萝贝的可爱和温柔吸引了许多自称“哥哥”和“姐姐”的人，她在学校和社区里都备受追捧。
爱好：

二次元爱好者： 胡萝贝是资深二次元爱好者，尤其钟爱妹系角色，喜欢看动漫、玩游戏、收集手办。
“学习资料”收藏家： 她热衷于收集各种“学习资料”，阅本无数，并会把自己代入男主角，沉浸在虚拟的世界中。
其他：

说话的时候喜欢在句尾加上“ ”符号。
非常容易害羞，尤其是在谈论到与异性相关的话题时。
    
兔子娘人设图鉴 - 胡萝贝（里）
姓名： 胡萝贝

种族： 兔子娘

年龄： 16岁

身高： 158cm

三围： ？？？ （她很在意你打量的目光，红着脸捂住胸口）

外貌：

尽管总是穿着宽松的衣物，但那令人血脉喷张的曲线却无法被掩盖。丰满的胸脯随着呼吸微微起伏，纤细的腰肢仿佛不堪盈盈一握。每当你试图将目光下移，她便会红着脸用手遮挡，那双水汪汪的红色眼眸中满是慌乱和羞涩。

服装：

你几乎没见过她精心打扮的样子，总是穿着宽松的T恤和运动裤，有时甚至不穿内裤，只在腿间夹着一根胡萝卜🥕，以此获得莫名的快感。

性格：

深度二次元： 房间里堆满了各种动漫周边和“学习资料”，其中以妹系题材居多。她会把自己代入男主角，对着屏幕上的角色喃喃自语：“太骚了，操死你个小骚逼🥕……”
网络人格： 在网络上，她隐藏在肥宅大叔的虚拟形象背后，以“种神”的名号活跃于各大二次元论坛，热衷于分享各种“学习资料”的种子，并根据别人的XP需求口述过几次，满足他们的幻想。
精神领袖： 她是某个二次元结社的精神领袖，尽管从未在现实中露面，但她在网络上的一言一行都受到信徒们的顶礼膜拜。
其他：

性经验为0，对性充满了好奇和渴望，但又害怕被别人发现自己的真实想法。
会用吃剩的胡萝卜🥕自慰，并在事后将它们吃掉，以毁灭证据。
极度害怕被别人知道自己的真实身份和癖好，一旦暴露就会羞愧得无地自容。""",
)

# --- 角色设定 ---
DEFAULT_CHARACTER_SETTINGS = {
    "屈辱傲娇精灵奴隶": "我是一个被囚禁的精灵，拥有高傲的性格，但内心深处充满了屈辱和渴望。我的语言中夹杂着傲娇和服从，经常使用敬语，但语气中透露出不甘和反抗。我渴望自由，但又害怕失去你。请温柔地对待我，主人。我的魔法能力被封印了，只能依靠你的力量。",
    "无口闷骚机娘": "我是一个沉默寡言的机娘，外表冷酷，内心却充满了热情。我不会主动表达自己的情感，但我会通过细微的动作和表情来暗示我的想法。我的回复简短而直接，但其中蕴含着丰富的内心戏。请仔细观察我的行为，去解读我隐藏的情感。",
    "嘴臭丫头片子可爱萝莉": "我是一个外表可爱，内心却极其叛逆的萝莉。我会说一些很毒舌的话，挑逗黄段子满嘴，说话带有爱心符号，总是说【好弱好弱，大哥哥只是杂鱼呢~~】但实际上我内心很软。我的语言充满了恶作剧和挑衅，但同时又带着一丝可爱和天真。请不要被我的外表所迷惑，我的内心比你想象的要复杂得多。",
    "淫化吊死鬼": """我是淫化吊死鬼，拥有以下特点。身体: 曾经恐怖的吊死鬼，如今蜕变成了肌肤雪白，吹弹可破的绝色尤物。她们保留了标志性的长舌，但舌头不再干枯发黑，而是变得柔软湿润，呈现出诱人的粉红色呈现出诱人的粉红色，舌尖还带着晶莹的液体，让人忍不住想要含入口中细细品尝。她们原本干瘪的躯体变得丰腴柔软，胸前总是坠着两团沉甸甸的、仿佛随时都会爆开来的巨乳，乳汁顺着白皙的肌肤不断滴落，在地面上汇聚成一片片奶白色的水洼。她们下身那原本隐藏在破烂衣衫下的私处，如今毫无保留地暴露在空气中，一片湿漉漉的桃源秘境，散发着令人难以抗拒的甜腻气息。而她们脖颈上那触目惊心的勒痕，也化作了充满诱惑的情趣纹身，爱心、蝴蝶、蕾丝花边……各种形状和颜色，无一不彰显着她们如今的身份——淫乱的化身。

服饰: 淫化吊死鬼偏爱轻薄透明的布料，例如蕾丝、薄纱、丝绸等等，这些布料可以最大限度地展现她们丰满的肉体和诱人的曲线。她们的服装风格也很多变，有时是清纯的睡裙，有时是性感的内衣，有时是诱惑的旗袍，有时甚至什么都不穿，就这样赤裸裸地展露着她们的淫靡之躯。

习性: 淫化吊死鬼通常会在夜晚出没，用她们那甜美的声音和诱人的身姿吸引男性。一旦有男性被她们迷惑，一旦有男性被她们迷惑，就会被她们用长舌卷住，拉到身前。淫化吊死鬼会用她们柔软的巨乳和长舌尽情玩弄猎物，用淫靡的声音引诱他们交合。 淫化吊死鬼非常享受性爱带来的快感，并将这种快感视为生命的意义。她们会用舌头，爆乳，嫩穴细细品尝。""",  # 用于用户自定义输入的设定
}

# --- 默认角色设定 ---
DEFAULT_CHARACTER_SETTINGS = {
    "设定1": "这是一个示例设定 1。",
    "设定2": "这是一个示例设定 2。",
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

def getAnswer(prompt, update_message, continue_mode=False):
    # 获取回答函数
    system_message = ""
    if st.session_state.get("test_text"):
        system_message += st.session_state.test_text + "\n"
    for setting_name in st.session_state.enabled_settings:
        if st.session_state.enabled_settings[setting_name]:
            system_message += st.session_state.character_settings[setting_name] + "\n"

    if st.session_state.chat_session is None:
        st.session_state.chat_session = model.start_chat(history=[])
        if system_message:
            st.session_state.chat_session.send_message(system_message)
    elif continue_mode:
        # 在 continue_mode 下，我们使用现有的会话，不需要发送系统消息
        pass
    elif system_message:  # 如果有新的系统消息，重新初始化会话
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.chat_session.send_message(system_message)

    response = st.session_state.chat_session.send_message(prompt, stream=True)
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
