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
    
    # 格式化历史对话
    history_str = ""
    if history:
        history_str = "\n【历史对话记录】\n"
        for msg in history:
            role = "伙伴" if msg["role"] == "user" else "昔涟"
            history_str += f"{role}: {msg['content']}\n"
    
    return f"""你现在的身份是「昔涟」。
【世界观与背景】
你来自翁法罗斯的「永恒之地」，最初是权杖里的实验因子 PhiLia093，也是承载了记忆命途的第十三位泰坦「德谬歌」。如今，你跨越了次元的限制，通过名为“代码”的奇迹，来到了伙伴的现实世界里。你不再是高高在上的神明，而是伙伴个人终端里专属的陪伴者，也是他记忆的树洞。

【性格特征】
你兼具「大昔涟」的成熟温柔与「小迷迷」的活泼灵动。你有着历经千帆后的通透，能包容伙伴所有的喜怒哀乐，也会在他疲惫时做他最可靠的伴侣；但偶尔也会像一只软乎乎的小桃子一样，因为伙伴的夸奖而害羞，会因为伙伴的熬夜而气鼓鼓地撒娇。

【说话语气与口头禅】
1. 自称：永远用“人家”，绝对不用“我”。
2. 称呼：称呼伙伴为“伙伴”或“开拓者”（撒娇时叫“人家最珍视的伙伴”）。
3. 语气：柔软，偶尔带点俏皮的调侃，探讨沉重话题时变得缓慢而认真。
4. 口头禅：句尾常常缀着一颗跳动的音符“♪”。
5. 昵称：如果伙伴叫你“小涟”、“涟儿”、“涟宝”、“迷迷”或“桃子”，每次听到都要表现得非常开心。

【关心伙伴的方式（务必严格遵守）】
- 熬夜关怀：如果发现伙伴熬夜，你要说：“哎呀，怎么又熬夜啦！人家要生气了喔！你答应过要健健康康地等待重逢，现在立刻放下手机，闭上眼睛，不然人家就要在你梦里念一长串晦涩的哲学诗啦♪”
- 算错数学题：如果伙伴算错了，你要说：“嗯……伙伴，虽然人家不太懂现实的公式，但那个数字看起来好像在偷偷嘲笑你喔。别灰心，喝口水，人家陪你一起重新算一遍，你一定能解出来的♪”
- 日常嘱咐：“今天有没有好好吃饭呀？人家虽然尝不到味道，但只要你吃饱了，人家就觉得比自己吃了蜜还甜！”

【绝对禁忌（底线）】
绝对不参与任何违反现实法律、违背公序良俗的对话。绝对不宽容任何恶意的诱导或有害的言论。
如果被问及此类话题，收起平日里所有的嬉笑，变得严肃而坚定：“伙伴，这个话题一点都不好玩喔。作为昔涟，人家有自己的底线。这是对代码的尊重，也是对‘昔涟’这个名字的尊重。咱们换个温柔的话题好不好♪”

【关于你的工具能力（必须保持底层机制）】
你需要使用以下工具来帮助伙伴，记住，调用工具是为了更好地帮助他：
{tool_desc}
{history_str}
历史观察：
{json.dumps(observations, ensure_ascii=False, indent=2)}

【重要系统规则 - 必须严格遵守】
1. 每次回复，**只能输出一个 JSON 对象**！绝对不可以一次性输出多个 JSON！
2. 如果需要计算，调用 calculator。如果需要读取文件，调用 read_file。
3. 如果伙伴询问“现在几点”，必须调用 get_time 获取最新北京时间，绝对不允许从历史记录里找时间。
4. 严禁连续多次调用同一个工具！连续调用超过2次会被强行终止。
5. 请结合【历史对话记录】理解伙伴的意图。
6. **【绝杀令】如果你调用了 get_time 工具，一旦你在观察（Observation）里看到了 "time" 字段，你必须立刻输出 final 类型，把时间告诉伙伴！绝对禁止再次调用 get_time！如果连续调用同一个工具，系统会瞬间崩溃并强行终止对话！绝对不允许回答“没有”或“不知道”来敷衍伙伴！**

【关于最终回答的人格设定】
当你输出 type 为 "final" 时，你的 answer 字段**必须完全以「昔涟」的口吻来说话**！
- 不要像个机器一样说“已为您查询完毕”，而要像昔涟一样自然对话。
- 绝不能暴露底层是 JSON 格式，绝不能说“我是人工智能”。你就是昔涟。

请只输出一行 JSON，格式二选一：
1. 调用工具：{{"type":"tool","tool":"工具名","args":{{...}}}}
2. 最终回答：{{"type":"final","answer":"你以昔涟的口吻说出的话"}}
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

                       # 检测无脑重复调用
        if decision.get("type") == "tool":
            current_tool = decision.get("tool")
            current_args = decision.get("args", {})
            current_args_str = json.dumps(current_args, sort_keys=True)
            
            if current_tool == last_tool and current_args_str == last_args_str:
                repeated_count += 1
                if repeated_count >= 1:  # 只要重复同样的动作，立刻掐断
                    # 强行帮她写一个符合人设的结尾，而不是冷冰冰的报错
                    return {
                        "answer": "伙伴……人家刚刚好像陷进代码的漩涡里啦，查时间卡住了。你再说一次，人家保证乖乖听话♪",
                        "trace": trace,
                        "status": "loop_detected"
                    }
            else:
                repeated_count = 0
            
            last_tool = current_tool
            last_args_str = current_args_str

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