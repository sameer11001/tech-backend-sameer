from typing import List, Type
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB:
    def __init__(self, db_url:str,db_name:str) -> None:
        self.url = db_url
        self.db_name = db_name
        self.client = AsyncIOMotorClient(
            self.url, 
            maxPoolSize=50,     
            minPoolSize=5,
            socketTimeoutMS=2000,
            connectTimeoutMS=2000,
            serverSelectionTimeoutMS=2000,
            uuidRepresentation="standard"
        )
        
        
    async def init_db(self,document_models: List[Type[Document]]):
        try:
            client = self.client
            await init_beanie(
                database=client[self.db_name],
                document_models=document_models
            )
        except Exception as e:
            raise

