import os
from openai import OpenAI

print("正在测试 API 连接...")
print("当前 BASE_URL:", os.getenv("OPENAI_BASE_URL"))
print("当前 MODEL:", os.getenv("MODEL"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

try:
    response = client.chat.completions.create(
        model=os.getenv("MODEL", "MiniMax-Text-01"),
        messages=[{"role": "user", "content": "你好，请回复一句话"}]
    )
    print("\n✅ API 连接成功！回复内容：")
    print(response.choices[0].message.content)
except Exception as e:
    print("\n❌ API 连接失败！错误信息：")
    print(e)