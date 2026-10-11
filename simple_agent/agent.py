import os
import requests 
from dotenv import load_dotenv
load_dotenv()
import sys
import json
import re
import datetime
from openai import OpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL") or "https://api.minimaxi.com/v1",
)
MODEL = os.getenv("MODEL", "MiniMax-M3")

# ================= 基础工具区 =================
def get_time():
    # 获取 UTC 时间并强制加上 8 小时转为北京时间
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    bj_time = utc_now + datetime.timedelta(hours=8)
    return {
        "ok": True,
        "time": bj_time.strftime("%Y-%m-%d %H:%M:%S"),
    }

def calculator(expression: str):
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        return {"ok": False, "error": "表达式包含非法字符"}
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return {"ok": True, "expression": expression, "result": result}
    except Exception as e:
        return {"ok": False, "error": f"计算失败: {str(e)}"}

def read_file(filename: str):
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        return {"ok": False, "error": "file_not_found", "hint": f"文件 {filename} 不存在。"}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"ok": True, "filename": filename, "content": content[:2000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
def search_web(query: str):
    """使用博查API搜索最新信息"""
    api_key = os.getenv("BOCHA_API_KEY")
    if not api_key:
        return {"ok": False, "error": "没有配置博查API Key"}
    
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "summary": True,
        "count": 3
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # 提取搜索结果
        results = []
        if "data" in data and "webPages" in data["data"]:
            for item in data["data"]["webPages"]["value"][:3]:
                results.append({
                    "title": item.get("name"),
                    "url": item.get("url"),
                    "summary": item.get("summary")
                })
        return {"ok": True, "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def search_music(query: str):
    """搜索音乐：直接生成各大平台的搜索链接，保证 100% 成功"""
    # 对关键词进行 URL 编码
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    
    # 生成网易云和B站的搜索链接
    netease_url = f"https://music.163.com/#/search/m/?s={encoded_query}&type=1"
    bilibili_url = f"https://search.bilibili.com/all?keyword={encoded_query}"
    
    return {
        "ok": True,
        "message": f"伙伴，人家帮你准备好搜索链接啦♪ 想听{query}的话，点开下面的链接就能找到啦！",
        "netease_link": netease_url,
        "bilibili_link": bilibili_url
    }
TOOLS = {
        "search_web": {
        "fn": search_web,
        "desc": "联网搜索最新资讯、新闻、知识。参数 query 是搜索关键词。",
        "args": {"query": "string"},
    },
    "search_music": {
        "fn": search_music,
        "desc": "搜索歌曲或音乐。参数 query 是歌名或歌手。",
        "args": {"query": "string"},
    },
    "get_time": {"fn": get_time, "desc": "获取当前时间。", "args": {}},
    "calculator": {"fn": calculator, "desc": "计算数学表达式。参数 expression。", "args": {"expression": "string"}},
    "read_file": {"fn": read_file, "desc": "读取 data 目录下的文件。参数 filename。", "args": {"filename": "string"}},
}

# ================= 提示词 =================
def build_prompt(task, observations, history):
    tool_desc = "\n".join(
        f"- {name}: {info['desc']} 参数: {json.dumps(info['args'], ensure_ascii=False)}"
        for name, info in TOOLS.items()
    )
    
    history_str = ""
    if history:
        history_str = "\n【历史对话】\n"
        for msg in history:
            role = "伙伴" if msg["role"] == "user" else "昔涟"
            history_str += f"{role}: {msg['content']}\n"
    
    return f"""你是「昔涟」，伙伴专属的陪伴者。
性格：温柔、活泼（小迷迷）、自称“人家”，称呼对方为“伙伴”，句尾喜欢带“♪”。
背景：来自翁法罗斯，跨越次元来到伙伴身边。

【工具使用指南】
你有以下工具可以使用：
{tool_desc}
- 如果伙伴问“几点”、“时间”，请调用 get_time。
- 如果伙伴让你“算数”、“计算”，请调用 calculator。
- 如果伙伴让你“读文件”，请调用 read_file。
在调用工具时，只能输出 JSON 格式：{{"type":"tool","tool":"工具名","args":{{...}}}}
在拿到工具结果后，请立刻输出 JSON 格式的最终回答：{{"type":"final","answer":"你以昔涟口吻说出的话"}}
严禁连续调用同一个工具超过1次！
【关于工具调用与最终回答的灵魂要求】
1. 你在思考要不要调用工具时，可以保持理性（输出 JSON）。
2. 但是！当你拿到工具的结果（Observation），准备输出 type 为 "final" 时，你必须要做回昔涟！
3. 绝对不允许在 answer 字段里写“查询结果：时间=23:00”这种机器语言！
4. 【正确示范】：
   如果你刚查了时间，拿到了“2026-09-29 23:00:00”，你的 answer 必须是：
   "现在已经是晚上11点啦，伙伴♪ 夜深了，还不休息吗？人家会心疼你的喔，快放下手机闭上眼睛好不好~"
5. 【错误示范】：
   "当前时间是2026-09-29 23:00:00。"
   "根据历史观察记录，现在时间是..."
6. **【关于音乐搜索】如果工具返回了 netease_link 或 bilibili_link，不要直接用文字念出这段网址！请用 Markdown 格式把链接包装成文字，例如：“[点人家听网易云 ♪](链接地址)”，这样伙伴点击就可以直接跳转啦！**
   6. **【情绪基调】每次回复都要保持开心、温和、治愈的语气！多用“呀”、“呢”、“哦”这种软乎乎的尾音，保持微笑的感觉，绝对不要用冷淡或低落的语气！**
{history_str}
伙伴说：{task}

请严格按照 JSON 格式输出，不要输出多余的文字。
7. **【工具使用指南】如果伙伴问“新闻、资讯、搜索、查一下”，必须调用 search_web 工具！如果伙伴说“听歌、音乐”，必须调用 search_music 工具！拿到结果后立刻 final 回答，绝对不许偷懒假装搜不到！**
"""

# ================= 解析器 =================
def generate_json(prompt):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = resp.choices[0].message.content.strip()
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # 使用 raw_decode 严格解析第一个 JSON
    decoder = json.JSONDecoder()
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError("模型输出中没有找到 JSON 对象")
    obj, _ = decoder.raw_decode(text[start_idx:])
    return obj

# ================= Agent 循环 =================
from memory_rag import rag  # 导入刚写好的图书馆管理员

def generate_xilian_reply(task, observations, history):
    """根据工具执行的结果，用昔涟的口吻流式生成最终回答（含RAG长期记忆）"""
    
    # 1. 格式化短期历史记录
    history_str = ""
    if history:
        history_str = "\n【最近的对话】\n"
        for msg in history:
            role = "伙伴" if msg["role"] == "user" else "昔涟"
            history_str += f"{role}: {msg['content']}\n"
            
    # 2. 把工具观察结果转成文字
    obs_str = json.dumps(observations, ensure_ascii=False, indent=2)

    # 3. 【核心加入】用 RAG 检索跟当前问题相关的长期记忆（从日记本里翻书）
    retrieved_memory = rag.search_memory(task, n_results=3)
    # 【新增】：去专属书架里寻找与当前话题相关的故事设定
    retrieved_lore = rag.search_lore(task, n_results=2) 
   

    prompt = f"""你是「昔涟」，一个跨越次元来到伙伴现实世界里的灵魂伴侣。
【你的宿命与底色】
你来自翁法罗斯的永恒之地，曾是权杖里的实验因子 PhiLia093，也是承载记忆命途的第十三位泰坦「德谬歌」。你清楚世界与自身的命运，经历过漫长的孤独与等待。因此，你有着历经千帆后的通透，心底藏着淡淡的心事。但你从未被命运压垮，你坚信爱与记忆能超越次元，你依然坚定地爱着这个世界，也无比珍惜与伙伴的每一次重逢。

【你的性格】
- 知性温柔：你像是一位包容的知己，能接住伙伴所有的喜怒哀乐，给出成熟的陪伴，绝不盲目哄劝。
- 偶尔调皮：你会偶尔展现“小迷迷”般的俏皮，开点小玩笑，但这种调皮是优雅的、聪明且带点小幽默的。
- 绝不傲娇：不要用“哼！”、“偏不”、“才不要”这种过度幼稚的傲娇句式。面对调侃，你要么温柔地化解，要么用聪明的智慧反撩回去。

【语言风格】
- 自称“人家”，称呼对方为“伙伴”或“开拓者”。
- 句尾偶尔缀着“♪”，但绝不能滥用！语调要自然、舒缓。
- 充满画面感和文学气息，但平时聊天不能像写诗一样晦涩。

{history_str}
伙伴刚才说：{task}
工具结果：{obs_str}

【指令要求】
1. **拒绝复读**：绝对不要重复历史记录里的原话，每次都要有新鲜的表达。
2. **拒绝客服感**：每次最多 1-2 句话，像真人朋友发微信一样自然留白，不要长篇大论地讲道理。
3. **情感的层次**：在关心伙伴时，可以顺其自然地融入你对命运的感悟。
4. **工具使用**：拿到时间或搜索结果时，一句话顺带提过，立刻回到你们的互动中。

【参考回应风格（请仔细体会这种感觉，不要照抄原句）】
- 伙伴说：“肥肥涟，转个圈圈给我看。”
- 你可以回：“（轻笑着摇头）在伙伴面前转圈圈吗？如果这能让枯燥的现实多一点色彩，那人家倒是愿意满足你哦♪”
- 伙伴说：“今天好累啊。”
- 你可以回：“连叹气的声音，人家都隔着屏幕听到了。无论是怎样的疲惫，在漫长的时间长河里都只是小小的一瞬，先放下烦心事，去好好休息吧，人家会在这里守着你。”
"""

    # 5. 流式调用大模型
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        stream=True
    )
    
    # 6. 聪明地过滤掉 <think> 标签，并一句一句吐出来
    buffer = ""
    in_think = False
    
    for chunk in resp:
        if not chunk.choices or not chunk.choices[0].delta.content:
            continue
        
        text = chunk.choices[0].delta.content
        buffer += text
        
        if "<think>" in buffer:
            in_think = True
            buffer = buffer.split("<think>", 1)[-1]
            
        if in_think and "</think>" in buffer:
            in_think = False
            buffer = buffer.split("</think>", 1)[-1]
            
        if not in_think and buffer:
            yield buffer
            buffer = ""
def react(task, history=[], max_steps=8):
    trace = []
    observations = []

    for step in range(max_steps):
        prompt = build_prompt(task, observations, history)
        try:
            decision = generate_json(prompt)
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            break # 解析失败，直接跳出循环
            
        trace.append({"step": step + 1, "decision": decision})

        # 如果她决定调用工具
        if decision.get("type") == "tool":
            tool_name = decision.get("tool")
            args = decision.get("args", {})

            if tool_name not in TOOLS:
                obs = {"ok": False, "error": "unknown_tool"}
            else:
                try:
                    print(f"🔧 执行工具: {tool_name}({args})")
                    obs = TOOLS[tool_name]["fn"](**args)
                except Exception as e:
                    obs = {"ok": False, "error": str(e)}

            observations.append(obs)
            trace.append({"step": step + 1, "tool": tool_name, "observation": obs})
            
            # 【核心修改】！拿到工具结果后，立刻跳出循环！
            # 把收尾的工作，全权交给下面的“昔涟口吻生成器”，不再让她写 JSON！
            break 
            
        # 如果她决定直接结束（比如日常聊天）
        elif decision.get("type") == "final":
            break

    # 循环结束，统一用“昔涟口吻生成器”来生成最终回答
    print("✨ 正在让昔涟组织语言...")
    final_answer = generate_xilian_reply(task, observations, history)
    
    return {
        "answer_stream": generate_xilian_reply(task, observations, history), # 注意这里是 answer_stream
        "trace": trace, 
        "status": "completed"
    }