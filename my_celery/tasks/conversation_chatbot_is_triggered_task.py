from sqlalchemy import text
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.tasks.base_task import BaseTask
from sqlalchemy.exc import NoResultFound

@celery_app.task(name="my_celery.tasks.conversation_chatbot_is_triggered_task", bind=True, base=BaseTask)
def conversation_chatbot_is_triggered_task(self, data):
    conversation_id = data["conversation_id"]
    with get_db() as session:
        stmt = text("""
            UPDATE conversations
            SET chatbot_triggered = TRUE,
                updated_at = now()
            WHERE id = :id
            RETURNING chatbot_triggered
        """)
        result = session.execute(stmt, {"id": str(conversation_id)})
        row = result.fetchone()
        if not row:
            raise NoResultFound(f"No conversation row with id={conversation_id}")
        return row[0]