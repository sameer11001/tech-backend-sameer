from typing import Optional
from fastapi import Request
import httpx

from app.core.services.HTTPClient import EnhancedHTTPClient

class HTTPService:
    
    def __init__(self, enhanced_client: EnhancedHTTPClient):
        self.client = enhanced_client

    async def get_with_context(
        self, 
        url: str, 
        request: Optional[Request] = None, 
        user_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        async with self.client.request_context(request=request, user_id=user_id):
            return await self.client.get(url, **kwargs)

    async def post_with_context(
        self, 
        url: str, 
        request: Optional[Request] = None, 
        user_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        async with self.client.request_context(request=request, user_id=user_id):
            return await self.client.post(url, **kwargs)

    async def put_with_context(
        self, 
        url: str, 
        request: Optional[Request] = None, 
        user_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        async with self.client.request_context(request=request, user_id=user_id):
            return await self.client.put(url, **kwargs)

    async def delete_with_context(
        self, 
        url: str, 
        request: Optional[Request] = None, 
        user_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        async with self.client.request_context(request=request, user_id=user_id):
            return await self.client.delete(url, **kwargs)