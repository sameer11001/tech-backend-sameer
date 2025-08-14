from celery.signals import (
    task_failure, 
    task_retry,
    task_prerun
)
from my_celery.config.celery_config import task_log
import structlog

@task_failure.connect
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **_):
    task_log.error(
        "task_failed",
        sender=sender.name,
        task_id=task_id,
        error=str(exception),
        args=args,
        kwargs=kwargs,
        traceback=einfo.traceback if einfo else None,
    )

@task_retry.connect
def task_retry_handler(request, reason, einfo, **_kwargs):
    task_log.warning(
        "task_retrying",
        task=request.task,
        reason=reason,
        retries=request.retries,
        max_retries=request.max_retries,
        traceback=einfo.traceback if einfo else None,
    )

@task_prerun.connect
def bind_task_context(sender=None, task_id=None, task=None, **_):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(task_id=task_id, task_name=task.name)