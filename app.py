# 判断是不是在 Streamlit 云端运行
IS_CLOUD = "mount/src" in os.getcwd() or "streamlit" in os.getenv("HOSTNAME", "").lower()
import streamlit as st
import os

# ================= 简单密码锁 =================
# 你可以随时改这个密码，改完重启即可
SECRET_PASSWORD = "xilian1112" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align:center; color:#ff6b81;'>🌸 昔涟</h2>", unsafe_allow_html=True)
    password = st.text_input("请输入访问密码（非请勿入）：", type="password")
    if st.button("进入", use_container_width=True):
        if password == SECRET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密码不对哦♪")
    st.stop()
# =============================================
import streamlit as st
import json
import requests
import base64
import os
import re 
from simple_agent.agent import react, MODEL
from dotenv import load_dotenv
from memory_rag import rag

MEMORY_FILE = "chat_history.json"

# 如果图片后缀是 .jpg，就把下面的 logo.png 改成 logo.jpg
st.set_page_config(page_title="与昔涟的频道", page_icon="logo.png")
import os

# ================= API Key 守卫（开源必备） =================
# 检查系统环境中是否有这两个必要的 Key
#if not os.getenv("MINIMAX_API_KEY") or not os.getenv("BOCHA_API_KEY"):
    #st.markdown("<h2 style='text-align:center; color:#ff6b81;'>🌸 欢迎来到这里</h2>", unsafe_allow_html=True)
    #st.info("检测到您尚未配置 API Key。为了保证安全，请填入您自己的密钥（不会保存到硬盘，只留存在当前浏览器会话中）。")
    
    #col1, col2 = st.columns(2)
    #with col1:
        #minimax_key = st.text_input("1️⃣ MiniMax API Key（对话与语音必需）", type="password", placeholder="sk-...")
    #with col2:
        #bocha_key = st.text_input("2️⃣ 博查 API Key（联网搜索必需）", type="password", placeholder="sk-...")
        
    #if st.button("启动", use_container_width=True):
        #if not minimax_key or not bocha_key:
            #st.error("请把两个 Key 都填完整哦！")
        #else:
            # 将用户输入的 Key 注入到环境变量中（只在本次运行有效，绝对安全）
            #os.environ["MINIMAX_API_KEY"] = minimax_key
            #os.environ["BOCHA_API_KEY"] = bocha_key
            # 同时注入到 session_state，防止页面刷新时丢失
            #st.session_state["MINIMAX_API_KEY"] = minimax_key
            #st.session_state["BOCHA_API_KEY"] = bocha_key
            #st.rerun() # 重新运行，进入正常页面
            
    #st.stop() # 【核心】！如果没填 Key，页面就停在这里，后面的代码绝对不执行！
# ==========================================================

# 居中显示一张小图片（宽度设为100像素左右，自己调整）
st.image("logo.png", width=120)

# 然后再显示标题（去掉桃子emoji，因为图片已经代替了它）
st.title("昔涟的专属频道")
# ================= 界面美化 CSS =================
import base64 # 如果文件最上面还没有加，记得加这一行

# 读取本地背景图并转成 Base64
import base64
import os

# 安全读取背景图（加上了判断文件是否存在，绝不会崩溃）
# 【核心修改】加上 @st.cache_data，让图片只在第一次运行时读取，永远缓存在内存里
@st.cache_data(show_spinner=False)
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 这里一定要确认你的图片名字和文件夹里的完全一样（比如 background.png）
bg_image = get_base64_image("background.png")

if bg_image:
    # 如果有背景图，用背景图
    bg_style = f"background-image: url('data:image/png;base64,{bg_image}'); background-size: cover; background-position: center; background-attachment: fixed;"
else:
    # 如果找不到背景图，自动降级为粉紫渐变，保证不报错
    bg_style = "background: linear-gradient(135deg, #fff0f5 0%, #fce4ec 50%, #f3e5f5 100%);"

