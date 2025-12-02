from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schemas.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models import ResponseSingnals
from controllers import NLPController
import logging
import inspect
from tqdm.auto import tqdm
from tasks.data_indexing import index_data_content

# silence Cohere provider logs ONLY
logging.getLogger("src.stores.llm.providers.CohereProvider").setLevel(logging.CRITICAL)
logging.getLogger("src.stores.llm.providers.OpenAIProvider").setLevel(logging.CRITICAL)


logger = logging.getLogger("uvicorn.error")
nlp_router = APIRouter(prefix="/api/v1/nlp", tags=["api_v1", "nlp"])


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request,
                        project_id: int,
                        push_request: PushRequest):
    # Delegate indexing to Celery task
    task = index_data_content.delay(
        project_id=project_id,
        do_reset=push_request.do_reset
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "signal": ResponseSingnals.DATA_PUSH_TASK_READY.value,
            "task_id": task.id
        }
    )

#     project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
#     chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
#     project = await project_model.get_project_or_create_one(project_id=project_id)
    
#     if not project:
#         return JSONResponse(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             content={"signal": ResponseSingnals.PROJECT_NOT_FOUND_ERROR.value}
#         )
    
#     nlp_controller = NLPController(
#         vectordb_client=request.app.vectordb_client,
#         generation_client=request.app.generation_client,
#         embedding_client=request.app.embedding_client,
#         template_parser=request.app.template_parser
#     )
    
#     has_records = True
#     page_no = 1
#     inserted_items_count = 0
#     idx = 0
    
#     # Create collection if not exist
#     collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
#     _ = await request.app.vectordb_client.create_collection(
#         collection_name=collection_name,
#         embedding_size=request.app.embedding_client.embedding_size,
#         do_reset=push_request.do_reset,
#     )
    
#     # Setup batching and progress bar
#     total_chunk_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
#     pbar = tqdm(total=total_chunk_count, desc="Vector Indexing", position=0)
    
#     try:
#         while has_records:
#                 page_chunks = await chunk_model.get_project_chunks(
#                     project_id=project.project_id, 
#                     page_no=page_no
#                 )

#                 if not page_chunks:
#                     has_records = False
#                     break
                
#                 page_no += 1
#                 # chunk_ids = list(range(idx, idx + len(page_chunks)))  # for Qdrant
#                 chunk_ids = [chunk.chunk_id for chunk in page_chunks]  # for PgVector

#                 # idx += len(page_chunks) # for qdrant

#                 result = await nlp_controller.index_into_vector_db(
#                     project=project,
#                     chunks=page_chunks,
#                     do_reset=push_request.do_reset,
#                     chunk_ids=chunk_ids
#                 )

#                 if inspect.isawaitable(result):
#                     is_inserted = await result
#                 else:
#                     is_inserted = result

#                 if not is_inserted:
#                     return JSONResponse(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         content={"signal": ResponseSingnals.INSERT_INTO_VECTORDB_ERROR.value}
#                     )

#                 pbar.update(len(page_chunks))
#                 inserted_items_count += len(page_chunks)
#     finally:
#         pbar.close()
        
#     index_created = await request.app.vectordb_client.create_vector_index(
#         collection_name=collection_name
#     )

#     # Log index creation result
#     if index_created:
#         request.app.logger.info(f"Vector index successfully created for: {collection_name}")
#     else:
#         request.app.logger.info(f"Vector index skipped (already exists or threshold not met) for: {collection_name}")

#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content={
#             "signal": ResponseSingnals.INSERT_INTO_VECTORDB_SUCCESS.value,
#             "inserted_items_count": inserted_items_count
#         }
#     )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSingnals.PROJECT_NOT_FOUND_ERROR.value}
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    collection_info = await nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSingnals.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSingnals.PROJECT_NOT_FOUND_ERROR.value}
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    try:
        results = await nlp_controller.search_vector_db_collection(
            project=project,
            text=search_request.text,
            limit=search_request.limit or 10
        )
    except Exception as exc:
        request.app.logger.exception("Vector DB search failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSingnals.VECTORDB_SEARCH_ERROR.value, "error": str(exc)}
        )

    if results is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSingnals.VECTORDB_SEARCH_ERROR.value}
        )

    return JSONResponse(
        content={
            "signal": ResponseSingnals.VECTOTDB_SEARCH_SUCCESS.value,
            "results": results
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSingnals.PROJECT_NOT_FOUND_ERROR.value}
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSingnals.RAG_ANSWER_ERROR.value}
        )

    return JSONResponse(
            content={
                "signal": ResponseSingnals.RAG_ANSWER_SUCCESS.value,
                "answer": answer,
                "full_prompt" : full_prompt,
                "chat_history" : chat_history 
                }
        )