"""
Web 界面 —— 基于 Gradio 的聊天应用
"""

import gradio as gr
from agent import PersonalAgent
from config import CONFIG, save_config
from memory import list_all_sessions, load_session_messages

agent = PersonalAgent()


def reset_chat():
    agent.reset()
    return [], ""


def save_config_handler(provider_label, api_key, model, prompt):
    from config import LABEL_TO_KEY, PROVIDER_CONFIG
    provider_key = LABEL_TO_KEY.get(provider_label, "deepseek")
    CONFIG["llm"]["provider"] = provider_key
    CONFIG["llm"]["api_key"] = api_key
    CONFIG["llm"]["model"] = model
    # 选择 provider 时自动填充 base_url
    if provider_key in PROVIDER_CONFIG:
        CONFIG["llm"]["base_url"] = PROVIDER_CONFIG[provider_key]["base_url"]
    if prompt:
        CONFIG["agent"]["system_prompt"] = prompt
    save_config(CONFIG)
    global agent
    sid = agent.get_session_id()
    agent = PersonalAgent(session_id=sid)
    return "✅ 配置已保存！"


def index_kb():
    try:
        c = agent.index_knowledge()
        return f"✅ 索引完成！共索引 {c} 个文件"
    except Exception as e:
        return f"❌ 索引失败: {e}"


# ===== 历史对话 =====

def get_session_list():
    """获取会话列表，供下拉框使用"""
    sessions = list_all_sessions()
    if not sessions:
        return ["(暂无历史会话)"]
    return [f"{s['id']} — {s['count']}条消息 ({s['updated'][:16]})" for s in sessions]


def _msgs_to_gradio(msgs: list[dict]) -> list[dict]:
    """将消息列表转成 Gradio chatbot 格式"""
    history = []
    for m in msgs:
        role = m.get("role", "")
        content = m.get("content", "")
        if role in ("user", "assistant"):
            history.append({"role": role, "content": content})
    return history


def load_history_session(choice: str):
    """加载选中的历史会话（仅查看）"""
    if not choice or "(暂无" in choice:
        return [], "(无)"
    session_id = choice.split(" — ")[0]
    msgs = load_session_messages(session_id)
    if not msgs:
        return [], "(空)"
    return _msgs_to_gradio(msgs), session_id


def continue_session(choice: str):
    """将选中的历史会话设为当前会话，继续聊天"""
    if not choice or "(暂无" in choice:
        return [], "(无)", "(无)", []
    session_id = choice.split(" — ")[0]
    msgs = load_session_messages(session_id)
    if not msgs:
        return [], "(空)", "(空)", []

    # 重新初始化 agent 以加载该会话
    global agent
    agent = PersonalAgent(session_id=session_id)
    # agent 初始化时已通过 ConversationMemory._load() 加载了全部消息

    history = _msgs_to_gradio(msgs)
    return history, session_id, agent.get_long_memory(), history


css = """
.container { max-width: 900px; margin: auto; }
"""

