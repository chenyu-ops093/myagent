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
    return f"""你是一个智能 Agent。你的任务是：{task}

可用工具：
{tool_desc}

历史观察：
{json.dumps(observations, ensure_ascii=False, indent=2)}

【重要规则 - 必须严格遵守】：
1. 每次回复，**只能输出一个 JSON 对象**！绝对不可以一次性输出多个 JSON！
2. 如果你调用了工具并且拿到了结果（比如 get_time 返回了时间），**必须立刻输出 final 类型来回答用户，绝对禁止再调用一次相同的工具**！
3. 严禁连续多次调用同一个工具！如果连续调用同一个工具超过2次，系统会判定你陷入死循环并强行终止。
4. 如果需要计算，调用 calculator。如果需要读取文件，调用 read_file。
5. 请结合【历史对话记录】理解用户的意图。

请只输出一行 JSON，格式二选一：
1. 调用工具：{{"type":"tool","tool":"工具名","args":{{...}}}}
2. 最终回答：{{"type":"final","answer":"你的回答"}}
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

        if decision.get("type") == "tool":
            current_tool = decision.get("tool")
            if current_tool == last_tool:
                repeated_count += 1
                if repeated_count >= 3:
                    return {"answer": "Agent 检测到陷入死循环，已强制停止。", "trace": trace, "status": "loop_detected"}
            else:
                repeated_count = 0
            last_tool = current_tool

        trace.append({"step": step + 1, "decision": decision})

        if decision.get("type") == "final":
            return {"answer": decision.get("answer"), "trace": trace, "status": "completed"}

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