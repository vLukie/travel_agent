"""
知识库模块 —— RAG 检索增强生成
ChromaDB 向量数据库 + Embedding 实现语义检索
Embedding：fastembed（首选）→ sentence-transformers（兜底）
"""

import hashlib
from pathlib import Path

from config import CONFIG


class KnowledgeBase:
    """个人知识库"""

    def __init__(self):
        self.embedder = None
        self.embedder_name = ""  # 记录当前用的是哪个库
        self.collection = None
        self.db_path = CONFIG["knowledge"]["chroma_db_path"]
        self.knowledge_dir = Path(CONFIG["knowledge"]["knowledge_dir"])
        self.model_name = CONFIG["knowledge"]["embedding_model"]
        self._ready = False

    def _init(self):
        if self._ready:
            return
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.db_path)
            self.collection = client.get_or_create_collection(
                name="personal_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            self._ready = True
        except ImportError:
            print("⚠️  chromadb 未安装")
        except Exception as e:
            print(f"⚠️  ChromaDB 初始化失败: {e}")

    def _embed(self, text: str) -> list[float]:
        """获取文本的 embedding 向量"""
        if self.embedder is None:
            self._load_embedder()
        if self.embedder is not None:
            try:
                return self.embedder.encode(text).tolist()
            except Exception as e:
                print(f"⚠️  embedding 推理失败: {e}")
        return []

    def _load_embedder(self):
        """加载 sentence-transformers 模型（30s 超时保护）"""
        try:
            from sentence_transformers import SentenceTransformer
            import threading
            result = [None]
            error = [None]

            def _load():
                try:
                    result[0] = SentenceTransformer(self.model_name)
                except Exception as e:
                    error[0] = e

            t = threading.Thread(target=_load, daemon=True)
            t.start()
            t.join(timeout=30)
            if t.is_alive():
                print("⚠️  embedding 模型加载超时，跳过知识库")
                return
            if error[0]:
                print(f"⚠️  embedding 模型加载失败: {error[0]}")
                return
            self.embedder = result[0]
            self.embedder_name = "sentence-transformers"
        except ImportError:
            print("⚠️  sentence-transformers 未安装，跳过知识库")

    def _chunk(self, text: str, size: int = 512) -> list[str]:
        paras = text.split("\n\n")
        chunks, cur = [], ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(cur) + len(p) < size:
                cur = (cur + "\n\n" + p).strip()
            else:
                if cur:
                    chunks.append(cur)
                cur = p if len(p) <= size else p[:size]
        if cur:
            chunks.append(cur)
        return chunks or [text[:size]]

    def add_doc(self, doc_id: str, text: str, metadata: dict = None):
        self._init()
        if not self._ready or not self.collection:
            return
        chunks = self._chunk(text)
        ids, embs, docs, metas = [], [], [], []
        for i, chunk in enumerate(chunks):
            e = self._embed(chunk)
            if not e:
                continue
            ids.append(f"{doc_id}_{i}")
            embs.append(e)
            docs.append(chunk)
            metas.append(metadata or {})
        if ids:
            self.collection.add(ids=ids, embeddings=embs, documents=docs, metadatas=metas)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        self._init()
        if not self._ready or not self.collection:
            return []
        qe = self._embed(query)
        if not qe:
            return []
        results = self.collection.query(query_embeddings=[qe], n_results=min(top_k, 10))
        hits = []
        if results["documents"] and results["documents"][0]:
            for i, d in enumerate(results["documents"][0]):
                hits.append({
                    "content": d,
                    "score": results["distances"][0][i] if results.get("distances") else 0,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                })
        return hits

    def index_all(self):
        """索引 knowledge/ 目录下的所有 .md .txt 文件"""
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for f in self.knowledge_dir.rglob("*"):
            if f.suffix.lower() not in (".md", ".txt"):
                continue
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace").strip()
                if not text:
                    continue
                doc_id = "file_" + hashlib.md5(str(f).encode()).hexdigest()
                self.add_doc(doc_id, text, {"source": str(f), "filename": f.name})
                count += 1
            except Exception:
                pass
        return count

    def format_context(self, query: str, top_k: int = 3) -> str:
        """检索相关知识，格式化为系统上下文"""
        results = self.search(query, top_k)
        if not results:
            return ""
        lines = ["\n📖 [知识库相关参考]"]
        for i, r in enumerate(results, 1):
            src = r["metadata"].get("filename", "未知")
            lines.append(f"\n--- 参考 {i} ({src}) ---")
            lines.append(r["content"][:500])
        return "\n".join(lines)
