import streamlit as st
import json
import requests
import os
from simple_agent.agent import react, MODEL
from dotenv import load_dotenv 
from memory_rag import rag

MEMORY_FILE = "chat_history.json"

# 如果图片后缀是 .jpg，就把下面的 logo.png 改成 logo.jpg
st.set_page_config(page_title="与昔涟的频道", page_icon="logo.png")

# 居中显示一张小图片（宽度设为100像素左右，自己调整）
st.image("logo.png", width=120)

# 然后再显示标题（去掉桃子emoji，因为图片已经代替了它）
st.title("昔涟的专属频道")
st.markdown("当前使用的模型：`" + MODEL + "` —— *“你答应过会等待着我们的重逢♪”*")
with st.sidebar:
    st.markdown("### ⚙️ 系统设置")
    if st.button("清空昔涟的记忆 🧹"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
        st.rerun()
# 1. 定义双方头像 (你的图片和昔涟的图片)
USER_AVATAR = "user.png"
AI_AVATAR = "xilian.png"

# 2. 初始化聊天记录
# ================= 记忆文件管理 =================


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
def play_voice(text, message_index):
    """调用 MiniMax TTS API 生成语音文件，并返回路径"""
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
            "speed": 0.9,    # 【核心修改】语速从 1.0 降到 0.9，让她慢条斯理，显得更温柔
            "vol": 1.0,
            "pitch": -2,     # 【核心修改】音调从 0 降到 -1，这样声音就不会很尖，会变得软糯
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
                # 如果还没生成，就显示一个“点播”按钮
                if st.button("🎵 让涟宝念给我听", key=f"tts_btn_{idx}"):
                    with st.spinner("正在生成声音..."):
                        audio_path = play_voice(message["content"], idx)
                        if audio_path:
                            message["audio"] = audio_path
                            save_memory(st.session_state.messages)
                            st.rerun()
                        else:
                            st.error("语音生成失败，请重试")
        
       

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