import streamlit as st
import json
from simple_agent.agent import react, MODEL

# 设置网页标题
st.set_page_config(page_title="我的第一个 AI Agent", page_icon="🤖")
st.title("🤖 我的第一个 AI Agent")
st.markdown("当前使用的模型：`" + MODEL + "`")

# 创建一个文本输入框
task = st.text_input("请输入你的任务：", "现在几点？帮我算一下 (25 * 4 + 10) / 2 等于多少，另外把 data 文件夹下的 test.txt 读出来。")

# 创建一个按钮
if st.button("开始执行 🚀"):
    if not task:
        st.warning("请先输入任务哦！")
    else:
        # 显示一个转圈圈的加载状态
        with st.spinner("Agent 正在思考和调用工具中..."):
            # 调用你写好的 react 函数
            result = react(task)
            
            # 显示最终答案
            st.subheader("🎯 最终答案")
            st.success(result["answer"])
            
            # 用折叠面板展示详细的执行轨迹（Trace）
            with st.expander("🔍 查看 Agent 执行轨迹 (Trace)"):
                st.json(result["trace"])