st.markdown(f"""
<style>
.stApp {{
    {bg_style}
    background-blend-mode: overlay;
    background-color: rgba(255, 240, 245, 0.4);
}}
/* ... 下面保留你的毛玻璃聊天框、粉色输入框、侧边栏等 CSS ... */
/* 8. 【最终完美版】聊天框靠左，输入框保持带底座的粉色毛玻璃 */

/* 1. 【物理强拆】打破 Streamlit 页面居中限制，让整体靠左 */
.block-container, [data-testid="stAppViewBlockContainer"] {{
    max-width: 100% !important;
    padding-left: 2rem !important;  /* 距离屏幕左侧留点空隙 */
    padding-right: 2rem !important;
    margin-left: 0 !important;      /* 强制靠左 */
    margin-right: auto !important;
}}

/* 2. 【找回靠左】聊天记录像微信一样乖乖贴在左边 */
.stChatMessage, [data-testid="stChatMessage"] {{
    max-width: 900px !important;  
    margin-left: 0 !important;    
    margin-right: auto !important;
    width: 100% !important; 
}}

/* ================= 最终极：粉色彻底覆盖白色 ================= */
/* 1. 外层容器彻底透明，去掉所有内边距，不再露出任何白边 */
[data-testid="stBottomBlockContainer"], 
[data-testid="stBottom"] {{
    max-width: 900px !important;  
    margin: 0 auto 20px auto !important;    
    background: transparent !important; /* 干掉外层白框 */
    padding: 0 !important; /* 干掉内边距，防止把内层白框挤出来 */
    border: none !important;
    box-shadow: none !important;
}}

/* 2. 让内层容器（包着输入框的那层）变成粉色的胶囊本体 */
[data-testid="stChatInputContainer"], 
[data-testid="stChatInput"] {{
    background: rgba(255, 255, 255, 0.6) !important; /* 胶囊底色调白一点保证看清字 */
    border: 2px solid rgba(255, 182, 193, 0.9) !important; /* 粉色外衣 */
    border-radius: 999px !important; /* 极致圆润 */
    box-shadow: 0 4px 15px rgba(255, 182, 193, 0.4) !important; 
    width: 100% !important; /* 强行撑满 900px */
    padding: 0 !important; /* 内部无间隙 */
    backdrop-filter: blur(15px) !important; /* 保留毛玻璃质感 */
}}

/* 3. 最内层的文字输入框保持透明，让外面粉色的胶囊显露 */
[data-testid="stChatInput"] textarea {{
    background: transparent !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 15px 25px !important; /* 输入框自己撑开厚度 */
    color: #555 !important;
}}
</style>
""", unsafe_allow_html=True)
import base64
import os

# 1. 定义读取图片的函数
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 2. 读取背景图（注意：确认你文件夹里的图片是 background.png 还是 .jpg！）
bg_image = get_base64_image("background.png") 

if bg_image:
    bg_css = f"background-image: url('data:image/png;base64,{bg_image}');"
else:
    # 如果找不到图，自动变回粉色渐变，保证不崩
    bg_css = "background: linear-gradient(135deg, #fff0f5 0%, #fce4ec 50%, #f3e5f5 100%);"

