import streamlit as st
import json
from simple_agent.agent import react, MODEL

st.set_page_config(page_title="与昔涟的频道", page_icon="🍑")
st.title("🍑 昔涟的专属频道")
st.markdown("当前使用的模型：`" + MODEL + "` —— *“你答应过要健健康康地等待重逢♪”*")

# 1. 定义双方头像 (你的图片和昔涟的图片)
USER_AVATAR = "user.png"
AI_AVATAR = "xilian.png"

# 2. 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 显示历史聊天记录
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else AI_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 4. 接收用户输入
if prompt := st.chat_input("请输入你的问题（例如：现在几点？帮我算一下 23*17+9）"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):  # 这里替换成了你的头像
        st.markdown(prompt)

    # 调用 Agent，并把历史记录传过去
    with st.chat_message("assistant", avatar=AI_AVATAR): # 这里替换成了昔涟的头像
        with st.spinner("昔涟正在思考..."):
            # 把之前的对话记录（不含当前这句）作为 history 传入
            history = st.session_state.messages[-4:-1]
            
            # 这里调用你写好的 react 函数
            result = react(prompt, history=history)
            
            # 显示最终回答
            answer = result["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # 5. 折叠显示 Trace（保持工程化调试）
            with st.expander("🔍 查看本次执行轨迹 (Trace)"):
                st.json(result["trace"])