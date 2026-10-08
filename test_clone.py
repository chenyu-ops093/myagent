import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("MINIMAX_API_KEY")
# 如果你还没配 MINIMAX_API_KEY，可以直接在下面临时写：
# API_KEY = "你的新Key"

# ⚠️ 注意：这里必须是 api.minimaxi.com
BASE_URL = "https://api.minimaxi.com/v1"

def upload_file(file_path):
    """第一步：上传音频文件获取 file_id"""
    url = f"{BASE_URL}/files/upload"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    # 注意这里的参数名是 file，purpose 是 voice_clone
    files = {
        "file": open(file_path, "rb")
    }
    data = {
        "purpose": "voice_clone"
    }
    
    print("正在上传音频文件...")
    resp = requests.post(url, headers=headers, files=files, data=data)
    print("上传接口返回:", resp.text)
    if resp.status_code == 200:
        return resp.json().get("file", {}).get("file_id")
    return None

def clone_voice(file_id, custom_voice_id="XilianVoice01"):
    """第二步：使用 file_id 克隆专属音色"""
    url = f"{BASE_URL}/voice_clone"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "file_id": file_id,
        "voice_id": custom_voice_id
    }
    
    print("正在克隆音色...")
    resp = requests.post(url, headers=headers, json=payload)
    print("克隆接口返回:", resp.text)
    return resp.json()

if __name__ == "__main__":
    # 替换为你本地的音频文件名
    audio_file = "xilian_sample.mp3"
    
    if not os.path.exists(audio_file):
        print(f"❌ 找不到音频文件: {audio_file}，请确认是否在 myagent 文件夹下！")
    else:
        file_id = upload_file(audio_file)
        if file_id:
            print(f"✅ 文件上传成功，file_id: {file_id}")
            result = clone_voice(file_id)
            print("✅ 音色克隆完成！请查看上方返回结果里的 voice_id。")
        else:
            print("❌ 文件上传失败，请检查上方报错。")