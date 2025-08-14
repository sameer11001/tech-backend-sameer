from typing import Optional
from celery.signals import (
    worker_ready, 
    setup_logging, 
    worker_process_init,
    worker_shutdown
)
from odmantic import SyncEngine
from pymongo import MongoClient
from my_celery.config.settings import settings
from my_celery.config.celery_config import task_log
from my_celery.database.MongoCRUD import MongoCRUD
from my_celery.models.ChatBot import ChatBot
from my_celery.models.Message import Message
from my_celery.database.db_config import psql_engine

mongo_client: Optional[MongoClient] = None
mongo_engine: Optional[SyncEngine] = None
message_crud: Optional[MongoCRUD] = None
chatbot_crud: Optional[MongoCRUD] = None

def initialize_mongo_resources():
    global mongo_client, mongo_engine, message_crud, chatbot_crud
    mongo_client = MongoClient(
        settings.MONGO_URI,
        uuidRepresentation="standard",
        connect=False,
    )
    mongo_engine = SyncEngine(client=mongo_client, database=settings.MONGO_DB)
    message_crud = MongoCRUD(Message, mongo_engine)
    chatbot_crud = MongoCRUD(ChatBot, mongo_engine)

        
def get_message_crud():
    if message_crud is None:
        raise RuntimeError("Message CRUD not initialized - worker may not be ready")
    return message_crud

def get_chatbot_crud():
    if chatbot_crud is None:
        raise RuntimeError("Chatbot CRUD not initialized - worker may not be ready")
    return chatbot_crud


@worker_process_init.connect
def init_worker_process(**kwargs):
    task_log.info("Initializing worker process resources...")
    try:
        initialize_mongo_resources()
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
