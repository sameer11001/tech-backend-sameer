from my_celery import celery_app
from my_celery.tasks.base_task import BaseTask

RETRY_COUNTDOWN = 60
MAX_RETRIES = 5

@celery_app.task(
    name="my_celery.tasks.system_logs_handler_task",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,        
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False,
)
def system_logs_handler_task(self, data):
    pass