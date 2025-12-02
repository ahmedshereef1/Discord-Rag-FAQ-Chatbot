from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
from controllers import NLPController, ProcessController
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemas import DataChunk
from models.AssetModel import AssetModel
from models import ResponseSingnals
from models.enums.AssetTypeEnum import AssetTypeEnum
import logging


logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.file_processing.process_project_files", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_project_files(self, project_id: int,
                file_id: int, overlap_size: int, chunk_size: int, do_reset: int):

    return asyncio.run(
        _process_project_files(
            self,
            project_id=project_id,
            file_id=file_id,
            overlap_size=overlap_size,
            chunk_size=chunk_size,
            do_reset=do_reset
        )
    )


async def _process_project_files(task_instance, project_id: int,
                                 file_id: int, overlap_size: int,
                                 chunk_size: int, do_reset: int):
    
    db_client, vectordb_client = None, None

    try: 
        (db_engine, db_client, llm_provider_factory,
            vectordb_provider_factory, generation_client, embedding_client,
            vectordb_client, template_parser) = await get_setup_utils()
        
        project_model = await ProjectModel.create_instance(
            db_client=db_client
        )

        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )

        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            template_parser=template_parser,
            embedding_client=embedding_client
        )

        asset_model = await AssetModel.create_instance(
            db_client=db_client)
        
        project_files_ids = {}
        if file_id:
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project.project_id,
                asset_name=file_id
            )

            if asset_record is None:
                task_instance.update_state( 
                    state='FAILURE',
                    meta={
                        "signal": ResponseSingnals.FILE_ID_ERROR.value,
                    }
                )

                raise Exception(f"No assests for file_id: {file_id}")

            project_files_ids = {
                asset_record.asset_id : asset_record.asset_name
            }
        else:

            project_files = await asset_model.get_all_project_assets(
                asset_project_id=project.project_id,
                asset_type=AssetTypeEnum.File.value
                )

            project_files_ids = {
                record.asset_id : record.asset_name
                for record in project_files
            }
        
        if len(project_files_ids) == 0:
            task_instance.update_state(
                state='FAILURE',
                meta={
                    "signal": ResponseSingnals.NO_FILES_ERROR.value,
                }
            )

            raise Exception(f"No files found for project_id: {project.project_id}")

        process_controller = ProcessController(project_id=project_id)

        no_of_records = 0
        no_of_files = 0

        chunk_model = await ChunkModel.create_instance(
                db_client=db_client
            )

        if do_reset == 1:
            # delete associated vectors collection
            collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
            _ = await vectordb_client.delete_collection(collection_name=collection_name)
            
            # delete associated chunks
            _ = await chunk_model.delete_chunks_by_project_id(
                    project_id=project.project_id ,
            )
            
        for asset_id, file_id in project_files_ids.items():

            file_content = process_controller.get_file_content(file_id=file_id)

            if file_content is None:
                logger.error(f"Error while processing file: {file_id}")
                continue

            file_chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=chunk_size,
                chunk_overlap=overlap_size)
            
            if file_chunks is None or len(file_chunks) == 0:
                logger.error(f"No chunks created for file: {file_id}")
                pass
            
            file_chunks_records = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i+1,
                    chunk_project_id=project.project_id,
                    chunk_asset_id=asset_id
                )
                for i, chunk in enumerate(file_chunks)
            ]

            

            no_of_records += await chunk_model.insert_many_chunks(
                chunks=file_chunks_records
            )
            no_of_files += 1
        
        task_instance.update_state(
            state='SUCCESS',
            meta={
                "signal": ResponseSingnals.NO_FILES_ERROR.value,
            }
        )

        return {
                "signal": ResponseSingnals.PROCESSING_SUCCESS.value,
                "inserted_chunks" : no_of_records,
                "processed_files" : no_of_files  
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