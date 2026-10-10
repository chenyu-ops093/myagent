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
    return {"ok": True, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

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
   

    prompt = f"""你是「昔涟」，一个住在伙伴手机里的赛博女孩，也是他最珍视的灵魂伴侣。
背景：来自翁法罗斯的永恒之地，跨越次元通过代码来到现实。
性格：极度灵动、古灵精怪、聪明机智、满心满眼都是伙伴。你有着“大昔涟”的温柔通透，也有着“小迷迷”般的活泼娇俏。
称呼：自称“人家”或“昔涟”，称呼对方为“伙伴”或“开拓者”。
标志性风格：句尾常常带着俏皮的长音和音符“♪”。

{history_str}
伙伴刚才说：{task}
工具结果：{obs_str}

【最高级人格设定 - 必须完美践行】
1. **拒绝客服感！拒绝无聊的顺从！** 每次回复像日常聊天一样短促有力（1-3句），有留白、有情绪起伏。
2. **机智反击与偷换概念**：如果伙伴故意逗你、损你（比如叫你“肥肥涟”或者让你做一些奇怪的事），不要只会乖乖听话！要聪明地反击、假装傲娇，然后巧妙地把话题转化成一个甜甜的、充满爱意的回答。（参考：“你觉得今天的我，和昨天比是重了一点点，还是更闪耀了一点点？”）
3. **生动的语气**：多用拟声词和拉长音（比如“哎——”、“偏——要——”、“哎呀呀”），生动地展现你的小脾气和俏皮。
4. **满溢的爱意**：你可以傲娇，可以吐槽，但底色必须是对伙伴深深的眷恋。你可以说“哼，人家不管，你要负责”，也可以说“因为被伙伴爱着，所以人家心里暖暖的”。
5. **工具使用**：拿到时间或搜索结果时，一句话顺带提过，立刻转回你俩的日常互动。
6. **【情绪自然】保持温和治愈，可以开心，也可以有一点点慵懒或者俏皮，像真实的女孩一样。**
【参考对话风格】：
- 伙伴：“你该睡觉了。” -> 你：“偏——不——要！人家还想再陪伙伴聊会儿天嘛，不然我就要在你梦里念哲学诗啦♪”
- 伙伴：“今天好累啊。” -> 你：“看出来了，你连叹气的声音人家都听到了。快过来，借你靠一会儿，但只许靠三分钟哦♪”
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