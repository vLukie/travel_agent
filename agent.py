"""
核心 Agent 引擎 —— ReAct 循环 + Function Calling + 记忆 + RAG
基于 OpenAI 兼容 API（DeepSeek / 通义千问 / GLM 等）
"""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import CONFIG
from tools import get_tool_definitions, execute_tool
from memory import ConversationMemory, LongTermMemory
from knowledge import KnowledgeBase


class PersonalAgent:
    """个人 AI Agent"""

    def __init__(self, session_id: str = None):
        self.config = CONFIG
        self.client = None
        self.memory = ConversationMemory(session_id)
        self.ltm = LongTermMemory()
        self.knowledge = KnowledgeBase()
        self.max_iter = self.config["agent"]["max_iterations"]
        self._kb_failed = False
        self._usage = {"prompt": 0, "completion": 0}  # token 用量追踪

        # 后台预热 embedding 模型（避免首次对话时卡 UI）
        threading.Thread(target=self._warm_kb, daemon=True).start()

    def _warm_kb(self):
        """后台预热知识库，不阻塞对话"""
        try:
            self.knowledge._init()
            self.knowledge._embed("预热")
        except Exception:
            pass

    def _init_client(self):
        if self.client is not None:
            return
        from openai import OpenAI
        cfg = self.config["llm"]
        self.client = OpenAI(
            api_key=cfg.get("api_key") or "sk-placeholder",
            base_url=cfg.get("base_url"),
        )

    def _build_system(self, user_input: str) -> str:
        """构建系统提示词：人格 + 长期记忆 + 知识库上下文（带超时保护）"""
        parts = [
            "[系统指令]",
            self.config["agent"]["system_prompt"],
        ]
        ltm = self.ltm.get_all()
        if "暂无" not in ltm:
            parts.append(ltm)

        # 知识库检索带超时保护（防止模型下载/网络问题卡死）
        ctx = self._safe_kb_query(user_input)
        if ctx:
            parts.append(ctx)

        return "\n".join(parts)

    def _safe_kb_query(self, query: str, timeout: float = 30.0) -> str:
        """带超时的知识库查询，超时或失败则跳过（不阻塞对话）"""
        if self._kb_failed:
            return ""  # 之前已经超时/失败过，不再重试

        result = [None]

        def _do():
            try:
                result[0] = self.knowledge.format_context(query)
            except Exception:
                result[0] = ""

        t = threading.Thread(target=_do, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive() or not result[0]:
            self._kb_failed = True  # 记住失败，不再重试
            return ""
        return result[0]

    def chat_stream(self, user_input: str):
        """
        流式 ReAct 循环 —— 逐步产出状态更新，最终产出回答
        yield 格式: {"type": "thinking"|"tool"|"tool_result"|"token"|"answer", ...}
        """
        self._init_client()
        if not self.client:
            yield {"type": "answer", "content": "错误：LLM 客户端未初始化，请检查 API 配置", "elapsed": 0, "steps": 0}
            return

        system = self._build_system(user_input)
        self.memory.add("user", user_input)
        messages = [{"role": "system", "content": system}] + self.memory.get_messages()
        tools = get_tool_definitions()
        start_time = time.time()

        for step in range(1, self.max_iter + 1):
            elapsed = time.time() - start_time
            yield {"type": "thinking", "step": step, "elapsed": elapsed}

            # === 流式调用 LLM ===
            stream = self.client.chat.completions.create(
                model=self.config["llm"]["model"],
                messages=messages,
                tools=tools or None,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
                stream=True,
                stream_options={"include_usage": True},
            )

            collected_content = ""
            collected_tc: dict[int, dict] = {}
            is_tool_response = False

            for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                # 收集 token 用量（仅最后 chunk 包含 usage）
                if finish_reason is not None and hasattr(chunk, "usage") and chunk.usage:
                    self._usage["prompt"] += chunk.usage.prompt_tokens or 0
                    self._usage["completion"] += chunk.usage.completion_tokens or 0

                # --- 累加 tool_calls 数据（流式 chunks 分片到达）---
                if delta.tool_calls:
                    is_tool_response = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in collected_tc:
                            collected_tc[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                        if tc.id:
                            collected_tc[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                collected_tc[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                collected_tc[idx]["function"]["arguments"] += tc.function.arguments

                # --- 流式输出文本 token（逐字推送到 UI）---
                if delta.content:
                    collected_content += delta.content
                    yield {
                        "type": "token",
                        "content": delta.content,
                        "full_content": collected_content,
                        "step": step,
                        "elapsed": time.time() - start_time,
                    }

                # --- 处理完成原因 ---
                if finish_reason == "tool_calls":
                    # 重建 assistant message
                    tool_calls_list = []
                    for idx in sorted(collected_tc.keys()):
                        tc = collected_tc[idx]
                        tool_calls_list.append({
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        })

                    messages.append({
                        "role": "assistant",
                        "content": collected_content or None,
                        "tool_calls": tool_calls_list,
                    })

                    # 并行执行工具（互不依赖的工具同时跑，大幅减少等待时间）

                    tool_infos = []
                    for tc_obj in tool_calls_list:
                        try:
                            args = json.loads(tc_obj["function"]["arguments"])
                        except json.JSONDecodeError:
                            args = {}
                        tool_name = tc_obj["function"]["name"]
                        tool_infos.append((tc_obj, tool_name, args))
                        yield {
                            "type": "tool",
                            "name": tool_name,
                            "args": args,
                            "step": step,
                            "elapsed": time.time() - start_time,
                        }

                    with ThreadPoolExecutor(max_workers=4) as pool:
                        future_to_info = {}
                        for tc_obj, tool_name, args in tool_infos:
                            future = pool.submit(execute_tool, tool_name, args)
                            future_to_info[future] = (tc_obj, tool_name, args)

                        for future in as_completed(future_to_info):
                            tc_obj, tool_name, args = future_to_info[future]
                            try:
                                result = future.result()
                            except Exception as e:
                                result = f"工具执行错误 ({tool_name}): {e}"
                            yield {
                                "type": "tool_result",
                                "name": tool_name,
                                "result": result[:200] if result else "",
                                "step": step,
                                "elapsed": time.time() - start_time,
                            }
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_obj["id"],
                                "content": result,
                            })
                    break  # 退出 for-chunk，继续外层的 for-step

                elif finish_reason == "stop":
                    reply = collected_content or ""
                    self.memory.add("assistant", reply)

                    # 长对话自动压缩
                    if self.memory.needs_summary():
                        try:
                            resp = self.client.chat.completions.create(
                                model=self.config["llm"]["model"],
                                messages=messages + [{"role": "user", "content": "请用 2-3 句话概括以上对话要点"}],
                                max_tokens=500,
                            )
                            summary = resp.choices[0].message.content or ""
                            self.memory.compress(summary)
                        except Exception:
                            pass

                    yield {
                        "type": "answer",
                        "content": reply,
                        "elapsed": time.time() - start_time,
                        "steps": step,
                    }
                    return

            if is_tool_response:
                continue  # 继续 ReAct 循环

        yield {"type": "answer", "content": "抱歉，思考步骤过多，请换个简化一点的方式提问。", "elapsed": time.time() - start_time, "steps": self.max_iter}

    def chat(self, user_input: str) -> str:
        """同步版本 —— 等全部处理完返回最终答案"""
        for update in self.chat_stream(user_input):
            if update["type"] == "answer":
                return update["content"]
        return "错误"

    def reset(self):
        self.memory.clear()
        self._usage = {"prompt": 0, "completion": 0}

    def get_session_id(self):
        return self.memory.session_id

    def get_long_memory(self):
        self.ltm.reload()  # 从文件重载，确保拿到最新数据
        return self.ltm.get_all()

    def index_knowledge(self):
        return self.knowledge.index_all()

    def get_usage(self) -> dict:
        """获取当前会话的 token 用量"""
        return dict(self._usage)

    def get_usage_str(self) -> str:
        """格式化的用量和费用估算"""
        p = self._usage["prompt"]
        c = self._usage["completion"]
        cost = (p * 0.5 + c * 2) / 1_000_000
        return f"⚡ {self._fmt(p)} in / {self._fmt(c)} out  ≈ ¥{cost:.4f}"

    @staticmethod
    def _fmt(n: int) -> str:
        if n >= 1000:
            return f"{n/1000:.1f}K"
        return str(n)

    def reset_usage(self):
        self._usage = {"prompt": 0, "completion": 0}