with gr.Blocks(title="个人 AI Agent") as demo:
    gr.Markdown("# 🗺️ 旅行规划 Agent\n你的智能旅行规划助手 —— 查景点、算预算、推荐目的地、安排行程")

    with gr.Tab("💬 对话"):
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(height=450)
                msg = gr.Textbox(label="输入消息", placeholder="输入问题，按 Enter 发送...", lines=2)
                with gr.Row():
                    send_btn = gr.Button("发送", variant="primary", scale=2)
                    reset_btn = gr.Button("重置对话", variant="secondary", scale=1)

            with gr.Column(scale=1):
                gr.Markdown("### 📊 状态")
                sid_box = gr.Textbox(label="会话 ID", value=agent.get_session_id(), interactive=False)
                status_box = gr.Textbox(label="⏱ 当前状态", value="就绪", interactive=False)
                usage_box = gr.Textbox(label="⚡ Token 用量", value=agent.get_usage_str(), interactive=False)
                trace_box = gr.Textbox(label="🧠 思维链", value="", lines=6, max_lines=10, interactive=False)
                mem_box = gr.Textbox(label="长期记忆", value=agent.get_long_memory(), lines=4, interactive=False)

        def chat_wrapper(msg, history):
            history = history or []
            history.append({"role": "user", "content": msg})
            yield history, "", agent.get_session_id(), "⏳ 思考中...", agent.get_usage_str(), "", agent.get_long_memory()

            trace_lines = []
            streaming_content = ""
            has_streamed = False

            for update in agent.chat_stream(msg):
                t = update["type"]
                el = update.get("elapsed", 0)

                # 始终保留已流式输出的内容，不被 thinking/tool 事件冲掉
                display = history + [{"role": "assistant", "content": streaming_content}] if streaming_content else history

                if t == "thinking":
                    status = f"🤔 第 {update['step']} 步思考中... ({el:.1f}s)"
                    yield display, "", agent.get_session_id(), status, agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()

                elif t == "tool":
                    name = update["name"]
                    args = update["args"]
                    args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                    trace_lines.append(f"🔧 [{el:.1f}s] 调用 {name}({args_str})")
                    status = f"🔧 正在使用工具: {name} ({el:.1f}s)"
                    yield display, "", agent.get_session_id(), status, agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()

                elif t == "tool_result":
                    name = update["name"]
                    result = update["result"]
                    trace_lines.append(f"📥 [{el:.1f}s] {name} 返回: {result}")
                    yield display, "", agent.get_session_id(), f"📥 获得 {name} 结果", agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()

                elif t == "token":
                    """逐字流式输出 —— 每生成一个 token 就更新一次聊天框"""
                    has_streamed = True
                    streaming_content += update["content"]
                    display_history = history + [{"role": "assistant", "content": streaming_content}]
                    status = f"✍️ 生成中... ({el:.1f}s)"
                    yield display_history, "", agent.get_session_id(), status, agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()

                elif t == "answer":
                    steps = update.get("steps", 0)
                    reply = update.get("content", "")

                    if has_streamed:
                        # 已经流式输出完了，最终确认状态
                        display_history = history + [{"role": "assistant", "content": streaming_content or reply}]
                        status = f"✅ 完成 ({steps} 步, {el:.1f}s)"
                        trace_lines.append(f"💡 [{el:.1f}s] 最终回答完成")
                        yield display_history, "", agent.get_session_id(), status, agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()
                    else:
                        # 非流式（错误信息等降级路径）
                        status = f"✅ 完成 ({steps} 步, {el:.1f}s)"
                        history.append({"role": "assistant", "content": reply})
                        trace_lines.append(f"💡 [{el:.1f}s] 最终回答完成")
                        yield history, "", agent.get_session_id(), status, agent.get_usage_str(), "\n".join(trace_lines), agent.get_long_memory()

        msg.submit(chat_wrapper, [msg, chatbot], [chatbot, msg, sid_box, status_box, usage_box, trace_box, mem_box])
        send_btn.click(chat_wrapper, [msg, chatbot], [chatbot, msg, sid_box, status_box, usage_box, trace_box, mem_box])
        reset_btn.click(reset_chat, outputs=[chatbot, msg]).then(
            lambda: (agent.get_session_id(), "就绪", agent.get_usage_str(), "", agent.get_long_memory()),
            outputs=[sid_box, status_box, usage_box, trace_box, mem_box]
        )

    with gr.Tab("⚙️ 配置"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### LLM 配置")

                from config import PROVIDER_CONFIG, KEY_TO_LABEL, PROVIDER_NAMES
                current_provider = CONFIG["llm"].get("provider", "deepseek")
                current_label = KEY_TO_LABEL.get(current_provider, "DeepSeek")
                provider_choices = [p["label"] for p in PROVIDER_CONFIG.values()]

                provider_dd = gr.Dropdown(
                    label="模型提供商",
                    choices=provider_choices,
                    value=current_label,
                    interactive=True,
                )
                api_key = gr.Textbox(
                    label="API Key",
                    placeholder="sk-...",
                    value=CONFIG["llm"]["api_key"],
                    type="password",
                )
                model_dd = gr.Dropdown(
                    label="模型",
                    choices=PROVIDER_CONFIG[current_provider]["models"],
                    value=CONFIG["llm"]["model"],
                    allow_custom_value=True,
                    interactive=True,
                )

                # provider 切换时更新模型建议列表
                def update_models(provider_label):
                    from config import LABEL_TO_KEY, PROVIDER_CONFIG
                    key = LABEL_TO_KEY.get(provider_label, "deepseek")
                    info = PROVIDER_CONFIG[key]
                    return gr.Dropdown(choices=info["models"], value=info["default_model"])

                provider_dd.change(update_models, inputs=[provider_dd], outputs=[model_dd])

                prompt = gr.Textbox(
                    label="系统提示词",
                    value=CONFIG["agent"]["system_prompt"],
                    lines=4,
                )
                save_btn = gr.Button("💾 保存配置", variant="primary")
                status = gr.Textbox(label="状态", interactive=False)
                save_btn.click(
                    save_config_handler,
                    [provider_dd, api_key, model_dd, prompt],
                    outputs=[status],
                )

            with gr.Column():
                gr.Markdown("### 📚 知识库")
                gr.Markdown("将文档放入 `knowledge/` 目录后点击下方按钮索引")
                idx_btn = gr.Button("🔄 索引知识库")
                idx_status = gr.Textbox(label="索引状态", interactive=False)
                idx_btn.click(index_kb, outputs=[idx_status])
                gr.Markdown("---\n### 💡 示例问题\n"
                    "- \"北京有什么好玩的？\"\n- \"帮我规划三天成都游，预算 2000\"\n"
                    "- \"推荐一个适合情侣去的海边城市\"\n- \"100美元是多少人民币？\"")

    with gr.Tab("📜 历史对话"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 选择会话")
                session_list = gr.Dropdown(
                    label="历史会话列表",
                    choices=get_session_list(),
                    value=None,
                    interactive=True,
                )
                refresh_list_btn = gr.Button("🔄 刷新列表", variant="secondary")
                load_btn = gr.Button("📂 加载查看", variant="secondary")
                continue_btn = gr.Button("💬 继续对话", variant="primary")
                loaded_id = gr.Textbox(label="当前查看的会话", value="(无)", interactive=False)

            with gr.Column(scale=3):
                history_chatbot = gr.Chatbot(height=500, label="历史对话内容")

        refresh_list_btn.click(
            lambda: gr.Dropdown(choices=get_session_list()),
            outputs=[session_list],
        )
        load_btn.click(
            load_history_session,
            inputs=[session_list],
            outputs=[history_chatbot, loaded_id],
        )
        continue_btn.click(
            continue_session,
            inputs=[session_list],
            outputs=[chatbot, sid_box, mem_box, history_chatbot],
        ).then(
            lambda: "✅ 已加载，切换到 💬 对话 继续聊天",
            outputs=[loaded_id],
        )

    with gr.Tab("📖 关于"):
        gr.Markdown(
            "## 🗺️ 旅行规划 Agent\n\n"
            "基于 ReAct 循环的智能旅行规划助手。\n\n"
            "### 项目结构\n"
            "```\n"
            "agent.py          # 核心引擎\n"
            "tools.py          # 工具（含15个工具）\n"
            "travel_data.py    # 城市数据库\n"
            "memory.py         # 记忆模块\n"
            "knowledge.py      # RAG 知识库\n"
            "app.py            # Web 界面\n"
            "config.py         # 配置管理\n"
            "config.json       # 用户配置\n"
            "knowledge/        # 知识库目录\n"
            "```\n\n"
            "### 旅行工具（5个）\n"
            "- `search_city_info` — 查询城市旅行信息\n"
            "- `plan_trip_budget` — 估算旅行预算\n"
            "- `get_city_attractions` — 获取景点列表\n"
            "- `currency_converter` — 货币换算\n"
            "- `suggest_trip` — 推荐旅行目的地\n\n"
            "### 技术栈\n"
            "- LLM: DeepSeek API\n"
            "- 工具调用: Function Calling\n"
            "- 知识库: ChromaDB + BGE Embedding\n"
            "- 界面: Gradio"
        )

if __name__ == "__main__":
    import webbrowser, threading
    url = "http://127.0.0.1:7860"
    threading.Timer(2, lambda: webbrowser.open(url)).start()
    print(f"==> 启动个人 AI Agent: {url}")
    import os
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name="127.0.0.1", server_port=port, share=False, show_error=True, css=css, theme=gr.themes.Soft())
