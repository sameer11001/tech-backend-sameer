from fastapi import APIRouter, Depends, File, UploadFile 
import fastapi
from sqlalchemy import text
from sqlmodel import Session
from app.core.storage.postgres import PostgresDatabase
from app.events.pub.WhatsappMessagePublisher import WhatsappMessagePublisher
from app.core.config.container import Container
from app.core.schemas.BaseResponse import ApiResponse
import sys

from dependency_injector.wiring import Provide, inject

from app.core.services.S3Service import S3Service
from app.events.pub.test_everything import TestPublisher

router = APIRouter()

@router.get("/", response_model=ApiResponse)
async def getInfo():
    data : dict = {"Python":sys.version, "FastAPI":fastapi.__version__,"platform":sys.platform}

    return ApiResponse.success_response(message="Server is up and running", status_code=200,data= data)


@router.post("/test-create-message")
@inject
async def test_create_message(test_message:WhatsappMessagePublisher = Depends(Provide[Container.message_publisher])):
    
    await test_message.publish_many(texts="test message")

@router.post("/upload")
@inject
async def upload(
    file: UploadFile = File(...),
    s3: S3Service = Depends(Provide[Container.s3_bucket_service]),
):
    key = s3.upload_fileobj(file=file.file,file_name=file.filename)
    return {"key": key}



@router.get("/download-url")
@inject
async def get_url(
    key: str,
    s3: S3Service = Depends(Provide[Container.s3_bucket_service]),
):
    url = s3.generate_presigned_url(key)
    return {"url": url}


@router.get("/test_flow_celery")
@inject
async def test_flow_celery(
    data: str,
    publisher:TestPublisher = Depends(Provide[Container.test_publisher]),
):
    test_data = {"test_flow_data": data}
    await publisher.send_message(test_data)
    
    
@router.get("/get_users_data", response_model=ApiResponse)
async def get_users_data():
    db = PostgresDatabase(db_url="postgresql+asyncpg://postgres:password@postgres/db_name")
    stmt = text("Select * from users")
    