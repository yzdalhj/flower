"""向量存储服务 - 基于ChromaDB"""

import json
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from app.config import get_settings

settings = get_settings()


class VectorStore:
    """
    向量存储服务
    使用ChromaDB存储和检索文本向量
    """

    def __init__(self, collection_name: str = "memories"):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加记忆到向量数据库

        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 元数据

        Returns:
            向量ID
        """
        # 生成文档ID
        doc_id = f"memory_{memory_id}"

        # 准备元数据（ChromaDB要求值为基本类型）
        chroma_metadata = {}
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    chroma_metadata[key] = value
                else:
                    chroma_metadata[key] = json.dumps(value)

        # 添加到集合
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[chroma_metadata],
        )

        return doc_id

    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            n_results: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict,
        )

        # 格式化结果
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )

        return formatted_results

    async def delete_memory(self, memory_id: str) -> bool:
        """删除向量记忆"""
        doc_id = f"memory_{memory_id}"
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    async def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """更新向量记忆（先删除后添加）"""
        await self.delete_memory(memory_id)
        return await self.add_memory(memory_id, content, metadata)

    async def get_memory_count(self) -> int:
        """获取记忆总数"""
        return self.collection.count()


class EmbeddingService:
    """
    文本嵌入服务
    使用sentence-transformers生成文本向量
    """

    _model = None

    @classmethod
    def get_model(cls):
        """获取嵌入模型（单例）"""
        if cls._model is None:
            from sentence_transformers import SentenceTransformer

            cls._model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
        return cls._model

    @classmethod
    def encode(cls, texts: List[str]) -> List[List[float]]:
        """
        编码文本为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        model = cls.get_model()
        # 添加指令前缀以提高检索效果
        instruction = "为这个句子生成表示："
        texts_with_instruction = [instruction + text for text in texts]
        embeddings = model.encode(texts_with_instruction, normalize_embeddings=True)
        return embeddings.tolist()

    @classmethod
    def encode_single(cls, text: str) -> List[float]:
        """编码单个文本"""
        return cls.encode([text])[0]


class HybridMemoryRetriever:
    """
    混合记忆检索器
    结合向量检索和关键词检索
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        混合检索

        Args:
            query: 查询文本
            user_id: 用户ID（用于过滤）
            n_results: 返回结果数

        Returns:
            检索结果
        """
        # 构建过滤条件
        filter_dict = None
        if user_id:
            filter_dict = {"user_id": user_id}

        # 向量检索
        vector_results = await self.vector_store.search(
            query=query,
            n_results=n_results * 2,  # 多检索一些用于重排序
            filter_dict=filter_dict,
        )

        # 简单重排序（可以添加更复杂的算法）
        # 按距离排序（越小越相似）
        vector_results.sort(key=lambda x: x["distance"])

        return vector_results[:n_results]
