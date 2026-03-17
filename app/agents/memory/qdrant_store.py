"""
Qdrant向量数据库实现
"""
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid


class QdrantVectorStore:
    """Qdrant向量存储实现"""

    def __init__(self, collection_name: str, dimension: int = 384,
                 url: str = None, api_key: str = None):
        self.collection_name = collection_name
        self.dimension = dimension

        # 初始化客户端 (本地或远程)
        if url and api_key:
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            self.client = QdrantClient(path="./qdrant_data")

        self._init_collection()

    def _init_collection(self):
        """初始化collection"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
        except Exception:
            # Collection可能已存在
            pass

    async def add(self, vectors: List[np.ndarray], payloads: List[Dict[str, Any]], ids: List[str]):
        """添加向量"""
        points = []
        for i, (vec, payload) in enumerate(zip(vectors, payloads)):
            point = PointStruct(
                id=ids[i] if i < len(ids) else str(uuid.uuid4()),
                vector=vec.tolist(),
                payload=payload
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    async def search(self, query_vector: np.ndarray, top_k: int = 5,
                   filter_conditions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        query_filter = None
        if filter_conditions:
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=must_conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
            query_filter=query_filter
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]

    async def delete(self, ids: List[str]):
        """删除向量"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取向量"""
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[id]
        )
        if results:
            return results[0].payload
        return None


def get_vector_store() -> QdrantVectorStore:
    """获取向量存储实例"""
    return QdrantVectorStore("secondme_memory")
