from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
import logging
from utils.idempotency_manager import IdempotencyManager

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.maintenance.clean_celery_executation_table", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60})

def clean_celery_executation_table(self):
    
    return asyncio.run(_clean_celery_executation_table_async(self))


async def _clean_celery_executation_table_async(task_instance):

    db_client, vectordb_client = None, None

    try: 
        (db_engine, db_client, llm_provider_factory,
            vectordb_provider_factory, generation_client, embedding_client,
            vectordb_client, template_parser) = await get_setup_utils()
        
        # Create idempotency manager
        idempotency_manager = IdempotencyManager(db_client=db_client, db_engine=db_engine)
        
        _ =await idempotency_manager.cleanup_old_tasks()

        return True
    
    
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    
    finally:
        try:
            if db_engine:
                await db_engine.dispose()

            if vectordb_client:
                await vectordb_client.disconnect()
        except Exception as e:
            logger.error(f"Error in closing resources: {str(e)}")