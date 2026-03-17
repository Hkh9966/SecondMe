"""
记忆管理器 - 管理Agent的多种记忆类型
使用 MiniMax API 生成 embedding
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import requests
import json

from app.agents.memory.vector_store import InMemoryVectorStore
from app.agents.memory.qdrant_store import QdrantVectorStore
from app.config import settings


class MemoryType:
    """记忆类型常量"""
    USER_PROFILE = "user_profile"      # 用户画像
    CONVERSATION = "conversation"     # 对话记忆
    INTEREST = "interest"             # 兴趣偏好
    HEART_MOMENT = "heart_moment"     # 心动时刻
    SUMMARY = "summary"               # 对话摘要


def get_minimax_embedding(text: str, emb_type: str = "query") -> np.ndarray:
    """
    使用 MiniMax API 获取文本 embedding

    Args:
        text: 输入文本
        emb_type: embedding 类型 ('query' 或 'db')
    """
    url = f"https://api.minimax.chat/v1/embeddings?GroupId={settings.minimax_group_id}"
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "texts": [text],
        "model": "embo-01",
        "type": emb_type
    }

    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
    result = response.json()

    if "vectors" in result and len(result["vectors"]) > 0:
        return np.array(result["vectors"][0], dtype=np.float32)
    else:
        raise ValueError(f"Failed to get embedding: {result}")


def embedding_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个 embedding 的余弦相似度"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


class MemoryItem:
    """记忆条目"""

    def __init__(self, memory_id: str, memory_type: str, content: str,
                 embedding: Optional[np.ndarray] = None,
                 metadata: Dict[str, Any] = None):
        self.id = memory_id
        self.type = memory_type
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class MemoryManager:
    """记忆管理器 - 使用 MiniMax embedding"""

    def __init__(self, agent_id: int, use_qdrant: bool = False):
        self.agent_id = agent_id
        self.embedding_dimension = 1024  # MiniMax embo-01 输出 1024 维向量

        # 初始化向量存储
        if use_qdrant:
            self.vector_store = QdrantVectorStore(
                f"agent_{agent_id}_memory",
                dimension=self.embedding_dimension
            )
        else:
            self.vector_store = InMemoryVectorStore(dimension=self.embedding_dimension)

        # 短期记忆 (当前对话)
        self.short_term_memory: List[Dict[str, Any]] = []

    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入 - 使用 MiniMax API"""
        return get_minimax_embedding(text, emb_type="db")

    async def add_memory(self, memory: MemoryItem):
        """添加记忆"""
        # 生成嵌入
        if memory.embedding is None:
            memory.embedding = self._generate_embedding(memory.content)

        # 存储到向量数据库
        await self.vector_store.add(
            vectors=[memory.embedding],
            payloads=[memory.to_dict()],
            ids=[memory.id]
        )

    async def add_conversation_turn(self, role: str, content: str,
                                    partner_name: str, emotion: str = None):
        """添加对话轮次到短期记忆"""
        turn = {
            "role": role,
            "content": content,
            "partner_name": partner_name,
            "emotion": emotion,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term_memory.append(turn)

    async def retrieve_memories(self, query: str, top_k: int = 5,
                               memory_type: str = None) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        # 使用 query 类型获取查询向量
        query_embedding = get_minimax_embedding(query, emb_type="query")

        # 向量搜索
        filter_cond = {"agent_id": self.agent_id}
        if memory_type:
            filter_cond["type"] = memory_type

        results = await self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            filter_conditions=filter_cond
        )

        return [r["payload"] for r in results]

    async def create_summary(self) -> str:
        """创建对话摘要"""
        if not self.short_term_memory:
            return ""

        summary_parts = []
        for turn in self.short_term_memory:
            role = "我" if turn["role"] == "assistant" else turn["partner_name"]
            summary_parts.append(f"{role}: {turn['content'][:100]}...")

        summary = " | ".join(summary_parts)
        return summary

    async def store_heart_moment(self, content: str, partner_name: str,
                                 score: float, context: str):
        """存储心动时刻"""
        import uuid
        moment = MemoryItem(
            memory_id=str(uuid.uuid4()),
            memory_type=MemoryType.HEART_MOMENT,
            content=f"与{partner_name}的心动时刻: {content}",
            metadata={
                "partner_name": partner_name,
                "score": score,
                "context": context,
                "agent_id": self.agent_id
            }
        )
        await self.add_memory(moment)

    def get_short_term_memory(self) -> List[Dict[str, Any]]:
        """获取短期记忆"""
        return self.short_term_memory.copy()

    def clear_short_term_memory(self):
        """清除短期记忆"""
        self.short_term_memory = []
