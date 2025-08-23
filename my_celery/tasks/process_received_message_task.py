from my_celery.celery_app import celery_app
from my_celery.tasks.base_task import BaseTask

MAX_RETRIES = 5
RETRY_COUNTDOWN = 60

@celery_app.task(
    name="my_celery.tasks.process_received_message_task",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False
)
def process_received_message(self, data):
    pass