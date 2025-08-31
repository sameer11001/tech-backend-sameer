import logging, sys, orjson, structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import add_log_level, TimeStamper, JSONRenderer, ExceptionRenderer
from structlog.dev import ConsoleRenderer

def configure_structlog(*, debug: bool = False) -> None:
    processors = [
        merge_contextvars,
        add_log_level,
        ExceptionRenderer(),
        TimeStamper(fmt="iso", utc=True),
        ConsoleRenderer(colors=True) if debug else JSONRenderer(serializer=orjson.dumps),
    ]

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        processors=processors,
        logger_factory=(
            structlog.PrintLoggerFactory()
            if debug
            else structlog.BytesLoggerFactory()
        ),
    )

    try:
        stream = sys.stdout.buffer if not debug else sys.stdout
    except AttributeError:  
        stream = sys.stdout
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(stream)],
        force=True,
    )