from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
import logging
from fastapi.responses import JSONResponse
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models import ResponseSingnals
from controllers import NLPController
import inspect
from tqdm.auto import tqdm


logger = logging.getLogger(__name__)    

@celery_app.task(name="tasks.data_indexing.index_data_content", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60})
def index_data_content(self, project_id: str, do_reset: int):

    return asyncio.run(_index_data_content(self, 
                                           project_id=project_id,
                                           do_reset=do_reset)
                    )

async def _index_data_content(task_instance, project_id: str, do_reset: int):

    db_client, vectordb_client = None, None

    try:
        (db_engine, db_client, llm_provider_factory,
            vectordb_provider_factory, generation_client, embedding_client,
            vectordb_client, template_parser) = await get_setup_utils()
        
        project_model = await ProjectModel.create_instance(db_client=db_client)
        chunk_model = await ChunkModel.create_instance(db_client=db_client)
        project = await project_model.get_project_or_create_one(project_id=project_id)

        if not project:
            task_instance.update_state(
                state='FAILURE',
                meta={
                    "signal": ResponseSingnals.PROJECT_NOT_FOUND_ERROR.value
                }
            )

            raise Exception(f"Project not found for project_id: {project_id}")

        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client=embedding_client,
            template_parser=template_parser
        )

        has_records = True
        page_no = 1
        inserted_items_count = 0
        idx = 0

        # Create collection if not exist
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # Setup batching and progress bar
        total_chunk_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        pbar = tqdm(total=total_chunk_count, desc="Vector Indexing", position=0)

        try:
            while has_records:
                    page_chunks = await chunk_model.get_project_chunks(
                        project_id=project.project_id, 
                        page_no=page_no
                    )

                    if not page_chunks:
                        has_records = False
                        break
                    
                    page_no += 1
                    # chunk_ids = list(range(idx, idx + len(page_chunks)))  # for Qdrant
                    chunk_ids = [chunk.chunk_id for chunk in page_chunks]  # for PgVector

                    # idx += len(page_chunks) # for qdrant

                    result = await nlp_controller.index_into_vector_db(
                        project=project,
                        chunks=page_chunks,
                        do_reset=do_reset,
                        chunk_ids=chunk_ids
                    )

                    if inspect.isawaitable(result):
                        is_inserted = await result
                    else:
                        is_inserted = result

                    if not is_inserted:
                        task_instance.update_state(
                            state='FAILURE',
                            meta={
                                "signal": ResponseSingnals.INSERT_INTO_VECTORDB_ERROR.value
                            }
                        )

                        raise Exception(f"Error inserting into vector DB | project_id: {project_id}")

                    pbar.update(len(page_chunks))
                    inserted_items_count += len(page_chunks)
        finally:
            pbar.close()

        index_created = await vectordb_client.create_vector_index(
            collection_name=collection_name
        )

        # Log index creation result
        if index_created:
            logger.info(f"Vector index successfully created for: {collection_name}")
        else:
            logger.info(f"Vector index skipped (already exists or threshold not met) for: {collection_name}")


        task_instance.update_state(
            state='SUCCESS',
            meta={
                "signal": ResponseSingnals.INSERT_INTO_VECTORDB_SUCCESS.value,
            }
        )

        return {
                "signal": ResponseSingnals.INSERT_INTO_VECTORDB_SUCCESS.value,
                "inserted_items_count": inserted_items_count
        }
        

    except Exception as e:
        logger.error(f"Error in processing project files: {str(e)}")
        raise
    
    finally:
        try:
            if db_engine:
                await db_engine.dispose()

            if vectordb_client:
                await vectordb_client.disconnect()
        except Exception as e:
            logger.error(f"Error in closing resources: {str(e)}")