from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums, PgVectorDistanceMethodEnums, PgVectorTableSchemeEnums, PgVectorIndexTypeEnums
from typing import List, Optional, Any
from models.db_schemas import RetrievedDocument
import logging
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):
    def __init__(self, db_client, default_vector_size: int = 786, 
                distance_method: str = None,
                index_threshold: int=100):
        
        self.db_client = db_client
        self.default_vector_size = default_vector_size
       
        self.index_threshold = index_threshold

        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method = PgVectorDistanceMethodEnums.VECTOR_COSINE_OPS.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            distance_method = PgVectorDistanceMethodEnums.VECTOR_IP_OPS.value 
      
        self.pgvector_table_prefix = PgVectorTableSchemeEnums._PREFIX.value
        self.distance_method = distance_method
        # self.logger = logging.getLogger("uvicorn")
        self.logger = logging.getLogger("app.indexer")
        self.logger.setLevel(logging.INFO)
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"


    async def connect(self):
        """Initialize pgvector extension in the database"""
        # async with self.db_client() as session:
        #     try:
        #         # Check if vector extension already exists
        #         result = await session.execute(sql_text(
        #             "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        #         ))
        #         extension_exists = result.scalar_one_or_none()

        #         if not extension_exists:
        #             # Only create if it doesn't exist
        #             await session.execute(sql_text("CREATE EXTENSION vector"))
        #             await session.commit()
        #     except Exception as e:
        #         # If extension already exists or any other error, just log and continue
        #         self.logger.warning(f"Vector extension setup: {str(e)}")
        #         await session.rollback()
        async with self.db_client() as session:
            async with session.begin():
                # Create pgvector extension if it doesn't exist
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
            self.logger.info("pgvector extension initialized successfully")
                
    async def disconnect(self):
        pass

    async def is_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection (table) exists in the database."""
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(
                    'SELECT 1 FROM pg_tables WHERE tablename = :collection_name')
                results = await session.execute(list_tbl, {"collection_name" : table_name})
                record = results.scalar_one_or_none()

        return record is not None
    
    async def list_all_collections(self) -> List:
        """List all collection (tables) with the pgvector prefix in the database."""
        records = []
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text("""
                    SELECT tablename FROM pg_tables 
                    WHERE tablename LIKE :prefix
                """)
                results = await session.execute(list_tbl, {"prefix": f"{self.pgvector_table_prefix}%"})
                records = results.scalars().all() 

        return records

    async def get_collection_info(self, collection_name: str) -> dict:
        """Get information about the collection"""
        table_name = f"{self.pgvector_table_prefix}{collection_name}"

        async with self.db_client() as session:
            async with session.begin():
                # Get table information
                table_info_query = sql_text(f"""
                    SELECT 
                    schemaname,tablename,tableowner,tablespace,hasindexes                
                    FROM pg_tables 
                    where tablename = :collection_name
                """)
                count_sql = sql_text(f'SELECT COUNT(*) FROM "{table_name}"')

                table_info = await session.execute(table_info_query, {"collection_name": table_name})
                record_count = await session.execute(count_sql)

                table_data = table_info.fetchone()
                if not table_data:
                    return None

                return {
                    "table_info" : {
                        'schemaname' : table_data[0],
                        'tablename' : table_data[1],
                        'tableowner' : table_data[2],
                        'tablespace': table_data[3],
                        'hasindexes' : table_data[4]
                    },
                    "record_count" : record_count.scalar()
                }
            
    async def delete_collection(self, collection_name: str):
        """Delete the collection"""
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_sql = sql_text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                await session.execute(delete_sql)

        return True
    
    async def create_collection(self, collection_name: str,
                                      embedding_size: int,
                                      do_reset: bool = False):
        """Create a new collection (table) with vector support."""
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                # Drop table if do_reset is True
                if do_reset:
                    await self.delete_collection(collection_name=collection_name)
                # Create table with vector column
                create_sql = sql_text(f"""
                    CREATE TABLE IF NOT EXISTS "{table_name}" (
                        {PgVectorTableSchemeEnums.ID.value} SERIAL PRIMARY KEY,
                        {PgVectorTableSchemeEnums.TEXT.value} TEXT,
                        {PgVectorTableSchemeEnums.CHUNK_ID.value} INTEGER,
                        {PgVectorTableSchemeEnums.METADATA.value} JSONB DEFAULT '{{}}'::jsonb,
                        {PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}),
                        FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)
                    )
                """)
                await session.execute(create_sql)
                self.logger.info(f"Created collection '{collection_name}' with embedding size {embedding_size}")

        return True
    
    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name=collection_name)
        table_name = f"{self.pgvector_table_prefix}{collection_name}"

        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text("""
                    SELECT 1 FROM pg_indexes
                    WHERE TABLENAME = :collection_name
                    AND INDEXNAME = :index_name
                    """
                )
                results = await session.execute(
                    check_sql,
                    {
                        "collection_name" : table_name,
                        "index_name": index_name
                    }
                )

                return bool(results.scalar_one_or_none())
            
    async def create_vector_index(self,collection_name: str,
                                    index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            self.logger.info(f"Index already exists for collection: {collection_name}")
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f'SELECT COUNT(*) FROM {table_name}')
                result = await session.execute(count_sql)
                records_count = result.scalar_one()

                if records_count < self.index_threshold:
                    self.logger.info(
                    f"Not enough records ({records_count}) to create index "
                    f"for collection: {collection_name}"
                    )
                    return False
                
                self.logger.info(f"START: Creating vector index for collection: {collection_name}")
                index_name = self.default_index_name(collection_name=collection_name)
                create_idx_sql = sql_text(
                    f'CREATE INDEX {index_name} ON "{table_name}" '
                    f'USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})'
                )

                self.logger.info(f"Creating index with SQL: {create_idx_sql}")

                await session.execute(create_idx_sql)

                self.logger.info(f"END: Created vector index for collection: {collection_name}")
        
        return True
    
    async def reset_vector_index(self, collection_name: str, 
                                index_type: str = PgVectorIndexTypeEnums.HNSW.value) -> bool:
        
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                drop_sql = sql_text(f'DROP INDEX IF EXISTS {index_name}')
                await session.execute(drop_sql)
        
        return await self.create_vector_index(collection_name=collection_name,
                                            index_type=index_type)


    async def insert_one(self, collection_name: str, text: str, vector: Any,
                                metadata: dict = None,
                                record_id : str = None):
        
        is_collection_exists = await self.is_collection_exist(collection_name=collection_name)
        if not is_collection_exists:
            self.logger.info(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        if not record_id :
            self.logger.info(f"Can not insert new record without record_id: {collection_name} ")
            return False
        
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f'INSERT INTO "{table_name}" '
                    f'({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value}, {PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value})'
                    'VALUES (:text, :vector, :metadata, :chunk_id)'
                )

                await session.execute(insert_sql, {
                    "text" : text,
                    "vector" : "[" + ",".join([str(v) for v in vector]) +"]" ,
                    "metadata" : json.dumps(metadata) if metadata else '{}',
                    "chunk_id" : record_id
                })

                await self.create_vector_index(collection_name=collection_name)
        return True

    async def insert_many(self, collection_name: str, texts: str, vectors: Any,
                   metadata: list = None,
                   record_ids : list = None,
                   batch_size : int = 50):
        
        is_collection_exists = await self.is_collection_exist(collection_name=collection_name)
        if not is_collection_exists:
            self.logger.info(f"Can not insert new records to non-existed collection: {collection_name}")
            return False
        
        if len(vectors) != len(record_ids):
            self.logger.info(f"Invalid data Items for collection: {collection_name}")
            return False
        
        if not metadata or len(metadata) == 0:
            metadata = [None] * len(texts)
        
        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_text = texts[i: i+batch_size]
                    batch_vectors = vectors[i: i+batch_size]
                    batch_metadata = metadata[i: i+batch_size]
                    batch_record_ids = record_ids[i: i+batch_size]

                    values = []

                    for _text, _vector, _metadata, _record_id in zip(batch_text, batch_vectors, batch_metadata, batch_record_ids):
                        values.append({
                            "text" : _text,
                            "vector" : "[" + ",".join([str(v) for v in _vector]) +"]" ,
                            "metadata" : json.dumps(_metadata) if _metadata else '{}',
                            "chunk_id" : _record_id
                        })
                    batch_insert_sql = sql_text(
                        f"""
                        INSERT INTO "{table_name}"
                        ({PgVectorTableSchemeEnums.TEXT.value},
                         {PgVectorTableSchemeEnums.VECTOR.value},
                         {PgVectorTableSchemeEnums.METADATA.value},
                         {PgVectorTableSchemeEnums.CHUNK_ID.value})
                        VALUES (:text, :vector, :metadata, :chunk_id)
                        """
                    )
                    await session.execute(batch_insert_sql, values)
        await self.create_vector_index(collection_name=collection_name)

        return True

    async def search_by_vector(self,collection_name: str,
                                    vector: Any,
                                    limit: int) -> List[RetrievedDocument]:
        
        is_collection_exists = await self.is_collection_exist(collection_name=collection_name)
        if not is_collection_exists:
            self.logger.info(f"Can not search for records in a non-existed collection: {collection_name}")
            return False
        
        vector = "[" + ",".join([str(v) for v in vector]) +"]"

        table_name = f"{self.pgvector_table_prefix}{collection_name}"
        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(
                    f"""
                    SELECT
                        {PgVectorTableSchemeEnums.TEXT.value} AS text,
                        1 - ({PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) AS score
                    FROM "{table_name}"
                    ORDER BY score DESC
                    LIMIT :limit
                    """
                )

                results = await session.execute(search_sql, {
                    "vector" : vector,
                     "limit": limit},
                )
                
                records = results.fetchall()

        return [
            RetrievedDocument(
                text=record.text,
                score=record.score
            )
            for record in records
        ]
            

        
