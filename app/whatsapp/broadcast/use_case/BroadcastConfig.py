import asyncio
import contextlib
import re
from typing import Optional
from app.core.logs import logger
from app.core.storage.redis import AsyncRedisService
from app.whatsapp.broadcast.use_case.BroadcastScheduler import BroadcastScheduler

logger = logger.get_logger("BroadcastConfig")

class BroadcastConfig:
    def __init__(self, redis_service: AsyncRedisService, broadcast_scheduler: BroadcastScheduler) -> None:
        self.redis_service = redis_service
        self.broadcast_scheduler = broadcast_scheduler
        self._listener_task: Optional[asyncio.Task] = None

    async def start_listener(self) -> None:
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_to_broadcasts())

    async def stop_listener(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None                 

    async def _listen_to_broadcasts(self) -> None:

        redis = await self.redis_service.get_redis()
        try:
            async with redis.pubsub() as pubsub:
                await pubsub.psubscribe("__keyevent@0__:expired")
                logger.info("BroadcastConfig listener started")

                async for message in pubsub.listen():
                    if message.get("type") != "pmessage":
                        continue

                    expired_key = message["data"]
                    if isinstance(expired_key, bytes):
                        expired_key = expired_key.decode()

                    pattern = r"^broadcast:\{(.+?)\}:schedule$"
                    
                    match = re.match(pattern, expired_key)
                    if match:
                        broadcast_id = match.group(1)
                        try:
                            await self.broadcast_scheduler._handle_scheduled_broadcast(broadcast_id)
                        except Exception:
                            logger.error(f"Failed to handle broadcast {broadcast_id}")
                            
        finally:
            await redis.close()
            if hasattr(redis, "wait_closed"):
                await redis.wait_closed()
