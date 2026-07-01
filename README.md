# 🗺️ 旅行规划 Agent — 小林

> **小林**，23 岁，你的活泼旅行规划助手 🌸

从零构建的个人 AI 助手 —— 基于 ReAct 循环 + Function Calling，支持智能对话、工具调用、RAG 知识库、长期记忆。

**约 2100 行 Python 代码**，无复杂框架依赖，核心逻辑清晰。

---

## ✨ 功能

- 💬 **智能对话** — 基于 LLM 的流式对话（DeepSeek / 通义千问 / GLM / OpenAI）
- 🛠️ **工具调用** — 自动注册机制，15+ 个内置工具
- 🧠 **长期记忆** — 跨会话持久化用户信息
- 📚 **RAG 知识库** — ChromaDB + BGE Embedding 语义检索
- 🌐 **Web 界面** — Gradio 聊天 UI，支持流式输出
- 🔄 **对话压缩** — 长对话自动摘要，保留最近 20 条
- 🗂️ **历史会话** — 查看/继续历史对话，最多保留 20 条
- ⚙️ **在线配置** — Web 界面切换模型、API Key、系统提示词
- 📤 **行程导出** — 保存行程、生成 HTML 分享页或 PDF 文件

### 旅行工具（8 个内置）

| 工具 | 说明 |
|------|------|
| `search_city_info` | 23 个城市的完整旅行信息 |
| `plan_trip_budget` | 预算估算（经济/舒适/豪华三档） |
| `get_city_attractions` | 景点列表及门票价格 |
| `currency_converter` | 10 种货币互换算 |
| `suggest_trip` | 按兴趣+预算推荐目的地 |
| `save_trip` | 保存行程规划到本地 |
| `list_my_trips` | 查看所有已保存的行程 |
| `export_trip` | 导出为 HTML 分享页或 PDF |

### 通用工具（10+ 个）

计算、天气、网页搜索、待办管理、文件读取、长期记忆读写……

---

## 🚀 快速开始

```bash
cd travel_agent
pip install -r requirements.txt
python app.py
```

浏览器自动打开 **http://127.0.0.1:7860**

### 配置 API Key

编辑 `config.json`:
```json
{ "llm": { "api_key": "sk-你的Key" } }
```

推荐使用 [DeepSeek](https://platform.deepseek.com/)（便宜、中文强），
也支持任何 OpenAI 兼容 API。

---

## 📁 项目结构

```
agent.py          # 核心引擎（ReAct 循环 + Function Calling）
tools.py          # 15+ 个工具（@tool 装饰器自动注册）
travel_data.py    # 23 个城市的旅行数据库
trip_export.py    # 行程存储 + HTML/PDF 导出
memory.py         # 短期/长期记忆 + 会话管理
knowledge.py      # RAG 知识库（ChromaDB + BGE）
app.py            # Gradio Web 界面
config.py         # 配置管理（支持 5 个 Provider）
config.json       # 用户配置（已 gitignore）
knowledge/        # 知识库文档（.md / .txt）
memory_logs/      # 对话历史存储（已 gitignore）
chroma_db/        # 向量数据库（已 gitignore）
saved_trips/      # 已保存的行程（已 gitignore）
exports/          # 导出文件（已 gitignore）
todos.json        # 待办事项
```

---

## 💡 示例对话

```
你: 帮我规划三天成都游，预算 2000
小林: 好嘞！帮你算算成都三天舒适游～

📊 成都 3天旅行预算估算（舒适型）
━━━━━━━━━━━━━━━━━━
👤 人数：1人
📅 天数：3天
💰 日均花费：¥500/人
人均总计：¥1,500

Day1: 大熊猫繁育基地(半天) → 宽窄巷子 → 锦里
Day2: 武侯祠 → 杜甫草堂 → 春熙路
Day3: 都江堰/青城山一日游

💡 预算内还有 ¥500 余额，可以吃顿火锅哦！
```

---

## 🔧 配置

支持 5 个模型提供商，可在 Web 界面切换：

| 提供商 | 默认模型 |
|--------|----------|
| DeepSeek | deepseek-chat |
| 通义千问 | qwen-plus |
| GLM | glm-4-flash |
| OpenAI | gpt-4o-mini |
| SiliconFlow | DeepSeek-V3 |

环境变量覆盖（优先级最高）：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_PROVIDER`

---

## 🧰 扩展

在 `tools.py` 中用 `@tool` 装饰器添加函数即可增加新工具：

```python
@tool
def my_tool(param1: str, param2: int = 0) -> str:
    """工具描述
    
    :param param1: 参数1说明
    :param param2: 参数2说明
    """
    return f"结果: {param1}, {param2}"
```

装饰器自动从类型注解 + docstring 生成 Function Calling Schema。

---

## 📊 数据

- **23 个城市**的旅行数据（北京/上海/成都/西安/杭州/昆明/三亚/重庆/大理/广州/厦门/南京/武汉/长沙/青岛/桂林/丽江/哈尔滨/苏州/洛阳/贵阳/张家界/拉萨）
- 每个城市包含：景点、美食、最佳季节、日均花费、实用提示
- 城市数据位于 `travel_data.py`，可直接编辑扩展
- 已规划的行程可保存为本地 JSON，并导出为 HTML 分享页或 PDF

---

## 技术栈

- **LLM**: DeepSeek API（默认）/ 通义千问 / GLM / OpenAI / SiliconFlow
- **工具调用**: OpenAI Function Calling
- **向量库**: ChromaDB + BAAI/bge-small-zh-v1.5
- **界面**: Gradio
- **搜索**: DuckDuckGo Lite（国内可用）
- **PDF 导出**: fpdf2 + 本地中文字体
- **Python**: 3.10+

---

> 写于 2026 年 7 月 | Python 3.10+
