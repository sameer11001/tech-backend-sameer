from datetime import datetime, timezone
from my_celery.celery_app import celery_app
from my_celery.models.Logger import Logger
from my_celery.signals.lifecycle import get_logs_crud
from my_celery.tasks.base_task import BaseTask
from my_celery.config.celery_config import task_log
from my_celery.utils.enums.LogLevel import LogLevel


RETRY_COUNTDOWN = 60
MAX_RETRIES = 1

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

    try:
        self.logger.info(f"Processing system log: {data.get('message', 'No message')[:100]}")
        
        required_fields = ['message', 'level', 'service']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            log_level = LogLevel(data['level'])
        except ValueError:
            error_msg = f"Invalid log level: {data['level']}. Valid levels: {[level.value for level in LogLevel]}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        logs_crud = get_logs_crud()
        
        timestamp = data.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid timestamp format: {timestamp}, using current time")
                timestamp = datetime.now(timezone.utc)
        elif not timestamp:
            timestamp = datetime.now(timezone.utc)
        
        log_entry_data = Logger(
            timestamp=timestamp,
            level=log_level.value,
            service=data['service'],
            message=data['message'],
            context=data.get('context', {}),
            host=data.get('host'),
            trace_id=data.get('trace_id'),
            request_id=data.get('request_id'),
            correlation_id=data.get('correlation_id'),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            env=data.get('env'),
            module=data.get('module'),
            function=data.get('function'),
            event_type=data.get('event_type'),
            event_category=data.get('event_category'),
            request_path=data.get('request_path'),
            request_method=data.get('request_method'),
            client_ip=data.get('client_ip'),
            user_agent=data.get('user_agent'),
            exception_type=data.get('exception_type'),
            stack_trace=data.get('stack_trace'),
            error_code=data.get('error_code'),
            retention_days=data.get('retention_days', 30),  
            archived=data.get('archived', False) 
        )
        
        log_entry = logs_crud.create(log_entry_data)
        
        self.logger.info(f"Successfully processed and saved log entry {log_entry.id}")
        
        return {
            'status': 'success',
            'log_id': str(log_entry.id),
            'timestamp': log_entry.timestamp.isoformat(),
            'message': f"Log entry created successfully for service: {data['service']}"
        }
        
    except ValueError as ve:
        self.logger.error(f"Validation error in system_logs_handler_task: {ve}")
        return {
            'status': 'failed',
            'error': str(ve),
            'error_type': 'validation_error'
        }
        
    except Exception as e:
        self.logger.error(f"Error in system_logs_handler_task: {e}")
        
        if self.request.retries < self.max_retries:
            retry_countdown = RETRY_COUNTDOWN * (2 ** self.request.retries)  
            self.logger.warning(f"Retrying system_logs_handler_task in {retry_countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=retry_countdown, exc=e)
        else:
            self.logger.error(f"Max retries exceeded for system_logs_handler_task: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'error_type': 'processing_error',
                'retries_exhausted': True
            }