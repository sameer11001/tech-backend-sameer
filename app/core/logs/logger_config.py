from datetime import datetime
import uuid
from sqlmodel import SQLModel
import logging, sys, orjson, structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    add_log_level,
    TimeStamper,
    ExceptionRenderer,
    CallsiteParameterAdder,
)
from structlog import make_filtering_bound_logger, PrintLoggerFactory
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='SYSTEM')
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='GLOBAL')
socket_session_ctx: ContextVar[str] = ContextVar('socket_session', default='')
user_id_ctx: ContextVar[str] = ContextVar('user_id', default='')

def add_socket_context(_, __, event_dict):
    socket_session = socket_session_ctx.get('')
    user_id = user_id_ctx.get('')
    
    if socket_session:
        event_dict['socket_session'] = socket_session
    if user_id:
        event_dict['user_id'] = user_id
    
    return event_dict

def filter_sensitive_data(_, __, event_dict):
    sensitive_keys = {'password', 'token', 'secret', 'key', 'auth'}
    
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = '***PROTECTED***'
    
    return event_dict

_structlog_configured = False

def configure_structlog(*, debug: bool = False, service_name: str = "whatsapp-service") -> None:
    global _structlog_configured
    
    if _structlog_configured:
        return
    
    min_level = logging.DEBUG if debug else logging.INFO

    processors = [
        merge_contextvars,              
        add_socket_context,             
        filter_sensitive_data,          
        add_log_level,                  
        ExceptionRenderer(),            
        TimeStamper(fmt="iso", utc=True),
    ]

    def add_service_metadata(_, __, event_dict):
        event_dict['service'] = service_name
        event_dict['version'] = '1.0.0'  
        return event_dict
    
    processors.append(add_service_metadata)

    if debug:
        processors.append(CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.LINENO]
        ))
        
        def colorized_dev_renderer(_, __, event_dict):
            msg = event_dict.pop("event")
            level = event_dict.pop("level", "INFO")
            timestamp = event_dict.pop("timestamp", "")
            
            colors = {
                "DEBUG": "\033[36m",    
                "INFO": "\033[32m",     
                "WARNING": "\033[33m",  
                "ERROR": "\033[31m",    
                "CRITICAL": "\033[35m", 
            }
            reset = "\033[0m"
            
            colored_level = f"{colors.get(level, '')}{level}{reset}"
            
            if event_dict:
                extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
                return f"{timestamp} [{colored_level}] {msg} | {extras}"
            else:
                return f"{timestamp} [{colored_level}] {msg}"

        processors.append(colorized_dev_renderer)
        logger_factory = PrintLoggerFactory()
        stream = sys.stdout
        formatter = logging.Formatter("%(message)s")
        
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
        logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
        logging.getLogger("motor").setLevel(logging.WARNING)
        logging.getLogger("message").setLevel(logging.WARNING)
        logging.getLogger('aio_pika').setLevel(logging.WARNING)
        logging.getLogger('aiormq').setLevel(logging.WARNING)
        logging.getLogger('pamqp').setLevel(logging.WARNING)
        logging.getLogger('amqp').setLevel(logging.WARNING)
        
    else:
        def custom_json_renderer(_, __, event_dict):
            if 'event' in event_dict:
                event_dict['message'] = event_dict.pop('event')
            
            def default_serializer(obj):
                from sqlmodel import SQLModel
                if isinstance(obj, SQLModel):
                    return obj.model_dump()
                if isinstance(obj, (uuid.UUID, type)):
                    return str(obj)
                return str(obj)  

            return orjson.dumps(event_dict, default=default_serializer).decode("utf-8")

        processors.append(custom_json_renderer)
        logger_factory = PrintLoggerFactory()  
        stream = sys.stdout
        formatter = logging.Formatter("%(message)s")
        
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("socketio").setLevel(logging.ERROR)
        logging.getLogger("engineio").setLevel(logging.ERROR)
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
        logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
        logging.getLogger("motor").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("message").setLevel(logging.WARNING)
        logging.getLogger('aio_pika').setLevel(logging.WARNING)
        logging.getLogger('aiormq').setLevel(logging.WARNING)
        logging.getLogger('pamqp').setLevel(logging.WARNING)
        logging.getLogger('amqp').setLevel(logging.WARNING)

    structlog.configure(
        processors=processors,
        wrapper_class=make_filtering_bound_logger(min_level),
        logger_factory=logger_factory,
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(min_level)
    
    _structlog_configured = True