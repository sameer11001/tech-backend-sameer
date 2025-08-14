import logging, sys, orjson, structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    add_log_level,
    TimeStamper,
    ExceptionRenderer,
    JSONRenderer,
)
from structlog import make_filtering_bound_logger, BytesLoggerFactory, PrintLoggerFactory


LOG_PATTERN = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FMT    = "%Y-%m-%d %H:%M:%S"


def configure_structlog(*, debug: bool = False) -> None:

    min_level = logging.DEBUG if debug else logging.INFO

    processors = [
        merge_contextvars,
        add_log_level,
        ExceptionRenderer(),                
        TimeStamper(fmt="iso", utc=not debug),
    ]

    if debug:

        def plain_renderer(_, __, event_dict):
            msg = event_dict.pop("event")
            if event_dict:                  
                extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
                msg = f"{msg}  {extras}"
            return msg

        processors.append(plain_renderer)
        logger_factory = PrintLoggerFactory()
        stream = sys.stdout                 # text stream
        formatter = logging.Formatter(LOG_PATTERN, DATE_FMT)

    else:
        processors.append(JSONRenderer(serializer=orjson.dumps))
        logger_factory = BytesLoggerFactory()
        stream = sys.stdout.buffer         
        formatter = logging.Formatter("%(message)s")   

    structlog.configure(
        processors=processors,
        wrapper_class=make_filtering_bound_logger(min_level),
        logger_factory=logger_factory,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=min_level,
        handlers=[handler],
        force=True,          
    )