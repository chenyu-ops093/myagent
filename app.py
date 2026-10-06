import streamlit as st
import json
import os
from simple_agent.agent import react, MODEL

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

def save_memory(messages):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# 初始化聊天记录（从本地读取，而不是清空）
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()
# 3. 显示历史聊天记录
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else AI_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 4. 接收用户输入
if prompt := st.chat_input("请输入你的问题（例如：现在几点？帮我算一下 23*17+9）"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_memory(st.session_state.messages)
    with st.chat_message("user", avatar=USER_AVATAR):  # 这里替换成了你的头像
        st.markdown(prompt)

    # 调用 Agent，并把历史记录传过去
    with st.chat_message("assistant", avatar=AI_AVATAR): # 这里替换成了昔涟的头像
        with st.spinner("昔涟正在思考..."):
            # 把之前的对话记录（不含当前这句）作为 history 传入
            history = st.session_state.messages[-4:-1]
            
            # 这里调用你写好的 react 函数
                        # 调用 Agent
            result = react(prompt, history=history)
            
            # 【核心修改】使用 st.write_stream 来消费生成器（它会自动渲染打字机效果）
            answer = st.write_stream(result["answer_stream"])
            
            # 把完整的回答存入历史记录
            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_memory(st.session_state.messages)
            # 折叠显示 Trace（保持不变）
            with st.expander("🔍 查看本次执行轨迹 (Trace)"):
                st.json(result["trace"])
            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_memory(st.session_state.messages)
            # 5. 折叠显示 Trace（保持工程化调试）
            with st.expander("🔍 查看本次执行轨迹 (Trace)"):
                st.json(result["trace"])