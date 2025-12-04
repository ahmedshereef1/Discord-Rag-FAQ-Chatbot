import hashlib
import json 
from datetime import datetime, timedelta, timezone
from models.db_schemas.minirag.schemes.celery_task_execution import CeleryTaskExecution
from sqlalchemy import select, delete

class IdempotencyManager:
    
    def __init__(self, db_client, db_engine):

        self.db_client = db_client
        self.db_engine = db_engine

    def create_args_hash(self, task_name: str, task_args: dict):

        combined_data = {
            **task_args,
            "task_name": task_name
        }

        json_string = json.dumps(combined_data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()
    
    async def create_task_record(self, task_name: str, task_args: dict, celery_task_id: str = None) -> CeleryTaskExecution:
        """Create a new task execution record in the database."""
        args_hash = self.create_args_hash(task_name=task_name, task_args=task_args)

        task_record = CeleryTaskExecution(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            celery_task_id=celery_task_id,
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(), 
        )

        session = self.db_client()
        try:
            session.add(task_record)
            await session.commit()
            await session.refresh(task_record)
            return task_record
        finally:
            await session.close()

    async def update_task_status(self, execution_id: str, status: str, result: dict = None):
        """Update task status and result"""
        session = self.db_client()
        try:
            task_record = await session.get(CeleryTaskExecution, execution_id)
            if not task_record:
                return None
            
            task_record.status = status
            if result:
                task_record.result = result

            if status in ["SUCCESS", "FAILURE"]:
                task_record.completed_at = datetime.utcnow()
            
            task_record.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(task_record)
            return task_record
        finally:
            await session.close()

    async def get_existing_task(self, task_name: str, 
                                celery_task_id: str,
                                task_args: dict) -> CeleryTaskExecution:
        """Check if task with same name and args hash exists."""

        args_hash = self.create_args_hash(task_name=task_name, task_args=task_args)

        session = self.db_client()

        try:
            stmt = select(CeleryTaskExecution).where(
                CeleryTaskExecution.task_name == task_name,
                CeleryTaskExecution.task_args_hash == args_hash,
                CeleryTaskExecution.celery_task_id == celery_task_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            await session.close()
    
    async def should_execute_task(self, task_name: str, task_args: dict , celery_task_id: str, task_time_limit: int= 600) -> tuple[bool, CeleryTaskExecution]:
        """
        Check if task should be executed or return ecisting result.
        Returns a tuple (should_execute: bool, task_record: CeleryTaskExecution)
        """

        existing_task = await self.get_existing_task(
            task_name=task_name,
            celery_task_id=celery_task_id,
            task_args=task_args
        )

        if not existing_task:
            return True, None
        
        # Don't execute if task is already completed successfully
        if existing_task.status == "SUCCESS":
            return False, existing_task
        
        # Don't execute if task is still pending or running
        if existing_task.status in ["PENDING", "STARTED","RETRY"]:
            if existing_task.started_at:
                time_elapsed = (datetime.utcnow() - existing_task.started_at).total_seconds()
                time_gap = 60  # 1 minute
                if time_elapsed > (task_time_limit + time_gap):
                    return True, existing_task # Task is stuch , allow re-execution
            return False, existing_task # Task is still in progress
        
        # Re-excute if task previously failed
        return True, existing_task
    
    async def cleanup_old_tasks(self, time_retention: int = 86400) -> int:
        """
        Delete old task records older than time_retention seconds.
        Args:
            time_retention: Time in seconds to retain tasks (default: 86400 = 24 hours)
        Returns:
            Number of deleted records
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_retention)
        
        session = self.db_client()
        try:
            stmt = delete(CeleryTaskExecution).where(
                CeleryTaskExecution.created_at < cutoff_time
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
        finally:
            await session.close()