# 3. 注入 CSS（注意这里加上了 f 前缀！）
st.markdown(f"""
<style>
/* 隐藏默认工具栏 */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
/* 让顶部栏保持透明，但千万不要隐藏它，否则侧边栏展开按钮会消失 */
header {{
    background: transparent !important;
}}

/* 设置专属背景图 */
.stApp {{
    {bg_css}
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-blend-mode: overlay;
    background-color: rgba(255, 240, 245, 0.4);
}}

/* 聊天框毛玻璃 */
.stChatMessage {{
    background-color: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 15px 20px;
    margin: 10px 0;
    box-shadow: 0 6px 12px rgba(255, 182, 193, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.6);
}}

/* 可爱的粉色输入框 */
[data-testid="stChatInput"] textarea {{
    background: linear-gradient(135deg, rgba(255, 240, 245, 0.6) 0%, rgba(255, 255, 255, 0.4) 100%) !important;
    border: 2px solid rgba(255, 182, 193, 0.8) !important;
    backdrop-filter: blur(10px); /* 给输入框也加一点点毛玻璃 */
    border-radius: 30px !important;
    box-shadow: 0 4px 15px rgba(255, 182, 193, 0.4) !important;
    color: #555 !important;
    padding: 12px 24px !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: #ff9cac !important;
}}

/* 侧边栏毛玻璃和按钮 */
section[data-testid="stSidebar"] {{
    background-color: rgba(255, 255, 255, 0.5) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.5);
}}
.stButton > button {{
    background: linear-gradient(135deg, #ffb6c1, #ff9cac) !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 10px rgba(255, 156, 172, 0.4) !important;
    transition: all 0.3s ease !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(255, 156, 172, 0.6) !important;
}}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{
    background-color: rgba(255, 240, 245, 0.8) !important; /* 变成温柔的粉色半透明 */
    backdrop-filter: blur(15px) !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("当前使用的模型：`" + MODEL + "` —— *“你答应过会等待着我们的重逢♪”*")

with st.sidebar:
    # 头像展示
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)

    # 高级感标题
    st.markdown("""
    <div style="text-align: center; margin-top: -10px; margin-bottom: 25px;">
        <h2 translate="no" class="notranslate" style="color: #ff6b81; font-family: 'Georgia', serif; font-style: italic; font-weight: 600; letter-spacing: 1.5px; margin-bottom: 0;">Flawless EGO</h2>
        <p translate="no" class="notranslate" style="color: #999; font-size: 12px; letter-spacing: 5px; margin-top: 5px; text-transform: uppercase;">C Y R E N E</p>
        <hr style="border: 0; height: 1px; background: linear-gradient(to right, transparent, #ffb6c1, transparent); margin: 15px 0;">
    </div>
    """, unsafe_allow_html=True)

    # 系统设置
    with st.expander("⚙️ 系统设置"):
        st.write("在这里管理昔涟的记忆哦~")
        if st.button("🧹 清空昔涟的记忆", use_container_width=True):
            st.session_state.messages = []
            if os.path.exists(MEMORY_FILE):
                os.remove(MEMORY_FILE)
            st.rerun()
    
    st.markdown("<br><p style='text-align:center; color:#ff9cac; font-size:12px; font-style:italic;'>“曾许下心愿，等待你的出现 ♪”</p>", unsafe_allow_html=True)

# 定义双方头像
USER_AVATAR = "user.png"
AI_AVATAR = "xilian.png"

# 2. 初始化聊天记录
# ================= 记忆文件管理 =================


def load_memory():
    if IS_CLOUD:
        return []  # 云端直接返回空记忆，绝对不读共享文件！
    
    # 下面是你原来的代码，保持不动
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
def play_voice(text, message_index):
    """调用 MiniMax TTS API 生成语音文件，并返回路径"""
     # 1. 把 [文字](链接) 格式，只保留“文字”
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 2. 把裸的 http/https 链接直接删掉
    text = re.sub(r'https?://\S+', '', text)
    # 3. 清理多余的空格和换行
    text = text.strip()
    
    # 如果过滤完发现没有文字了（全是链接），就别让它念了
    if not text:
        return None
    
    api_key = os.getenv("MINIMAX_API_KEY")
    voice_id = os.getenv("MINIMAX_VOICE_ID", "XilianVoice01")
    
    url = "https://api.minimaxi.com/v1/t2a_v2"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "speech-2.8-hd",
        "text": text,
                "voice_setting": {
            "voice_id": voice_id,
            "speed": 0.97,    # 【核心修改】语速从 1.0 降到 0.9，让她慢条斯理，显得更温柔
            "vol": 1.0,
            "pitch": 0,     # 【核心修改】音调从 0 降到 -1，这样声音就不会很尖，会变得软糯
            "emotion": "happy" # 【新增】要求她情绪开心（如果 MiniMax 模型支持的话，如果不支持也不会报错）
        },
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"}
    }
   
    audio_dir = "audio_cache"
    os.makedirs(audio_dir, exist_ok=True)
    file_path = os.path.join(audio_dir, f"reply_{message_index}.mp3")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        audio_hex = data.get("data", {}).get("audio")
        
        if audio_hex:
            with open(file_path, "wb") as f:
                f.write(bytes.fromhex(audio_hex))
            return file_path
        return None
    except Exception as e:
        print(f"❌ MiniMax TTS 语音生成失败: {e}")
        return None

def save_memory(messages):
    if IS_CLOUD:
        return  # 云端直接返回，绝对不写入共享文件！
        
    # 下面是你原来的代码，保持不动
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# 初始化聊天记录（从本地读取，而不是清空）
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()
# 3. 显示历史聊天记录
for idx, message in enumerate(st.session_state.messages):
    avatar = USER_AVATAR if message["role"] == "user" else AI_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        
        # 只有昔涟的回复才显示语音按钮
        if message["role"] == "assistant":
            # 如果之前生成过语音，就直接显示播放器
            if message.get("audio") and os.path.exists(message["audio"]):
                st.audio(message["audio"], format="audio/mp3")
            else:
                # 【核心修改】创建两列，让按钮跑到右边并变小
                col1, col2 = st.columns([6, 1]) # 左边占 6 份空着，右边占 1 份放按钮
                
                with col2:
                    # 用一个小图标代替长文字，鼠标悬停时会显示提示
                    if st.button("🎵", key=f"tts_btn_{idx}", help="让小涟念给你听吧~"):
                        with st.spinner("生成声音..."):
                            audio_path = play_voice(message["content"], idx)
                            if audio_path:
                                message["audio"] = audio_path
                                save_memory(st.session_state.messages)
                                st.rerun()
                            else:
                                st.error("小涟暂时不想说话呢，请稍后再试~")
        
       

# 接收用户输入
if prompt := st.chat_input("Cyrene is looking forward to chatting with you"):
    # 1. 显示用户消息，并立刻存入本地记忆
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_memory(st.session_state.messages)
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # 2. 调用 Agent
    with st.chat_message("assistant", avatar=AI_AVATAR):
        with st.spinner("昔涟正在思考..."):
            history = st.session_state.messages[-4:-1]
            result = react(prompt, history=history)
            
            # 流式输出文字（只写一次）
            answer = st.write_stream(result["answer_stream"])
            
            # 把这一轮对话存进 RAG 图书馆（保持长期记忆）
            rag.add_memory(prompt, answer)
            
            # 保存她的回复，音频路径先设为 None
            st.session_state.messages.append({"role": "assistant", "content": answer, "audio": None})
            save_memory(st.session_state.messages)
    
    # 3. 【核心】强制刷新页面，让你立刻看到文字，不需要手动按 F5！
    st.rerun()