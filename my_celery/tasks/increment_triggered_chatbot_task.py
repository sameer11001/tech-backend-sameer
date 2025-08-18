from sqlalchemy import text
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.tasks.base_task import BaseTask
from sqlalchemy.exc import NoResultFound

@celery_app.task(name="my_celery.tasks.increment_triggered_chatbot_task", bind=True, base=BaseTask)
def increment_triggered_chatbot_task(self, data):
    chatbot_id = data["chatbot_id"]
    with get_db() as session:
        stmt = text("""
            UPDATE chat_bots
            SET triggered = COALESCE(triggered, 0) + 1,
                updated_at = now()
            WHERE id = :id
            RETURNING triggered
        """)
        result = session.execute(stmt, {"id": str(chatbot_id)})
        row = result.fetchone()
        if not row:
            raise NoResultFound(f"No ChatBotMeta row with id={chatbot_id}")
        return row[0]