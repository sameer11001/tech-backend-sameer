from datetime import datetime, timezone
from random import uniform
import traceback
import asyncio
from functools import wraps
from app.utils.DateTimeHelper import DateTimeHelper
from celery import Task
import structlog
from typing import Any, Callable
from celery.exceptions import MaxRetriesExceededError, Retry

RETRY_COUNTDOWN = 60  
MAX_RETRIES = 5

class BaseTask(Task):
    abstract = True
    max_retries = MAX_RETRIES
    default_retry_delay = RETRY_COUNTDOWN

    def __call__(self, *args, **kwargs):
        self.start_time = DateTimeHelper.now_utc()
        self.logger = structlog.get_logger().bind(
            task=self.name, task_id=self.request.id
        )
        self.logger.info("task_started", args=args, kwargs=kwargs)

        try:
            result = super().__call__(*args, **kwargs)

            duration = (DateTimeHelper.now_utc() - self.start_time).total_seconds()
            self.logger.info("task_completed", duration=duration)
            return result

        except Retry:
            raise
        except Exception as exc:
            duration = (DateTimeHelper.now_utc() - self.start_time).total_seconds()
            self.logger.error(
                "task_failed",
                error=str(exc),
                duration=duration,
                traceback=traceback.format_exc(),
            )
            raise

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.logger = structlog.get_logger().bind(task=self.name, task_id=task_id)
        self.logger.error(
            "task_failed",
            error=str(exc),
            args=args,
            kwargs=kwargs,
            traceback=str(einfo),
        )
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        self.logger = structlog.get_logger().bind(task=self.name, task_id=task_id)
        self.logger.warning(
            "task_retrying",
            error=str(exc),
            retries=self.request.retries,
            max_retries=self.max_retries,
            traceback=str(einfo),
        )
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        self.logger = structlog.get_logger().bind(task=self.name, task_id=task_id)
        self.logger.info("task_succeeded", result=retval)
        return super().on_success(retval, task_id, args, kwargs)

    def retry_task(self, exc=None, countdown=None, **kwargs):
        self.logger = structlog.get_logger().bind(task=self.name, task_id=self.request.id)
        try:
            if exc and "rate limit" in str(exc).lower():
                retry_countdown = self.default_retry_delay * (2 ** self.request.retries)
                retry_countdown += uniform(0, retry_countdown)  # jitter
                self.logger.info("rate_limit_backoff", retry_countdown=int(retry_countdown))
                return self.retry(exc=exc, countdown=int(retry_countdown), **kwargs)

            actual_countdown = countdown if countdown is not None else self.default_retry_delay
            return self.retry(exc=exc, countdown=actual_countdown, **kwargs)

        except MaxRetriesExceededError:
            self.logger.critical(
                "max_retries_exceeded",
                error=str(exc),
                retries=self.request.retries,
            )
            raise exc 

    def run_async(self, coro_func):
        return asyncio.run(coro_func)


def async_task(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper