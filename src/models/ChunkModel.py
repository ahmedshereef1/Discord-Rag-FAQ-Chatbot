from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId # pyright: ignore[reportMissingImports]
from pymongo import InsertOne # pyright: ignore[reportMissingImports]

class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_clinet[DataBaseEnum.COLLECTION_CHUNKS_NAME.value]
    
    # Create Chunk
    async def create_chunk(self,chunk: DataChunk):
        result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))
        chunk._id = result.inserted_id
        return chunk

    # Get chunk by id
    async def get_chunk(self, chunk_id: str):
        result = await self.collection.find_one({
            "_id" : ObjectId(chunk_id)
        })

        if result is None:
            return None
        
        return DataChunk(**result)

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]

            operations = [
              InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
             for chunk in batch
            ]

            await self.collection.bulk_write(operations)
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id" : project_id
        })

        return result.deleted_count
    