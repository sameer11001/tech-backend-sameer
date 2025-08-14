from __future__ import annotations

import inspect
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

import structlog

T = TypeVar("T")
R = TypeVar("R")



_SENSITIVE_KEYS = {"password", "token", "secret", "key", "auth", "credential"}


def _sanitize_arguments(args: dict[str, Any]) -> dict[str, Any]:
    """Mask PII/secrets and truncate very long values."""
    sanitized: dict[str, Any] = {}
    for k, v in args.items():
        if k in {"self", "cls"}:
            continue
        if any(s in k.lower() for s in _SENSITIVE_KEYS):
            sanitized[k] = "*****"
        else:
            s = str(v)
            sanitized[k] = f"{s[:500]}… [truncated]" if len(s) > 500 else v
    return sanitized


def _get_logger(component: str) -> structlog.BoundLogger:
    """Short-hand to get a structlog logger bound with the component name."""
    return structlog.get_logger(component=component)



def log_app(component: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorate a sync or async function so every call logs:

    * ENTRY  – args (sanitized), start-timestamp
    * EXIT   – duration when it succeeds
    * ERROR  – duration + exception on failure
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        logger = _get_logger(component)

        async def _async(*args: Any, **kwargs: Any) -> R:         
            start = time.time()
            sig_args = inspect.signature(func).bind(*args, **kwargs).arguments
            logger.debug(
                "ENTRY",
                action=func.__name__,
                arguments=_sanitize_arguments(sig_args),
                type="START",
            )
            try:
                result = await func(*args, **kwargs)                
                logger.debug(
                    "EXIT",
                    action=func.__name__,
                    duration=f"{time.time()-start:.3f}s",
                    type="END",
                )
                return result
            except Exception as exc:
                logger.error(
                    "ERROR",
                    action=func.__name__,
                    error=str(exc),
                    exception=type(exc).__name__,
                    duration=f"{time.time()-start:.3f}s",
                    type="ERROR",
                )
                raise

        def _sync(*args: Any, **kwargs: Any) -> R:                
            start = time.time()
            sig_args = inspect.signature(func).bind(*args, **kwargs).arguments
            logger.info(
                "ENTRY",
                action=func.__name__,
                arguments=_sanitize_arguments(sig_args),
                type="START",
            )
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "EXIT",
                    action=func.__name__,
                    duration=f"{time.time()-start:.3f}s",
                    type="END",
                )
                return result
            except Exception as exc:
                logger.error(
                    "ERROR",
                    action=func.__name__,
                    error=str(exc),
                    exception=type(exc).__name__,
                    duration=f"{time.time()-start:.3f}s",
                    type="ERROR",
                )
                raise

        return cast(Callable[..., R], _async if inspect.iscoroutinefunction(func) else _sync)

    return decorator


def log_class_methods(component: str) -> Callable[[T], T]:
    """
    Decorate *all* user-defined methods of a class with `@log_app(component)`.
    """
    def decorator(cls: T) -> T:
        for name, attr in cls.__dict__.items():
            if inspect.isfunction(attr):                           # skip class attrs, properties, etc.
                setattr(cls, name, log_app(component)(attr))
        return cls
    return decorator