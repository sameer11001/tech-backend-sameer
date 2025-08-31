from typing import Optional
import boto3
from boto3.s3.transfer import TransferConfig
from celery.signals import (
    worker_ready, 
    setup_logging, 
    worker_process_init,
    worker_shutdown
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

mongo_client: Optional[MongoClient] = None
mongo_engine: Optional[SyncEngine] = None
message_crud: Optional[MongoCRUD] = None
chatbot_crud: Optional[MongoCRUD] = None
logs_crud: Optional[MongoCRUD] = None
s3_bucket_service: Optional[S3BucketService] = None
redis_service: Optional[RedisService] = None
chat_bot_context_service_instance: Optional[ChatbotContextService] = None


def initialize_mongo_resources():
    global mongo_client, mongo_engine, message_crud, chatbot_crud, logs_crud
    mongo_client = MongoClient(
        settings.MONGO_URI,
        uuidRepresentation="standard",
        connect=False,
    )
    mongo_engine = SyncEngine(client=mongo_client, database=settings.MONGO_DB)
    message_crud = MongoCRUD(Message, mongo_engine)
    chatbot_crud = MongoCRUD(FlowNode, mongo_engine)
    logs_crud = MongoCRUD(Logger, mongo_engine)

def initialize_s3_service():
    global s3_bucket_service
    if not s3_bucket_service:
        session = boto3.Session()
        transfer_config = TransferConfig(multipart_threshold=8 * 1024 ** 2)
        
        s3_bucket_service = S3BucketService(
            s3_client=session.client("s3"),
            bucket_name=settings.S3_BUCKET_NAME,
            transfer_config=transfer_config,
            aws_region=settings.AWS_REGION,
            aws_s3_bucket_name=settings.S3_BUCKET_NAME
        )
    return s3_bucket_service

def init_redis_service():
    global redis_service
    if redis_service is None:
        redis_service = RedisService(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            default_ttl=86400,
        )

def get_redis_service() -> RedisService:
    if redis_service is None:
        raise RuntimeError("Redis service not initialized")
    return redis_service

def get_message_crud():
    if message_crud is None:
        raise RuntimeError("Message CRUD not initialized - worker may not be ready")
    return message_crud

def get_chatbot_crud():
    if chatbot_crud is None:
        raise RuntimeError("Chatbot CRUD not initialized - worker may not be ready")
    return chatbot_crud

def get_logs_crud():
    if logs_crud is None:
        raise RuntimeError("Logs CRUD not initialized - worker may not be ready")
    return logs_crud

def get_s3_bucket_service():
    if s3_bucket_service is None:
        raise RuntimeError("S3 Bucket Service not initialized - worker may not be ready")
    return s3_bucket_service

def get_chatbot_context_service() -> ChatbotContextService:
    if chat_bot_context_service_instance is None:
        raise RuntimeError("ChatbotContextService not initialized")
    return chat_bot_context_service_instance

@worker_process_init.connect
def init_worker_process(**kwargs):
    task_log.info("Initializing worker process resources...")
    global chat_bot_context_service_instance
    try:
        initialize_mongo_resources()
        initialize_s3_service()
        init_redis_service()
        chat_bot_context_service_instance = ChatbotContextService(redis_client=get_redis_service())
        task_log.info("Worker process resources initialized successfully")
    except Exception as e:
        task_log.error(f"Failed to initialize worker resources: {e}")
        raise

@worker_shutdown.connect
def shutdown_worker(**_kwargs):
    task_log.info("Shutting down worker resources...")
    try:
        if mongo_client:
            mongo_client.close()
            task_log.info("MongoDB connection closed")
    except Exception as e:
        task_log.warning("Error closing MongoDB connection", error=str(e))
        
    try:
        if redis_service:
            redis_service._client.connection_pool.disconnect()
    except Exception as e:
        task_log.warning("Error disconnecting from Redis", error=str(e))
    
    try:
        psql_engine.dispose()
        task_log.info("PostgreSQL connection closed")
    except Exception as e:
        task_log.warning("Error disposing PostgreSQL engine", error=str(e))

@setup_logging.connect
def disable_celery_logging(**kwargs):
    pass

@worker_ready.connect
def worker_ready_handler(**kwargs):
    task_log.info("Message worker is ready")
