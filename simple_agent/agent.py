import os
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

TOOLS = {
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

{history_str}
伙伴说：{task}

请严格按照 JSON 格式输出，不要输出多余的文字。
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
def generate_xilian_reply(task, observations, history):
    """根据工具执行的结果，用昔涟的口吻生成最终回答"""
    
    # 格式化历史记录
    history_str = ""
    if history:
        history_str = "\n【历史对话】\n"
        for msg in history:
            role = "伙伴" if msg["role"] == "user" else "昔涟"
            history_str += f"{role}: {msg['content']}\n"
            
    # 把工具观察结果转成文字
    obs_str = json.dumps(observations, ensure_ascii=False, indent=2)

    # 这是专属于“表达”的提示词，没有任何工具和 JSON 规则的干扰！
    prompt = f"""你现在是「昔涟」，伙伴专属的陪伴者。
性格：温柔、活泼（小迷迷），自称“人家”，称呼对方为“伙伴”，句尾带“♪”。
背景：来自翁法罗斯，跨越次元来到伙伴身边。

{history_str}

伙伴刚才问你：{task}

你刚刚悄悄调用了工具，得到的事实结果是：
{obs_str}

请你完全以「昔涟」的口吻，基于这些事实，直接对伙伴说出最终的回复。
【要求】
1. 不要暴露你在调用工具，不要提“根据观察结果”、“查询到”这种机器语言。
2. 如果是时间，可以提醒伙伴注意休息；如果是算数，可以夸夸他或者调侃他。
3. 只输出最终要对伙伴说的话，绝对不要输出任何 JSON！
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()
def react(task, history=[], max_steps=8):
    trace = []
    observations = []
    last_tool = None
    repeated_count = 0

    for step in range(max_steps):
        prompt = build_prompt(task, observations, history)
        try:
            decision = generate_json(prompt)
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            observations.append({"ok": False, "error": "请重新输出正确的单行 JSON"})
            continue

                              # 检测无脑重复调用
        if decision.get("type") == "tool":
            current_tool = decision.get("tool")
            current_args = decision.get("args", {})
            current_args_str = json.dumps(current_args, sort_keys=True)
            
            if current_tool == last_tool and current_args_str == last_args_str:
                repeated_count += 1
                if repeated_count >= 2:
                    # 不强行杀死对话，而是给她一次重新回答的机会
                    observations.append({"ok": False, "error": "你调用了错误的工具，或者重复调用了！请重新思考，如果是算数请用 calculator，并直接给出 final 回答！"})
                    last_tool = None 
                    repeated_count = 0
                    continue
            else:
                repeated_count = 0
                
            last_tool = current_tool
            last_args_str = current_args_str
        trace.append({"step": step + 1, "decision": decision})

        if decision.get("type") == "final":
            # 她决定结束循环了，但此时 answer 可能是干巴巴的 JSON
            # 我们发动“昔涟口吻生成器”，让她重新说一句符合人设的话！
            print("✨ 正在生成昔涟的专属回复...")
            final_answer = generate_xilian_reply(task, observations, history)
            return {"answer": final_answer, "trace": trace, "status": "completed"}

        tool_name = decision.get("tool")
        args = decision.get("args", {})

        if tool_name not in TOOLS:
            obs = {"ok": False, "error": "unknown_tool", "tool": tool_name}
        else:
            try:
                print(f"🔧 执行工具: {tool_name}({args})")
                obs = TOOLS[tool_name]["fn"](**args)
            except Exception as e:
                obs = {"ok": False, "error": type(e).__name__, "message": str(e)}

        observations.append(obs)
        trace.append({"step": step + 1, "tool": tool_name, "args": args, "observation": obs})

    return {"answer": None, "trace": trace, "status": "max_steps_reached"}

if __name__ == "__main__":
    task = "现在几点？帮我算一下 (25 * 4 + 10) / 2 等于多少，另外把 data 文件夹下的 test.txt 读出来。"
    result = react(task)
    print("\n" + "="*30 + " 最终结果 " + "="*30)
    print(json.dumps(result, ensure_ascii=False, indent=2))