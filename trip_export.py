"""
行程导出模块 —— 行程存储、HTML 分享页、PDF 导出
支持保存/读取行程数据，生成精美的分享页面和 PDF 文件
"""

import json
import datetime
import uuid
from pathlib import Path
from typing import Optional

TRIP_DIR = Path(__file__).parent / "saved_trips"
EXPORT_DIR = Path(__file__).parent / "exports"


def _ensure_dirs():
    TRIP_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)


def _trip_path(trip_id: str) -> Path:
    return TRIP_DIR / f"{trip_id}.json"


# ======================================================================
# 行程数据管理
# ======================================================================

def save_trip(destination: str, days: int = 3, style: str = "舒适",
              budget: float = 0, itinerary: str = "", notes: str = "",
              trip_id: str = None) -> str:
    """保存一条行程记录到本地

    :param destination: 目的地城市
    :param days: 旅行天数
    :param style: 消费档次（经济/舒适/豪华）
    :param budget: 总预算（元），0 表示未设定
    :param itinerary: 行程详情（纯文本，可包含换行）
    :param notes: 备注
    :param trip_id: 指定 ID（编辑时用），None 则自动生成
    :returns: trip_id
    """
    _ensure_dirs()
    if not trip_id:
        trip_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]

    # 如果是编辑已有行程，保留创建时间
    created_at = datetime.datetime.now().isoformat()
    if trip_id:
        existing = get_trip(trip_id)
        if existing:
            created_at = existing.get("created_at", created_at)

    trip = {
        "id": trip_id,
        "destination": destination,
        "days": days,
        "style": style,
        "budget": budget,
        "itinerary": itinerary,
        "notes": notes,
        "created_at": created_at,
        "updated_at": datetime.datetime.now().isoformat(),
    }
    _trip_path(trip_id).write_text(
        json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return trip_id


def get_trip(trip_id: str) -> Optional[dict]:
    """根据 ID 获取行程"""
    path = _trip_path(trip_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_trips() -> list[dict]:
    """列出所有已保存的行程（按更新时间倒序）"""
    _ensure_dirs()
    trips = []
    for f in sorted(TRIP_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            trips.append(data)
        except Exception:
            continue
    return trips


def delete_trip(trip_id: str) -> bool:
    """删除一条行程"""
    path = _trip_path(trip_id)
    if path.exists():
        path.unlink()
        return True
    return False


# ======================================================================
# 分享页面 HTML 生成
# ======================================================================

def _generate_trip_html(trip: dict) -> str:
    """生成美观的行程分享 HTML 页面（单文件，无外部依赖）"""
    destination = trip.get("destination", "未知目的地")
    days = trip.get("days", 1)
    style = trip.get("style", "舒适")
    budget = trip.get("budget", 0)
    itinerary = trip.get("itinerary", "")
    notes = trip.get("notes", "")
    created = trip.get("created_at", "")[:10]

    budget_str = f"¥{budget:,.0f}" if budget else "未设定"

    # 行程文本 -> HTML（保留换行和简单格式）
    itinerary_html = ""
    if itinerary:
        # 支持 Markdown 风格的标题行：Day 1: xxx / **Day 2** 等
        for line in itinerary.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                itinerary_html += "<br>"
            elif line_stripped.startswith("Day ") or line_stripped.startswith("第"):
                itinerary_html += f"<h3 style='color:#667eea;margin:16px 0 8px;font-size:16px;'>📍 {line_stripped}</h3>"
            elif line_stripped.startswith("- ") or line_stripped.startswith("·"):
                itinerary_html += f"<li style='margin:4px 0 4px 20px;'>{line_stripped[2:]}</li>"
            else:
                itinerary_html += f"<p style='margin:4px 0;'>{line_stripped}</p>"
    else:
        itinerary_html = "<p style='color:#999;'>暂无详细行程</p>"

    notes_html = ""
    if notes:
        for line in notes.split("\n"):
            line = line.strip()
            if line:
                notes_html += f"<p style='margin:4px 0;'>{line}</p>"

    # 根据消费档次选颜色
    style_colors = {"经济": "#52c41a", "舒适": "#1890ff", "豪华": "#722ed1"}
    style_color = style_colors.get(style, "#1890ff")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🗺️ {destination} 行程单</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
    background: linear-gradient(135deg, #e8ecf1 0%, #d5dce6 100%);
    min-height: 100vh;
    padding: 24px;
    color: #2c3e50;
}}
.card {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.12);
    overflow: hidden;
}}
.header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 44px 40px 36px;
    text-align: center;
}}
.header h1 {{ font-size: 30px; margin-bottom: 6px; letter-spacing: 1px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.85; margin-top: 4px; }}
.header .meta-bar {{
    display: flex; justify-content: center; flex-wrap: wrap; gap: 8px 20px;
    margin-top: 18px;
}}
.header .meta-item {{
    background: rgba(255,255,255,0.18);
    backdrop-filter: blur(4px);
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 14px;
}}
.body-section {{
    padding: 32px 40px;
    border-bottom: 1px solid #f0f2f5;
}}
.body-section:last-child {{ border-bottom: none; }}
.section-title {{
    font-size: 17px;
    font-weight: 600;
    color: #667eea;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.day-block {{ margin-bottom: 4px; }}
ul.itinerary-list {{
    list-style: none;
    padding: 0;
}}
ul.itinerary-list li {{
    padding: 3px 0 3px 24px;
    position: relative;
    line-height: 1.7;
}}
ul.itinerary-list li::before {{
    content: "•";
    position: absolute;
    left: 8px;
    color: #667eea;
    font-weight: bold;
}}
.notes-box {{
    background: #f8f9ff;
    border-radius: 14px;
    padding: 20px 24px;
    color: #555;
    line-height: 1.7;
    font-size: 14px;
}}
.footer {{
    text-align: center;
    padding: 20px;
    color: #aaa;
    font-size: 12px;
    background: #fafafa;
}}
@media print {{
    body {{ background: white; padding: 0; }}
    .card {{ box-shadow: none; border-radius: 0; }}
    .header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
}}
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <h1>🗺️ {destination}</h1>
        <div class="subtitle">来自 旅行规划 Agent 的行程推荐</div>
        <div class="meta-bar">
            <span class="meta-item">📅 {days} 天</span>
            <span class="meta-item" style="border: 1px solid {style_color}; background: rgba(255,255,255,0.10);">🏷️ {style} 型</span>
            <span class="meta-item">💰 {budget_str}</span>
        </div>
    </div>

    <div class="body-section">
        <div class="section-title">📋 行程安排</div>
        <div>{itinerary_html}</div>
    </div>

    {f'''<div class="body-section">
        <div class="section-title">📝 备注 & 贴士</div>
        <div class="notes-box">{notes_html}</div>
    </div>''' if notes else ""}

    <div class="footer">
        生成于 {created} · 由旅行规划 Agent 制作 · 可在浏览器中打印为 PDF
    </div>
</div>
</body>
</html>"""
    return html


# ======================================================================
# 导出函数
# ======================================================================

def export_to_html(trip_id: str) -> Optional[str]:
    """生成分享用的 HTML 页面，返回文件路径"""
    trip = get_trip(trip_id)
    if not trip:
        return None
    _ensure_dirs()
    html = _generate_trip_html(trip)
    html_path = EXPORT_DIR / f"trip_{trip_id}.html"
    html_path.write_text(html, encoding="utf-8")
    return str(html_path)


def _find_chinese_font() -> Optional[dict]:
    """在系统中查找可用中文字体，返回 {'file': str, 'family': str, 'index': int}"""
    # 优先 TTF（简单），其次 TTC（需 collection_font_number）
    candidates = [
        ("C:/Windows/Fonts/simhei.ttf", "SimHei", 0),
        ("C:/Windows/Fonts/simsun.ttc", "SimSun", 0),
        ("C:/Windows/Fonts/msyh.ttc", "Microsoft YaHei", 0),
        ("C:/Windows/Fonts/yahei.ttf", "Microsoft YaHei", 0),
        ("C:/Windows/Fonts/msyhbd.ttc", "Microsoft YaHei Bold", 0),
    ]

    # Linux / macOS
    unix_candidates = [
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "NotoSansCJK", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "NotoSansCJK", 0),
        ("/System/Library/Fonts/PingFang.ttc", "PingFang", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti", 0),
        ("/Library/Fonts/Arial Unicode.ttf", "Arial Unicode", 0),
    ]

    for filepath, family, idx in candidates + unix_candidates:
        p = Path(filepath)
        if p.exists():
            return {"file": str(p), "family": family, "index": idx}
    return None


def export_to_pdf(trip_id: str) -> Optional[str]:
    """导出行程为 PDF 文件

    优先使用 fpdf2 生成（需要中文字体），
    若 fpdf2 不可用则降级为 HTML 文件。
    返回文件路径。
    """
    trip = get_trip(trip_id)
    if not trip:
        return None
    _ensure_dirs()

    # ---- 尝试 fpdf2 ----
    try:
        from fpdf import FPDF
        font_info = _find_chinese_font()

        if not font_info:
            # 无中文字体，降级为 HTML
            return export_to_html(trip_id)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # 注册并使用中文字体
        # fpdf2 v2.5.1+ 不再需要 uni=True；TTC 需 collection_font_number
        add_font_kw = {"fname": font_info["file"]}
        if font_info["file"].endswith(".ttc"):
            add_font_kw["collection_font_number"] = font_info["index"]
        pdf.add_font("CN", **add_font_kw)
        pdf.set_font("CN", "", 24)
        pdf.set_text_color(102, 126, 234)

        # 标题
        pdf.cell(0, 18, f"  {trip['destination']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(102, 126, 234)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # 元信息
        pdf.set_font("CN", "", 11)
        pdf.set_text_color(100, 100, 100)
        days = trip.get("days", 1)
        style = trip.get("style", "舒适")
        budget = trip.get("budget", 0)
        budget_str = f"  {budget:,.0f}" if budget else "未设定"
        created = trip.get("created_at", "")[:10]

        pdf.cell(0, 7, f"  天数: {days} 天  |  档次: {style}  |  预算: {budget_str}  |  创建: {created}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # 行程内容
        pdf.set_text_color(44, 62, 80)
        itinerary = trip.get("itinerary", "")
        if itinerary:
            pdf.set_font("CN", "", 16)
            pdf.set_text_color(102, 126, 234)
            pdf.cell(0, 10, "  行程安排", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(44, 62, 80)
            pdf.set_font("CN", "", 11)

            for line in itinerary.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("Day ") or line.startswith("第"):
                    # 日期标题，用稍大字号
                    pdf.set_font("CN", "", 13)
                    pdf.set_text_color(102, 126, 234)
                    pdf.cell(0, 8, f"  {line}", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("CN", "", 11)
                    pdf.set_text_color(44, 62, 80)
                else:
                    # 普通内容
                    display = line[2:] if line.startswith("- ") or line.startswith("·") else line
                    pdf.multi_cell(0, 6, f"  {display}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        # 备注
        notes = trip.get("notes", "")
        if notes:
            pdf.set_font("CN", "", 16)
            pdf.set_text_color(102, 126, 234)
            pdf.cell(0, 10, "  备注 & 贴士", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(100, 100, 100)
            pdf.set_font("CN", "", 11)
            for line in notes.split("\n"):
                line = line.strip()
                if line:
                    pdf.multi_cell(0, 6, f"  {line}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        # 页脚
        pdf.set_text_color(180, 180, 180)
        pdf.set_font("CN", "", 8)
        pdf.cell(0, 10, f"  由 旅行规划 Agent 生成  {created}", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf_path = EXPORT_DIR / f"trip_{trip_id}.pdf"
        pdf.output(str(pdf_path))
        return str(pdf_path)

    except ImportError:
        pass
    except Exception as e:
        print(f"  PDF 生成失败 ({e})，降级为 HTML")

    # ---- 降级：生成 HTML ----
    return export_to_html(trip_id)


def get_trip_summary(trip: dict) -> str:
    """行程的简短摘要（用于列表展示）"""
    dest = trip.get("destination", "?")
    days = trip.get("days", "?")
    style = trip.get("style", "?")
    created = trip.get("created_at", "")[5:16] if trip.get("created_at") else "?"
    return f"  {dest}  |  {days}天 {style}型  |  {created}"


# ======================================================================
# 快速测试
# ======================================================================
if __name__ == "__main__":
    # 测试保存行程
    tid = save_trip(
        destination="成都",
        days=3,
        style="舒适",
        budget=1500,
        itinerary="""Day 1: 抵达成都
- 上午抵达，入住春熙路附近酒店
- 中午吃顿火锅
- 下午逛宽窄巷子、锦里
- 晚上看川剧变脸

Day 2: 大熊猫之旅
- 上午去大熊猫繁育基地（早点去，熊猫最活跃）
- 中午在基地附近就餐
- 下午去武侯祠、锦里
- 晚上吃串串香

Day 3: 文化体验
- 上午去都江堰（半天游）
- 下午回市区逛人民公园
- 傍晚返程""",
        notes="最佳季节：3-6月、9-11月\n必吃：火锅、串串香、担担面\n熊猫基地建议早上8点前到",
    )
    print(f"  保存成功: {tid}")
    print(get_trip_summary(get_trip(tid)))

    html_path = export_to_html(tid)
    print(f"  HTML: {html_path}")

    pdf_path = export_to_pdf(tid)
    print(f"  PDF: {pdf_path}")
