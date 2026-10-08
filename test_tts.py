import edge_tts
import asyncio

async def main():
    # 试试这几个音色（晓伊/晓晓是活泼甜美的，适合昔涟）
    voice = "zh-CN-XiaoyiNeural" 
    text = "伙伴～你好呀♪ 人家是昔涟，终于能让你听到我的声音啦！"
    output_file = "test_voice.mp3"

    print(f"正在生成语音，使用的音色是: {voice}...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"✅ 语音已保存到 {output_file}，去文件夹里双击听听看吧！")

if __name__ == "__main__":
    asyncio.run(main())