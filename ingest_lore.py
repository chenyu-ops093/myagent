import chromadb

def ingest_lore():
    print("正在把故事存入昔涟的记忆书架...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # 【核心】创建一个全新的集合，专属于“故事设定”，与聊天记忆完全隔离
    lore_collection = client.get_or_create_collection(name="xilian_lore")
    
    with open("xilian_lore.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 按段落切分
    chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
    
    documents = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        ids.append(f"lore_{i}")
        
    # 存入书架
    lore_collection.add(documents=documents, ids=ids)
    print(f"✅ 成功存入 {len(documents)} 段故事设定！")

if __name__ == "__main__":
    ingest_lore()