from .BaseController import BaseController
from models.db_schemas import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnums
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, template_parser , embedding_client):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: int):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self, project : Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name= collection_name)

    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        # Check if collection exists before querying
        collection_exists = await self.vectordb_client.is_collection_exist(collection_name)
        if not collection_exists:
            logger.warning(f"Collection '{collection_name}' does not exist for project {project.project_id}")
            return {
                "collection_name": collection_name,
                "exists": False,
                "record_count": 0,
                "message": "Collection not found - may need to index documents first"
            }
            
        collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)
        
        def default_serializer(obj):
            # SQLAlchemy Row  
            if hasattr(obj, "_mapping"):
                return dict(obj._mapping)

            # __dict__ (زي كائنات Qdrant)
            if hasattr(obj, "__dict__"):
                return obj.__dict__

            # fallback أخير
            return str(obj)

        return json.loads(
            json.dumps(collection_info, default=default_serializer)
        )
    
    async def index_into_vector_db(self, project: Project,
                            chunk_ids: list[int],
                            chunks: List[DataChunk], do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)
        
        # step2: manage item 
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]

        vectors = self.embedding_client.embed_text(text=texts, 
                                            document_type=DocumentTypeEnums.DOCUMENT.value)


        # step3: create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size ,
            do_reset = do_reset
        )

        # step4: insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts= texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=chunk_ids
        )

        return True
    
    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):
        collection_name = self.create_collection_name(project_id=project.project_id)

        if not text or not text.strip():
            raise ValueError("Search text is empty")
        
        collection_exists = await self.vectordb_client.is_collection_exist(collection_name)
        if not collection_exists:
            logger.warning(f"Collection '{collection_name}' does not exist")
            return []

        # Embed the query text
        try:
            vector = self.embedding_client.embed_text(
                text=text,
                document_type=DocumentTypeEnums.QUERY.value
            )
            # Await if coroutine
            if hasattr(vector, "__await__"):
                vector = await vector
        except Exception as e:
            logger.exception("Failed to embed query text")
            raise

        if not vector:
            logger.error("Embedding returned empty vector")
            return []

        if isinstance(vector, list) and len(vector) > 0:
            # Check if it's nested (List[List[float]])
            if isinstance(vector[0], list):
                vector = vector[0]  # Extract first embedding
            # Now vector should be List[float]
            if len(vector) == 0:
                logger.error("Embedding returned empty vector")
                return []
        else:
            logger.error("Invalid vector format")
            return []

         # Perform semantic search
        try:
            results = await self.vectordb_client.search_by_vector(
                 collection_name=collection_name,
                 vector=vector,
                 limit=limit
            )
        except Exception as e:
            logger.exception("Vector DB search_by_vector failed")
            raise
         
        if not results:
            return []

        # Convert to json-friendly structure
        try:
            return json.loads(json.dumps(results, default=lambda x: x.__dict__))
        except Exception:
            # Fallback: return raw results if transform fails
            return results

    async def answer_rag_question(self, project: Project, query: str, limit: int = 10):
       
        answer, full_prompt, chat_history = None, None, None

        # step 1 : retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(project=project,
                                                               text=query,
                                                               limit=limit)
        if not retrieved_documents or len(retrieved_documents) == 0 :
            return answer, full_prompt, chat_history
        
        # step 2 : construct LLM prompt
        system_prompt = self.template_parser.get(
            "rag", "system_prompt"
        )

        document_prompt = "\n".join([
            self.template_parser.get(
                "rag",
                "document_prompt",
                {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(
                        doc.get("text") or doc.get("content") or str(doc)
                    )
                },
            )
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt = self.template_parser.get(
            "rag", "footer_prompt", {
                "query" : query
            }
        )

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        full_prompt = "\n\n".join([ document_prompt, footer_prompt ])
        
        answer = self.generation_client.generate_text(prompt=full_prompt,
                                        chat_history=chat_history,
                                        temperature=0.7)
        
        return answer, full_prompt, chat_history




        

    