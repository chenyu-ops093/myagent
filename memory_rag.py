import chromadb
from chromadb.config import Settings
import json
import os

class MemoryRAG:
    def __init__(self):
        # 数据库存到本地这个文件夹里
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # 创建一个表（集合）
        self.collection = self.client.get_or_create_collection(name="xilian_memory")

    def add_memory(self, user_text, ai_text):
     if "mount/src" in os.getcwd(): # 判断云端
        return # 云端直接跳过，防止跨用户污染
    # ... 下面是你原来的代码，保持不变 ...
        """把一轮对话存进图书馆"""
        doc_id = str(hash(user_text + ai_text)) # 给这页书做个唯一编号
        content = f"伙伴：{user_text}\n昔涟：{ai_text}"
        
        # 如果已经存过就不重复存
        existing = self.collection.get(ids=[doc_id])
        if existing["ids"]:
            return
            
        self.collection.add(
            documents=[content],
            metadatas=[{"type": "chat"}],
            ids=[doc_id]
        )
    def search_lore(self, query, n_results=3):
        """去故事书架里翻找相关的设定"""
        # 获取专门的设定集合
        lore_collection = self.client.get_or_create_collection(name="xilian_lore")
        if lore_collection.count() == 0:
            return ""
            
        results = lore_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results["documents"] or not results["documents"][0]:
            return ""
            
        lore_str = "\n【关于昔涟的回忆与故事设定】\n"
        for doc in results["documents"][0]:
            lore_str += f"{doc}\n---\n"
        return lore_str
    def search_memory(self, query, n_results=3):
        """根据问题，去图书馆找相关的 3 页书"""
        # 如果图书馆是空的，直接返回空
        if self.collection.count() == 0:
            return ""
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results["documents"] or not results["documents"][0]:
            return ""
            
        # 把找到的记忆拼成一段文字
        memory_str = "\n【与伙伴的记忆碎片】\n"
        for doc in results["documents"][0]:
            memory_str += f"{doc}\n---\n"
        return memory_str

# 创建一个全局实例
import streamlit as st  # 在文件最上面记得加这一行

# ... 上面是你的类代码 ...

# 替换掉原来的 rag = MemoryRAG()
@st.cache_resource(show_spinner=False)
def get_rag():
    return MemoryRAG()

rag = get_rag()