from celery import chain # pyright: ignore[reportMissingImports]
from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
import logging
from tasks.data_indexing import index_data_content
from tasks.file_processing import process_project_files
from tasks.data_indexing import _index_data_content

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.process_workflow.push_after_process_task", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60})

def push_after_process_task(self, prev_task_result):
    
    project_id = prev_task_result.get('project_id')
    do_reset = prev_task_result.get('do_reset')

    task_results = asyncio.run(
        _index_data_content(self, project_id, do_reset)
    )
    
    return {
        "project_id" : project_id,
        "do_reset": do_reset,
        "task_results" : task_results
    }


@celery_app.task(name="tasks.process_workflow.process_and_push_workflow", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_and_push_workflow(self, project_id: int,
                            file_id: int,
                            overlap_size: int,
                            chunk_size: int,
                            do_reset: int):
    
    workflow = chain(
        process_project_files.s(
            project_id=project_id,
            file_id=file_id,
            overlap_size=overlap_size,
            chunk_size=chunk_size,
            do_reset=do_reset
        ),
        push_after_process_task.s()
    )

    result = workflow.apply_async()

    return {
        "signal": "WORKFLOW_STARTED",
        "workflow_id": result.id,
        "tasks" : ["tasks.file_processing.process_project_files", 
                   "tasks.data_indexing.index_data_content"]
    }
