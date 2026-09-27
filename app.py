import streamlit as st
import json
from simple_agent.agent import react, MODEL

st.set_page_config(page_title="我的 AI Agent", page_icon="🤖")
st.title("🤖 我的第一个 AI Agent")
st.markdown("当前使用的模型：`" + MODEL + "`")

# 1. 初始化聊天记录（给它一个记忆本）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. 显示历史聊天记录（画在网页上）
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. 接收用户输入（用聊天输入框）
if prompt := st.chat_input("请输入你的问题（例如：现在几点？帮我算一下 23*17+9）"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. 调用 Agent，并把之前的聊天记录传给它
    with st.chat_message("assistant"):
        with st.spinner("Agent 正在思考..."):
            # 把之前的对话记录（不含当前这句）作为 history 传入
            history = st.session_state.messages[:-1]
            
            # 这里调用你写好的 react 函数
            result = react(prompt, history=history)
            
            # 显示最终回答
            answer = result["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # 5. 折叠显示 Trace（保持工程化调试）
            with st.expander("🔍 查看本次执行轨迹 (Trace)"):
                st.json(result["trace"])