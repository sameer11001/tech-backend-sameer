from celery import Celery
from my_celery.config import celery_config
from my_celery.config.celery_config import CELERY_TASK
from my_celery.config.settings import settings

celery_app : Celery = Celery(
    "worker",
    broker=settings.RABBITMQ_URI,
    include=CELERY_TASK
)

celery_app.conf.update(
    task_serializer='msgpack',
    accept_content=['msgpack', 'json'],
    result_serializer='msgpack',
    task_default_queue="default_queue",
    task_queues=celery_config.QUEUES,
    task_default_exchange="direct",
    task_routes=celery_config.TASK_ROUTES,
    task_create_missing_queues=True,    
    task_reject_on_worker_lost=True,
    task_ignore_result=True,
    task_acks_late=True,
    task_acks_on_failure_or_timeout=True,
    task_always_eager=False,
    task_eager_propagates=False,
    task_store_eager_result=False,
    
    worker_concurrency=1,
    worker_disable_rate_limits=True,
    worker_max_tasks_per_child=10,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=True,
    worker_max_memory_per_child=256000,
    
    broker_connection_max_retries=10,
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    
    visibility_timeout=300,
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(CELERY_TASK)