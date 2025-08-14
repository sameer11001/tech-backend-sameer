from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from my_celery.signals.lifecycle import get_message_crud
from my_celery.tasks.base_task import BaseTask
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.models.Message import Message

RETRY_COUNTDOWN = 60
MAX_RETRIES = 5

@celery_app.task(
    name="my_celery.tasks.status_whatsapp_message",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,        
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False,
)
def status_whatsapp_message(self, data):
    try:
        message_crud = get_message_crud()
    except RuntimeError as e:
        self.logger.error("get_message_crud_failed", error=str(e))
        raise self.retry(exc=e)

    wa_id = data["wa_message_id"]
    new_status = data["status"]

    with get_db() as db:
        try:
            result = db.execute(
                text("""
                    UPDATE messages
                    SET message_status = :new_status
                    WHERE whatsapp_message_id = :wa_id
                    RETURNING id
                """),
                {"new_status": new_status, "wa_id": wa_id},
            )
            updated_row = result.fetchone()
        except OperationalError as oe:
            self.logger.warning("db_update_failed", error=str(oe))
            raise self.retry(exc=oe)

        if not updated_row:
            self.logger.warning("no_message_found_for_wa_id", wa_id=wa_id)
            return {"updated": False}

        message_id = updated_row[0]
        self.logger.info("message_updated", message_id=message_id)

    try:
        mongo_msg : Message = message_crud.get_by_id(message_id)
        if not mongo_msg:
            self.logger.warning("no_mongo_document_found", message_id=message_id)
            return {"updated": False}

        mongo_msg.message_status = new_status
        mongo_msg.wa_message_id = wa_id
        message_crud.update(id=message_id, data=mongo_msg)

        self.logger.info("mongo_doc_updated", message_id=message_id)
    except Exception as e:
        self.logger.error("mongo_update_failed", error=str(e))
        return self.retry(exc=e)