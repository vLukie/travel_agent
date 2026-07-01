"""
记忆模块 —— 对话历史管理 + 长期记忆存储
- 短期记忆：当前会话的消息列表，自动持久化
- 长期记忆：跨会话的键值存储
"""

import json
import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent / "memory_logs"
MAX_MSG_BEFORE_SUMMARY = 20
MAX_SESSIONS = 20


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self, session_id: str = None):
        MEMORY_DIR.mkdir(exist_ok=True)
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages: list[dict] = []
        self._load()

    def _path(self) -> Path:
        return MEMORY_DIR / f"session_{self.session_id}.json"

    def _load(self):
        p = self._path()
        if p.exists():
            try:
                self.messages = json.loads(p.read_text(encoding="utf-8")).get("messages", [])
            except: self.messages = []

    def _save(self):
        p = self._path()
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({
            "session_id": self.session_id,
            "updated_at": datetime.datetime.now().isoformat(),
            "messages": self.messages,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        _cleanup_old_sessions()

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._save()

    def get_messages(self) -> list[dict]:
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def needs_summary(self) -> bool:
        real_msgs = [m for m in self.messages if not (m.get("role") == "system" and "[对话摘要]" in m.get("content", ""))]
        return len(real_msgs) > MAX_MSG_BEFORE_SUMMARY

    def compress(self, summary: str):
        """用摘要压缩历史，保留最近 20 条"""
        recent = self.messages[-20:]
        self.messages = [{"role": "system", "content": f"[对话摘要] {summary}"}] + recent
        self._save()

    def clear(self):
        self.messages = []
        self._save()


def list_all_sessions() -> list[dict]:
    """列出所有历史会话"""
    MEMORY_DIR.mkdir(exist_ok=True)
    sessions = []
    for f in sorted(MEMORY_DIR.glob("session_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": data["session_id"],
                "updated": data.get("updated_at", ""),
                "count": len(data.get("messages", [])),
            })
        except Exception:
            continue
    return sessions


def load_session_messages(session_id: str) -> list[dict]:
    """加载指定历史会话的全部消息"""
    path = MEMORY_DIR / f"session_{session_id}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("messages", [])
    except Exception:
        return []


def _cleanup_old_sessions():
    """清理历史会话，最多保留 MAX_SESSIONS 条（按更新时间取最新）"""
    MEMORY_DIR.mkdir(exist_ok=True)
    files = sorted(MEMORY_DIR.glob("session_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[MAX_SESSIONS:]:
        try:
            f.unlink()
        except Exception:
            pass


class LongTermMemory:
    """长期记忆 —— JSON 键值存储"""

    def __init__(self):
        MEMORY_DIR.mkdir(exist_ok=True)
        self._file = MEMORY_DIR / "long_term.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self._file.exists():
            try: return json.loads(self._file.read_text(encoding="utf-8"))
            except: return {}
        return {}

    def _save(self):
        self._file.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def remember(self, key: str, value: str):
        self._data[key] = {"value": value, "updated_at": datetime.datetime.now().isoformat()}
        self._save()

    def recall(self, key: str) -> str | None:
        r = self._data.get(key)
        return r["value"] if r else None

    def get_all(self) -> str:
        return self._format()

    def reload(self):
        """从文件重新加载（工具写入后调用）"""
        self._data = self._load()

    def _format(self) -> str:
        if not self._data:
            return "暂无长期记忆"
        return "[关于用户的信息]\n" + "\n".join(f"- {k}: {v['value']}" for k, v in self._data.items())
