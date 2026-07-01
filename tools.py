"""
工具模块 —— Agent 可以调用的各种工具
通过 @tool 装饰器自动注册，无需手写 Function Calling Schema
"""

import datetime
import inspect
import json
import math
import re
from pathlib import Path
from typing import get_origin, get_args, Literal

import requests
import urllib3
from memory import LongTermMemory

# 屏蔽 SSL 警告（DDG Lite 在国内需要 verify=False）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from travel_data import get_city, get_attractions, estimate_daily_cost, get_all_cities, CURRENCY_RATES

# 复用 HTTP 连接（减少 TCP 握手开销）
_http = requests.Session()
_http.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
_http.verify = False

# ======================================================================
# @tool 装饰器 —— 自动注册工具，从类型注解 + docstring 生成 schema
# ======================================================================

TOOL_REGISTRY: list[dict] = []


def tool(name: str = None, description: str = None):
    """
    将函数注册为 Agent 可用工具。
    自动提取：函数名、类型注解、docstring → Function Calling Schema

    用法:
        @tool
        def my_tool(param1: str, param2: int = 0):
            \"\"\"工具描述\n\n:param param1: 参数1说明\n:param param2: 参数2说明\"\"\"
            ...

        @tool(name="别名", description="自定义描述")
        def my_tool():
            ...
    """
    # === 支持 @tool 无括号用法 ===
    if callable(name):
        decorator = tool()
        return decorator(name)

    def decorator(func):
        tool_name = name or func.__name__
        doc = func.__doc__.strip() if func.__doc__ else ""
        tool_desc = description or doc.split("\n\n")[0].strip().replace("\n", " ") if doc else ""

        sig = inspect.signature(func)
        properties = {}
        required = []

        # 类型映射（Python → JSON Schema）
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # — 推断参数类型和 enum —
            param_type = "string"
            enum_values = None

            if param.annotation != inspect.Parameter.empty:
                origin = get_origin(param.annotation)
                if origin is Literal:
                    param_type = "string"
                    args = get_args(param.annotation)
                    enum_values = [str(a) for a in args]
                else:
                    param_type = type_map.get(param.annotation, "string")

            prop = {"type": param_type}
            if enum_values:
                prop["enum"] = enum_values

            properties[param_name] = prop

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        # — 从 docstring 提取参数描述 :param name: desc —
        if doc:
            for line in doc.split("\n"):
                m = re.search(r":param\s+(\w+)\s*:\s*(.+)", line)
                if m and m.group(1) in properties:
                    properties[m.group(1)]["description"] = m.group(2).strip()

            # 没有用 :param: 语法的参数，直接用名字作为描述
            for pname in properties:
                if "description" not in properties[pname]:
                    properties[pname]["description"] = pname

        # — 组装 OpenAI Function Calling Schema —
        parameters = {"type": "object", "properties": properties}
        if required:
            parameters["required"] = required

        tool_schema = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_desc,
                "parameters": parameters,
            },
        }

        TOOL_REGISTRY.append({
            "func": func,
            "name": tool_name,
            "description": tool_desc,
            "parameters": tool_schema,
        })

        return func

    return decorator


# ======================================================================
# 辅助函数（非工具）
# ======================================================================

