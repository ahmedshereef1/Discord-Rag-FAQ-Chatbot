from celery_app import celery_app
from helpers.config import get_settings, Settings
import logging 
import asyncio
from time import sleep
from datetime import datetime

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True, name='tasks.mail_service.send_email_reports')
def send_email_reports(self,mail_wait_seconds: int):

    # return await _send_email_reports(self, mail_wait_seconds=mail_wait_seconds)
    return asyncio.run(_send_email_reports(self, mail_wait_seconds=mail_wait_seconds))

async def _send_email_reports(task_instance, mail_wait_seconds: int):
    
    started_at = str(datetime.now())
    task_instance.update_state(
        state='PROGRESS',
        meta={
            "started_at" : started_at,
        }
    )

    # ==== Start ===== send reports
    for ix in range(15):
        logging.info(f"Send email to user {ix}")
        await asyncio.sleep(3)
    # ==== End ===== send reports

    return {
        "no_emails_sent": 15,
        "ended_at": str(datetime.now()),
    }
