"""
向量记忆存储接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np


class VectorStore(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    async def add(self, vectors: List[np.ndarray], payloads: List[Dict[str, Any]], ids: List[str]):
        """添加向量"""
        pass

    @abstractmethod
    async def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        pass

    @abstractmethod
    async def delete(self, ids: List[str]):
        """删除向量"""
        pass


class InMemoryVectorStore(VectorStore):
    """内存向量存储 (用于开发/测试)"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []
        self.payloads: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    async def add(self, vectors: List[np.ndarray], payloads: List[Dict[str, Any]], ids: List[str]):
        """添加向量到内存"""
        self.vectors.extend(vectors)
        self.payloads.extend(payloads)
        self.ids.extend(ids)

    async def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """简单的余弦相似度搜索"""
        if not self.vectors:
            return []

        # 计算余弦相似度
        similarities = []
        for i, vec in enumerate(self.vectors):
            similarity = np.dot(query_vector, vec) / (np.linalg.norm(query_vector) * np.linalg.norm(vec) + 1e-8)
            similarities.append((i, similarity))

        # 排序并返回top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, sim in similarities[:top_k]:
            result = self.payloads[i].copy()
            result["score"] = float(sim)
            results.append(result)

        return results

    async def delete(self, ids: List[str]):
        """删除向量"""
        ids_to_delete = set(ids)
        new_vectors = []
        new_payloads = []
        new_ids = []
        for i, id_ in enumerate(self.ids):
            if id_ not in ids_to_delete:
                new_vectors.append(self.vectors[i])
                new_payloads.append(self.payloads[i])
                new_ids.append(self.ids[i])

        self.vectors = new_vectors
        self.payloads = new_payloads
        self.ids = new_ids