def _safe_eval(expression: str) -> str:
    """安全执行数学表达式，只允许白名单内的函数"""
    allowed = {
        "abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "pi": math.pi, "e": math.e,
        "int": int, "float": float,
    }
    for name in set(re.findall(r"\b[a-zA-Z_]\w*\b", expression)):
        if name not in allowed and name != "__builtins__":
            return f"错误：不允许使用 '{name}'"
    try:
        result = eval(expression, {"__builtins__": {}}, {k: v for k, v in allowed.items() if callable(v)})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def _load_todos() -> list:
    todo_file = Path(__file__).parent / "todos.json"
    if todo_file.exists():
        try:
            return json.loads(todo_file.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_todos(todos: list):
    todo_file = Path(__file__).parent / "todos.json"
    todo_file.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")


# ======================================================================
# 工具函数 —— 每个 @tool 自动注册到 TOOL_REGISTRY
# ======================================================================

# ----- 通用工具 -----


@tool
def get_current_time() -> str:
    """获取当前日期和时间（年-月-日 时:分:秒 星期），无参数"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")


@tool
def calculate(expression: str) -> str:
    """执行数学计算（支持 + - * / ** sqrt sin 等）

    :param expression: 数学表达式，如 '2+2'、'sqrt(16)'、'sin(pi/2)'
    """
    return _safe_eval(expression)


@tool
def read_file(filepath: str) -> str:
    """读取项目目录下的文件内容（安全限制：只能读项目内文件）

    :param filepath: 相对项目目录的文件路径
    """
    base_dir = Path(__file__).parent
    target = (base_dir / filepath).resolve()
    if not str(target).startswith(str(base_dir)):
        return "错误：不允许访问项目目录外的文件"
    if not target.exists():
        return f"错误：文件不存在 ({filepath})"
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > 5000:
            content = content[:5000] + "\n\n... (文件过长，已截断)"
        return content
    except Exception as e:
        return f"读取失败: {e}"


@tool
def web_search(query: str) -> str:
    """搜索网络实时信息，仅当 search_city_info 等本地工具查不到数据时才使用！
    本地已收录以下 23 个城市的完整信息：北京、上海、成都、西安、杭州、昆明、三亚、重庆、
    大理、广州、厦门、南京、武汉、长沙、青岛、桂林、丽江、哈尔滨、苏州、洛阳、贵阳、张家界、拉萨。
    请先确认用户问的城市不在上述列表中，否则用 search_city_info 而不是此工具。

    :param query: 搜索关键词，尽量具体，如'潍坊到昆明火车票价 硬卧'
    """
    result = _search_ddg_lite(query)
    if result:
        return result
    return "未找到相关结果"


def _search_ddg_lite(query: str, max_results: int = 5) -> str | None:
    """通过 DuckDuckGo Lite 搜索（纯 HTML，轻量快速，国内可用）"""
    try:
        resp = _http.post(
            "https://lite.duckduckgo.com/lite/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10,
            verify=False,  # 绕过 SSL 证书校验（兼容国内网络环境）
        )
        if resp.status_code != 200:
            return None

        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, re.DOTALL)
        items = []
        for i, row in enumerate(rows):
            if len(items) >= max_results:
                break

            # 找包含 rel="nofollow" 链接的行（标题行）
            title_m = re.search(r'<a[^>]*rel="nofollow"[^>]*>(.*?)</a>', row, re.DOTALL)
            link_m = re.search(r'href="(https?://[^"]+)"', row)
            if not title_m or not link_m:
                continue

            title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()
            url = link_m.group(1)

            # 下一行是摘要（class="result-snippet"）
            snippet = ""
            if i + 1 < len(rows):
                snippet = re.sub(r"<[^>]+>", "", rows[i + 1]).strip()
                snippet = re.sub(r"\s+", " ", snippet)[:200]
                snippet = snippet.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()

            items.append(f"{len(items)+1}. {title}\n   {snippet}\n   {url}")

        return "\n\n".join(items) if items else None
    except Exception:
        return None


@tool
def get_weather(city: str = "北京") -> str:
    """查询指定城市当前的天气（温度、湿度、风速），用于出行前准备

    :param city: 城市名称，如北京、成都、大理
    """
    try:
        resp = _http.get(
            f"https://wttr.in/{city}?format=%C+%t+%h+%w",
            timeout=10
        )
        if resp.status_code == 200:
            return f"{city} 天气：{resp.text.strip()}"
        return f"查询失败 (HTTP {resp.status_code})"
    except Exception as e:
        return f"天气查询失败: {e}"


# ----- 待办事项 -----


@tool(name="add_todo")
def add_todo_func(task: str) -> str:
    """添加一条待办事项

    :param task: 待办内容
    """
    todos = _load_todos()
    todos.append({"id": len(todos) + 1, "task": task, "done": False, "created": str(datetime.date.today())})
    _save_todos(todos)
    return f"✅ 已添加待办: {task}"


@tool(name="list_todos")
def list_todos_func() -> str:
    """列出所有待办事项"""
    todos = _load_todos()
    if not todos:
        return "📭 没有待办事项"
    lines = ["📋 待办列表："]
    for t in todos:
        status = "✅" if t["done"] else "⬜"
        lines.append(f"  {status} [{t['id']}] {t['task']} ({t['created']})")
    return "\n".join(lines)


@tool
def done_todo(todo_id: int) -> str:
    """标记某条待办为已完成

    :param todo_id: 待办 ID
    """
    todos = _load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            _save_todos(todos)
            return f"✅ 已完成: {t['task']}"
    return f"❌ 未找到 ID {todo_id}"


# ----- 长期记忆 -----

_ltm = LongTermMemory()


@tool
def remember_info(key: str, value: str) -> str:
    """记住一条关于用户的信息到长期记忆，比如名字、年龄、偏好等

    :param key: 信息关键词，如 '名字'、'年龄'
    :param value: 信息内容
    """
    _ltm.remember(key, value)
    return f"已记住: {key} = {value}"


@tool(name="get_remembered_info")
def get_remembered_info_func(key: str = "") -> str:
    """从长期记忆中回忆信息，不传 key 则返回全部

    :param key: 要回忆的关键词，不传则返回全部
    """
    if key:
        val = _ltm.recall(key)
        return f"{key}: {val}" if val else f"未找到关于 '{key}' 的记忆"
    return _ltm.get_all()


# ----- 旅行规划工具 -----


@tool
def search_city_info(city: str) -> str:
    """查询某城市的完整旅行信息：景点列表、当地美食、最佳旅游季节、日均花费、实用提示
    已收录城市：北京、上海、成都、西安、杭州、昆明、三亚、重庆、大理
    未收录的城市会提示，请改用 web_search

    :param city: 目的地城市名称，如 '北京'、'成都'、'大理'
    """
    info = get_city(city)
    if not info:
        return f"暂未收录 {city} 的信息"
    lines = [
        f"📍 {city}（{info['name_en']}）— {info['region']}",
        f"📅 最佳季节：{info['best_season']}",
        f"💰 日均花费：经济{info['avg_cost_per_day']['经济']}元 / 舒适{info['avg_cost_per_day']['舒适']}元 / 豪华{info['avg_cost_per_day']['豪华']}元",
        f"🏷️ 特色：{'、'.join(info['features'])}",
        f"🍜 美食：{'、'.join(info['local_food'])}",
        f"💡 提示：{info['tips']}",
        f"\n🏛️ 景点推荐（{len(info['attractions'])}个）：",
    ]
    for a in info["attractions"]:
        ticket_str = f"¥{a['ticket']}" if a["ticket"] > 0 else "免费"
        lines.append(f"  · {a['name']}（{a['time']}，{ticket_str}）")
    return "\n".join(lines)


@tool
def plan_trip_budget(
    city: str,
    days: int = 3,
    travelers: int = 1,
    style: Literal["经济", "舒适", "豪华"] = "舒适",
) -> str:
    """估算一次旅行的总预算（住宿+餐饮+门票+市内交通）

    :param city: 目的地城市，如北京、成都、大理
    :param days: 旅行天数（建议 1-7 天）
    :param travelers: 出行人数
    :param style: 消费档次，经济=省钱，舒适=适中，豪华=高品质
    """
    if not city or not city.strip():
        return "❌ 请输入目的地城市"
    if days < 1:
        return "❌ 旅行天数不能少于 1 天"
    if days > 30:
        return "❌ 旅行天数建议不超过 30 天"
    if travelers < 1:
        return "❌ 出行人数不能少于 1 人"
    if travelers > 100:
        return "❌ 出行人数建议不超过 100 人"

    daily = estimate_daily_cost(city, style)
    total_per_person = daily * days
    total = total_per_person * travelers

    lines = [
        f"📊 {city} {days}天旅行预算估算（{style}型）",
        f"━━━━━━━━━━━━━━━━━━",
        f"👤 人数：{travelers}人",
        f"📅 天数：{days}天",
        f"💰 日均花费：¥{daily}/人",
        f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄",
        f"人均总计：¥{total_per_person}",
        f"🏷️ 合计：¥{total}",
        f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄",
        f"📝 费用包含：住宿 + 餐饮 + 门票 + 市内交通",
        f"⚠️ 不包含：往返大交通、购物",
    ]
    return "\n".join(lines)


@tool
def get_city_attractions(city: str, max_count: int = 10) -> str:
    """获取某城市推荐景点列表（含门票价格、建议游玩时长、景点类型）
    数据来源为本地数据库，景点有限。如需更多推荐请用 web_search

    :param city: 城市名称，如北京、成都
    :param max_count: 最多返回的景点数量，默认 10
    """
    attractions = get_attractions(city)
    if not attractions:
        return f"暂未收录 {city} 的景点信息"
    lines = [f"🏛️ {city} 推荐景点（共{len(attractions)}个）："]
    for a in attractions[:max_count]:
        ticket_str = f"¥{a['ticket']}" if a["ticket"] > 0 else "免费"
        lines.append(f"  · {a['name']} | {a['type']} | 建议{a['time']} | {ticket_str}")
    return "\n".join(lines)


@tool
def currency_converter(amount: float, from_currency: str = "CNY", to_currency: str = "USD") -> str:
    """货币换算，支持常见币种互转
    支持：CNY(人民币) USD(美元) EUR(欧元) JPY(日元) GBP(英镑)
          KRW(韩元) THB(泰铢) HKD(港元) AUD(澳元) TWD(台币)

    :param amount: 金额
    :param from_currency: 源币种代码，如 CNY、USD、EUR、JPY
    :param to_currency: 目标币种代码，如 USD、CNY、EUR
    """
    if from_currency not in CURRENCY_RATES or to_currency not in CURRENCY_RATES:
        return f"不支持的币种。支持: {', '.join(CURRENCY_RATES.keys())}"
    cny_amount = amount * CURRENCY_RATES[from_currency]
    result = cny_amount / CURRENCY_RATES[to_currency]
    symbols = {
        "CNY": "¥", "USD": "$", "EUR": "€", "JPY": "¥", "GBP": "£",
        "KRW": "₩", "THB": "฿", "HKD": "HK$", "AUD": "A$",
    }
    src_sym = symbols.get(from_currency, "")
    dst_sym = symbols.get(to_currency, "")
    return f"{src_sym}{amount:,.2f} {from_currency} = {dst_sym}{result:,.2f} {to_currency}（参考汇率）"


@tool
def suggest_trip(interests: str = "", budget: int = 0, days: int = 3) -> str:
    """根据兴趣关键词和预算推荐合适的旅行目的地城市
    支持的兴趣：历史、美食、自然、海滩、古镇、购物、城市、文艺
    预算设为 0 表示不限制预算

    :param interests: 兴趣关键词，多个用空格分隔，如 '历史 美食'
    :param budget: 总预算上限（元），0 表示不限制
    :param days: 旅行天数
    """
    interest_map = {
        "历史": ["北京", "西安", "洛阳"],
        "美食": ["成都", "重庆", "广州", "西安"],
        "自然": ["昆明", "大理", "桂林", "张家界"],
        "海滩": ["三亚", "厦门", "青岛"],
        "古镇": ["大理", "丽江", "苏州"],
        "购物": ["上海", "香港", "深圳"],
        "城市": ["上海", "北京", "深圳", "广州"],
        "文艺": ["大理", "杭州", "厦门"],
    }

    # 根据兴趣筛选
    candidates = set()
    if interests:
        for keyword in interests.replace("、", " ").replace(",", " ").split():
            if keyword in interest_map:
                candidates.update(interest_map[keyword])

    if not candidates:
        candidates = set(get_all_cities())

    # 根据预算过滤
    max_daily = (budget / days) if budget > 0 and days > 0 else 9999
    results = []
    for city in candidates:
        daily = estimate_daily_cost(city, "舒适")
        if daily <= max_daily or budget == 0:
            info = get_city(city) or {}
            total = daily * days
            results.append((city, daily, total, "、".join(info.get("features", [])[:3])))

    results.sort(key=lambda x: x[2])  # 按总价排序

    if not results:
        return f"在预算 ¥{budget} 内未找到合适的 {days} 天行程目的地，试试提高预算或减少天数？"

    lines = [f"🎯 推荐目的地（{interests or '不限兴趣'} | {days}天 | 预算¥{budget if budget else '不限'}）："]
    for city, daily, total, features in results[:5]:
        lines.append(f"  · {city} — 日均¥{daily}，{days}天约¥{total} | {features}")
    lines.append("\n💡 用 search_city_info 查看详情，用 plan_trip_budget 算具体预算")
    return "\n".join(lines)


# ======================================================================
# 行程导出工具
# ======================================================================

from trip_export import save_trip as _save_trip, list_trips as _list_trips, get_trip_summary as _trip_summary


@tool
def save_trip(destination: str, days: int = 3, style: str = "舒适",
              budget: float = 0, itinerary: str = "", notes: str = "") -> str:
    """保存当前规划的行程到本地，便于后续导出为 PDF 或分享链接
    当你为用户规划好完整的行程后，主动调用此工具将行程保存下来。
    包括目的地、天数、预算、详细的每日安排等。

    :param destination: 目的地城市名称
    :param days: 旅行天数
    :param style: 消费档次，可选：经济/舒适/豪华
    :param budget: 总预算（元），0 表示未设定
    :param itinerary: 详细的行程安排，包含每日计划，建议用 Day1/Day2 分天描述
    :param notes: 备注信息，如最佳季节、必吃美食、重要提示等
    """
    tid = _save_trip(destination=destination, days=days, style=style,
                     budget=budget, itinerary=itinerary, notes=notes)
    trip = get_trip_from_export(tid)
    summary = _trip_summary(trip) if trip else ""
    return f"✅ 行程已保存！\n{summary}\n\n可在「📤 行程导出」中查看、导出 PDF 或生成分享链接。"


def get_trip_from_export(trip_id: str):
    """从 trip_export 模块获取行程（辅助函数）"""
    from trip_export import get_trip
    return get_trip(trip_id)


@tool(name="list_my_trips")
def list_my_trips_func() -> str:
    """列出所有已保存的行程，方便回顾之前规划过的旅行计划"""
    trips = _list_trips()
    if not trips:
        return "📭 暂无已保存的行程。在规划完行程后可以用 save_trip 保存，或者去「📤 行程导出」手动添加。"

    lines = ["📋 已保存的行程："]
    for t in trips:
        summary = _trip_summary(t)
        tid = t.get("id", "")[:16]
        lines.append(f"  · [{tid}] {summary}")
    lines.append("\n💡 使用 export_trip 查看详情，或到「📤 行程导出」导出 PDF / 分享链接")
    return "\n".join(lines)


@tool
def export_trip(trip_id: str = "", format: str = "html") -> str:
    """将已保存的行程导出为 HTML 分享页或 PDF 文件
    需要先通过 save_trip 保存行程，或用 list_my_trips 查看已保存的行程 ID

    :param trip_id: 行程 ID（部分匹配也可），为空则导出最近一条
    :param format: 导出格式，html（分享页）或 pdf
    """
    from trip_export import get_trip, list_trips, export_to_html, export_to_pdf

    trips = list_trips()
    if not trips:
        return "❌ 没有已保存的行程，请先规划行程并用 save_trip 保存"

    target = None
    if trip_id:
        # 尝试精确匹配或前缀匹配
        for t in trips:
            tid = t.get("id", "")
            if tid == trip_id or tid.startswith(trip_id):
                target = t
                break
        if not target:
            return f"❌ 未找到 ID 以 '{trip_id}' 开头的行程，用 list_my_trips 查看所有行程"
    else:
        target = trips[0]

    tid = target["id"]
    if format == "pdf":
        path = export_to_pdf(tid)
    else:
        path = export_to_html(tid)

    if path:
        return f"✅ 已导出：{path}\n💡 可在浏览器中打开查看或分享"
    return "❌ 导出失败"


# ======================================================================
# 工具查找
# ======================================================================


def get_tool_definitions() -> list[dict]:
    """获取 OpenAI 格式的 tool definitions（从 TOOL_REGISTRY 动态生成）"""
    return [t["parameters"] for t in TOOL_REGISTRY]


def execute_tool(name: str, arguments: dict) -> str:
    """根据名称执行工具，返回结果字符串"""
    for tool_item in TOOL_REGISTRY:
        if tool_item["name"] == name:
            try:
                result = tool_item["func"](**arguments)
                return str(result) if result is not None else "执行完成"
            except Exception as e:
                return f"工具执行错误 ({name}): {e}"
    return f"错误：未知工具 '{name}'"
