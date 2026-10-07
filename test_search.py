import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件里的环境变量
load_dotenv()
api_key = os.getenv("BOCHA_API_KEY")

if not api_key:
    print("❌ 错误：没有在 .env 里找到 BOCHA_API_KEY！")
    exit()

print(f"🔑 正在使用 API Key: {api_key[:10]}...")

url = "https://api.bochaai.com/v1/web-search"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "query": "今天有什么新闻",
    "summary": True,
    "count": 2
}

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"📡 状态码: {resp.status_code}")
    print(f"📄 返回内容: {resp.text}")
except Exception as e:
    print(f"❌ 请求失败: {e}")