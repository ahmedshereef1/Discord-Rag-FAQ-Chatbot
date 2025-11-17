from qdrant_client import QdrantClient, models
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from typing import List, Optional, Any
import logging

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str):

        self.client = Optional[QdrantClient] = None
        self.db_path = db_path
        self.distance_method = None

        self.logger = logging.getLogger(__name__)

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.Dot

    def connect(self):
        """Create Qdrant client (local/embedded path)."""
        self.client = QdrantClient(path=self.db_path)
    
    def disconnect(self):
        raise NotImplementedError
    
    def is_collection_exist(self, collection_name: str):
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self) -> List:
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        if self.client is None:
            raise RuntimeError("Client not connected.")
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.client is None:
            raise RuntimeError("Client not connected.")
        if self.is_collection_exist(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        return None
    
    def create_collection(self, collection_name: str,
                          embedding_size: int,
                          do_reset: bool = False):
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
           
        if not self.is_collection_exist(collection_name=collection_name):
            _ = self.client.create_collection(collection_name,
                            vectors_config=models.VectorParams(
                            size=embedding_size,
                            distance=self.distance_method
                )
            )
            return True
        return False

    def insert_one(self, collection_name: str, text: str, vector: Any,
                   metadata: dict = None,
                   record_id : str = None):
        if self.client is None:
            raise RuntimeError("Client not connected.")

        if not self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection {collection_name}")
            return False
        
        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        vector=vector,
                        payload={
                            "text" : text,
                            "metadata" : metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True
    
    def insert_many(self, collection_name: str, texts: str, vectors: Any,
                   metadata: list = None,
                   record_ids : list = None,
                   batch_size : int = 50):
        if self.client is None:
            raise RuntimeError("Client not connected.")
        
        if not self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection {collection_name}")
            return False
        
        if metadata is None:
            metadata = [None] + len(texts)
        
        if record_ids is None:
            record_ids = [None] + len(texts)

        for i in range(0 , len(texts) , batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]

            batch_records = [
                models.Record(
                    vector=batch_vectors[x],
                    payload={
                        "text" : batch_texts[x],
                        "metadata" : batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]
            try: 
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True
    
    def search_by_vector(self, collection_name: str,
                            vector: Any,
                            limit: int = 5):
        
        if self.client is None:
            raise RuntimeError("Client not connected.")
        
        if not self.is_collection_exist(collection_name=collection_name):
            self.logger.error(f"Can not search non-existed collection {collection_name}")
            return []
        
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector, limit=limit)
    
        



            




        


    
