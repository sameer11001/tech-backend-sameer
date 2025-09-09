# my_celery/signals/lifecycle.py
import os
import threading
import time
from typing import Optional
import boto3
from boto3.s3.transfer import TransferConfig
from celery.signals import (
    worker_ready, 
    setup_logging, 
    worker_process_init,
    worker_shutdown,
    task_prerun
)
from odmantic import SyncEngine
from pymongo import MongoClient
from my_celery.config.S3BucketService import S3BucketService
from my_celery.config.settings import settings
from my_celery.config.celery_config import task_log
from my_celery.database.MongoCRUD import MongoCRUD
from my_celery.database.redis import RedisService
from my_celery.models.Logger import Logger
from my_celery.models.ChatBot import FlowNode
from my_celery.models.Message import Message
from my_celery.database.db_config import psql_engine
from my_celery.services.ChatbotContextService import ChatbotContextService


class WorkerContext:
    """Per-worker context that holds all service instances"""
    
    def __init__(self):
        self.worker_pid = os.getpid()
        self.worker_id = f"worker-{self.worker_pid}"
        self._lock = threading.RLock()
        self._initialized = False
        self._initialization_failed = False
        self._initialization_error = None
        
        # Service instances
        self.mongo_client: Optional[MongoClient] = None
        self.mongo_engine: Optional[SyncEngine] = None
        self.message_crud: Optional[MongoCRUD] = None
        self.chatbot_crud: Optional[MongoCRUD] = None
        self.logs_crud: Optional[MongoCRUD] = None
        self.s3_bucket_service: Optional[S3BucketService] = None
        self.redis_service: Optional[RedisService] = None
        self.chatbot_context_service: Optional[ChatbotContextService] = None
    
    def ensure_initialized(self, max_retries=3, retry_delay=2):
        """Ensure worker is initialized, with retries if needed"""
        if self._initialized:
            return True
            
        if self._initialization_failed:
            # Try to recover from previous failure
            self._initialization_failed = False
            self._initialization_error = None
        
        with self._lock:
            if self._initialized:
                return True
                
            retry_count = 0
            while retry_count < max_retries:
                try:
                    task_log.info(f"Initializing services for worker {self.worker_id} (attempt {retry_count + 1}/{max_retries})")
                    
                    self._init_mongo_resources()
                    self._init_redis_service() 
                    self._init_s3_service()
                    self._init_chatbot_context_service()
                    
                    self._initialized = True
                    task_log.info(f"Worker {self.worker_id} initialized successfully")
                    return True
                    
                except Exception as e:
                    retry_count += 1
                    error_msg = f"Failed to initialize worker {self.worker_id} (attempt {retry_count}/{max_retries}): {e}"
                    
                    if retry_count < max_retries:
                        task_log.warning(f"{error_msg} - retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        task_log.error(f"{error_msg} - max retries exceeded")
                        self._initialization_failed = True
                        self._initialization_error = str(e)
                        return False
            
            return False
    
    def _init_mongo_resources(self):
        """Initialize MongoDB resources"""
        if self.mongo_client is None:
            self.mongo_client = MongoClient(
                settings.MONGO_URI,
                uuidRepresentation="standard",
                connect=False,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=1,
                appName=f"celery-worker-{self.worker_pid}"
            )
            
            # Test connection
            self.mongo_client.admin.command('ping')
            
            self.mongo_engine = SyncEngine(client=self.mongo_client, database=settings.MONGO_DB)
            self.message_crud = MongoCRUD(Message, self.mongo_engine)
            self.chatbot_crud = MongoCRUD(FlowNode, self.mongo_engine)
            self.logs_crud = MongoCRUD(Logger, self.mongo_engine)
    
    def _init_redis_service(self):
        """Initialize Redis service"""
        if self.redis_service is None:
            self.redis_service = RedisService(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                default_ttl=86400,
            )
            # Test connection
            self.redis_service._client.ping()
    
    def _init_s3_service(self):
        if self.s3_bucket_service is None:
            try:
                import tempfile
                import os
                
                temp_dir = tempfile.gettempdir() 
                
                session = boto3.Session()
                
                transfer_config = TransferConfig(
                    multipart_threshold=8 * 1024 ** 2,
                    use_threads=False,  
                    max_concurrency=1   
                )
                
                os.environ['TMPDIR'] = temp_dir
                os.environ['TMP'] = temp_dir
                os.environ['TEMP'] = temp_dir
                
                self.s3_bucket_service = S3BucketService(
                    s3_client=session.client("s3"),
                    bucket_name=settings.S3_BUCKET_NAME,
                    transfer_config=transfer_config,
                    aws_region=settings.AWS_REGION,
                    aws_s3_bucket_name=settings.S3_BUCKET_NAME
                )
                
                task_log.info(f"S3 service initialized with temp dir: {temp_dir}")

            except Exception as e:
                task_log.error(f"S3 service initialization failed: {e}")
                self.s3_bucket_service = None
                
    def _init_chatbot_context_service(self):
        """Initialize ChatbotContextService"""
        if self.chatbot_context_service is None:
            if not self.redis_service:
                raise RuntimeError("Redis service must be initialized first")
            self.chatbot_context_service = ChatbotContextService(redis_client=self.redis_service)
    
    def cleanup_services(self):
        """Clean up all services"""
        task_log.info(f"Cleaning up services for worker {self.worker_id}...")
        
        if self.mongo_client:
            try:
                self.mongo_client.close()
                task_log.info(f"MongoDB connection closed for worker {self.worker_id}")
            except Exception as e:
                task_log.warning(f"Error closing MongoDB for worker {self.worker_id}: {e}")
        
        if self.redis_service:
            try:
                self.redis_service._client.connection_pool.disconnect()
                task_log.info(f"Redis connection closed for worker {self.worker_id}")
            except Exception as e:
                task_log.warning(f"Error closing Redis for worker {self.worker_id}: {e}")
        
        try:
            psql_engine.dispose()
            task_log.info(f"PostgreSQL connection closed for worker {self.worker_id}")
        except Exception as e:
            task_log.warning(f"Error disposing PostgreSQL for worker {self.worker_id}: {e}")
        
        # Reset state
        self._initialized = False
        self._initialization_failed = False
        self._initialization_error = None
    
    def get_redis_service(self) -> RedisService:
        """Get Redis service, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.redis_service:
            raise RuntimeError(f"Redis service not available for worker {self.worker_id}")
        return self.redis_service
    
    def get_chatbot_context_service(self) -> ChatbotContextService:
        """Get ChatbotContextService, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.chatbot_context_service:
            raise RuntimeError(f"ChatbotContextService not available for worker {self.worker_id}")
        return self.chatbot_context_service
    
    def get_message_crud(self):
        """Get message CRUD, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.message_crud:
            raise RuntimeError(f"Message CRUD not available for worker {self.worker_id}")
        return self.message_crud
    
    def get_chatbot_crud(self):
        """Get chatbot CRUD, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.chatbot_crud:
            raise RuntimeError(f"Chatbot CRUD not available for worker {self.worker_id}")
        return self.chatbot_crud
    
    def get_logs_crud(self):
        """Get logs CRUD, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.logs_crud:
            raise RuntimeError(f"Logs CRUD not available for worker {self.worker_id}")
        return self.logs_crud
    
    def get_s3_bucket_service(self):
        """Get S3 service, ensuring initialization"""
        if not self.ensure_initialized():
            raise RuntimeError(f"Failed to initialize worker {self.worker_id}: {self._initialization_error}")
        if not self.s3_bucket_service:
            raise RuntimeError(f"S3 Bucket Service not available for worker {self.worker_id}")
        return self.s3_bucket_service


# Global worker context - one per worker process
_worker_context: Optional[WorkerContext] = None
_context_lock = threading.RLock()


def get_worker_context() -> WorkerContext:
    """Get the worker context for the current process"""
    global _worker_context
    if _worker_context is None:
        with _context_lock:
            if _worker_context is None:
                _worker_context = WorkerContext()
    return _worker_context


# Public API functions
def get_redis_service() -> RedisService:
    """Get Redis service for current worker"""
    return get_worker_context().get_redis_service()


def get_chatbot_context_service() -> ChatbotContextService:
    """Get ChatbotContextService for current worker"""
    return get_worker_context().get_chatbot_context_service()


def get_message_crud():
    """Get message CRUD for current worker"""
    return get_worker_context().get_message_crud()


def get_chatbot_crud():
    """Get chatbot CRUD for current worker"""
    return get_worker_context().get_chatbot_crud()


def get_logs_crud():
    """Get logs CRUD for current worker"""
    return get_worker_context().get_logs_crud()


def get_s3_bucket_service():
    """Get S3 service for current worker"""
    return get_worker_context().get_s3_bucket_service()


# Celery signal handlers
@worker_process_init.connect
def init_worker_process(**kwargs):
    """Initialize worker process - this runs once per worker process startup"""
    worker_context = get_worker_context()
    task_log.info(f"Worker process init signal received for {worker_context.worker_id}")
    
    # Pre-initialize services during worker startup
    if worker_context.ensure_initialized():
        task_log.info(f"Worker {worker_context.worker_id} pre-initialization completed successfully")
    else:
        task_log.error(f"Worker {worker_context.worker_id} pre-initialization failed - services will be initialized on-demand")


@task_prerun.connect
def ensure_worker_ready_before_task(sender=None, task_id=None, task=None, args=None, kwargs=None, **_):
    """Ensure worker is ready before any task execution"""
    worker_context = get_worker_context()
    
    if not worker_context._initialized:
        task_log.info(f"Worker {worker_context.worker_id} not initialized, initializing before task {task.name}")
        if not worker_context.ensure_initialized():
            task_log.error(f"Failed to initialize worker {worker_context.worker_id} before task execution")
            raise RuntimeError(f"Worker {worker_context.worker_id} initialization failed")


@worker_ready.connect  
def worker_ready_handler(**kwargs):
    """Worker ready handler"""
    worker_context = get_worker_context()
    task_log.info(f"Worker {worker_context.worker_id} is ready and accepting tasks")


@worker_shutdown.connect
def shutdown_worker(**kwargs):
    """Shutdown worker and cleanup its context"""
    worker_context = get_worker_context()
    task_log.info(f"Shutting down worker {worker_context.worker_id}")
    
    try:
        worker_context.cleanup_services()
        task_log.info(f"Worker {worker_context.worker_id} shutdown completed")
    except Exception as e:
        task_log.error(f"Error during worker {worker_context.worker_id} shutdown: {e}")


@setup_logging.connect
def disable_celery_logging(**kwargs):
    """Setup logging configuration"""
    pass