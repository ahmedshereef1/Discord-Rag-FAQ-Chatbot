from qdrant_client import QdrantClient, models
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from typing import List, Optional, Any
import logging
from models.db_schemas import RetrievedDocument


class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_client: str, default_vector_size: int = 786, 
                distance_method: str = None,
                index_threshold: int=100):
        
        self.client: Optional[QdrantClient] = None
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold
        self.distance_method = None
        self.logger = logging.getLogger("uvicorn")

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.Dot

    async def connect(self):
        """Create Qdrant client (local/embedded path)."""
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        if self.client is None:
            return
        try:
            # Qdrant client may not need explicit close, but if it has a close/disconnect method call it here
            if hasattr(self.client, "close"):
                self.client.close()
        finally:
            self.client = None

    async def is_collection_exist(self, collection_name: str) -> bool:
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self) -> List:
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.get_collections()

    async def get_collection_info(self, collection_name: str) -> dict:
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.get_collection(collection_name=collection_name)

    async def delete_collection(self, collection_name: str):
        if self.client is None:
            raise RuntimeError("Client not connected.")
        if await self.is_collection_exist(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        return None

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ) -> bool:
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_method
                ),
            )
            return True
        return False

    async def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: Any,
        metadata: Optional[dict] = None,
        record_id: Optional[str] = None,
    ) -> bool:
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(
                f"Can not insert new record to non-existed collection {collection_name}"
            )
            return False

        try:
            record = models.Record(
                id=record_id,
                vector=vector,
                payload={"text": text, "metadata": metadata},
            )
            _ = self.client.upload_records(collection_name=collection_name, records=[record])
        except Exception as e:
            self.logger.error(f"Error while inserting record: {e}")
            return False

        return True

    async def insert_many(
        self,
        collection_name: str,
        texts: List[str],
        vectors: List[Any],
        metadata: Optional[List[dict]] = None,
        record_ids: Optional[List[str]] = None,
        batch_size: int = 50,
    ) -> bool:
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(
                f"Can not insert new record to non-existed collection {collection_name}"
            )
            return False

        n = len(texts)
        if metadata is None:
            metadata = [None] * n
        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, n, batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={"text": batch_texts[x], "metadata": batch_metadata[x]},
                )
                for x in range(len(batch_texts))
            ]
            try:
                _ = self.client.upload_records(
                    collection_name=collection_name, records=batch_records
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    async def search_by_vector(self, collection_name: str, vector: Any, limit: int = 5):
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if not await self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not search non-existed collection {collection_name}")
            return []

        results = self.client.search(collection_name=collection_name, query_vector=vector, limit=limit)

        if not results or len(results) == 0 :
            return None
        
        return [
            RetrievedDocument(**{
                "score" : result.score,
                "text" : result.payload["text"]
            })
            for result in results
        ]
