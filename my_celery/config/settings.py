from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_PROFILE : str
    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET_NAME: str = Field(..., env="aws_s3_bucket_name")
    
    FRONTEND_URL: str
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_PUBLIC_KEY_PATH: str
    JWT_PRIVATE_KEY_PATH: str
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    CACHE_URL: str
    REDIS_TTL: int

    # Rate Limit
    RATE_LIMIT: int
    WINDOW_SIZE: int

    # WhatsApp API
    WHATSAPP_API_VERSION: str
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
    
    SESSION_SECRET_KEY: str


    # Postgres DB
    POSTGRES_DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_DATABASE_URL_CELERY: str

    # Mongo DB
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_DB: str
    MONGO_URI: str
    
    # RabbitMQ
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_VHOST: str
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_URI: str
    
    CORS_ORIGIN_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings: Settings = Settings()