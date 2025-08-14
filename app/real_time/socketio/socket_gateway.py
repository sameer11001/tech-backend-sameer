from asyncio.log import logger
from datetime import datetime
import json
from typing import Any, Dict, Optional, Set
from socketio import AsyncServer

from app.core.config.logger import get_logger
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException
from app.core.security.JwtUtility import JwtTokenUtils
from app.core.storage.redis import AsyncRedisService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService

logger = get_logger("SocketMessageGateway")

class SocketMessageGateway:
    def __init__(
        self, 
        sio: AsyncServer,
        redis: AsyncRedisService,
        business_profile_service: BusinessProfileService
        ) -> None:
        self.sio = sio
        self.redis = redis
        self.business_profile_service = business_profile_service

        self.user_to_business_profile: Dict[str, str] = {}
        self.business_profile_users: Dict[str, Set[str]] = {} 
        
        self.sid_to_conversations: Dict[str, Set[str]] = {}  
        self.conversation_users: Dict[str, Set[str]] = {}   
        
        self.sio.on('connect', handler=self._on_connect)
        self.sio.on('disconnect', handler=self._on_disconnect)
        self.sio.on('join_business_group', handler=self._on_join_business_group)
        self.sio.on('leave_business_group', handler=self._on_leave_business_group)
        self.sio.on('join_conversation', handler=self._on_join_conversation)
        self.sio.on('leave_conversation', handler=self._on_leave_conversation)
        self.sio.on('mark_as_read', handler=self._on_mark_as_read)

    async def _on_connect(self, sid: str, environ: dict,auth: dict) -> None:
        try:
            token = auth.get("token", None)  
            logger.info(f"Socket connected: {sid} with token: {token}")       
            if not token:
                logger.warning("No JWT provided – disconnecting.")
                return await self.sio.disconnect(sid)
            try:
                logger.info(f"Verifying JWT: {token}")
                claims = JwtTokenUtils.verify_token(token)
            except TokenValidityException:
                await self.sio.emit(
                    "token_expired",
                    {"message": "Token expired, please login again."},
                    room=sid
                )
                await self.sio.disconnect(sid)
                return

            user_id: str = claims["userId"]
            business_profile_id: str = claims["business_profile_id"]
            logger.info(f"User {user_id} connected with business profile {business_profile_id}")
            
            old_user_id_key = RedisHelper.redis_socket_user_id_session_key(user_id)
            old_sid: Optional[str] = None

            if await self.redis.exists(old_user_id_key):
                old_sid = await self.redis.get(old_user_id_key)

                if await self._sid_is_active(old_sid):
                    logger.info(f"Kicking previous socket {old_sid} for user {user_id}")
                    try:
                        await self.sio.disconnect(old_sid)
                    except KeyError:
                        logger.warning("Previous sid vanished while kicking.")
                else:
                    await self.redis.delete(RedisHelper.redis_socket_user_session_key(old_sid))
                    await self.redis.delete(old_user_id_key)

            await self.sio.save_session(sid, claims)
            logger.info(f"User {user_id} connected with session {sid}")

            await self.redis.set(
                RedisHelper.redis_socket_user_session_key(sid),
                {
                    "userId": user_id,
                    "business_profile_id": business_profile_id,
                    "connected_at": datetime.now().isoformat(),
                },
                ttl=3600, 
            )
            
            await self.redis.set(old_user_id_key, sid, ttl=3600)
            
            logger.info(f"User {user_id} connected with session and set redis {sid}")

            await self.sio.emit("session", {"session": sid}, room=sid)
            
            logger.info(f"Client {sid} connected")
        except Exception:
            logger.exception("Exception in _on_connect. Unhandled error in _on_connect — disconnecting.")
            await self.sio.disconnect(sid)

    async def _on_disconnect(self, sid: str):
        try:
            if not await self._sid_is_active(sid):
                logger.info(f"Skip disconnect: sid {sid} is not active")
                return
            
            session = await self._get_session_data(sid)
            user_id = session.get("userId") if session else None
            
            if sid in self.sid_to_conversations:
                for conversation_id in self.sid_to_conversations[sid].copy():
                    await self._leave_conversation_internal(sid, conversation_id)            
            
            if sid in self.user_to_business_profile:
                phone_number_id = self.user_to_business_profile[sid]
                await self._on_leave_business_group(sid)
            logger.info(f"User {user_id} disconnected with session {sid}")
            
            if user_id:
                await self.redis.delete(RedisHelper.redis_socket_user_session_key(sid=sid))
                await self.redis.delete(RedisHelper.redis_socket_user_id_session_key(user_id=user_id))
            
            logger.info(f"Client {sid} disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting user: {e}")

####### conversation            
    async def _on_join_conversation(self, sid: str, data: dict):
        try:
            if not await self._sid_is_active(sid):
                logger.warning(f"Skip leave: sid {sid} not active to join conversation")
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                await self.sio.emit('error', {'message': 'conversation_id required'}, room=sid)
                return False
                
            session = await self._get_session_data(sid)
            user_id = session.get("userId") if session else None
            business_profile_id = session.get("business_profile_id") if session else None
            
            if not user_id or not business_profile_id:
                await self.sio.emit('error', {'message': 'Invalid session'}, room=sid)
                return False
                        
            await self._join_conversation_internal(sid, conversation_id, user_id,business_profile_id)
            
        except Exception as e:
            logger.exception(f"Error joining conversation: {e}")
            await self.sio.emit('error', {'message': 'Failed to join conversation'}, room=sid)
            return False

    async def _join_conversation_internal(self, sid: str, conversation_id: str, user_id: str, business_profile_id: str):
        try:
            await self.sio.enter_room(sid=sid,room= conversation_id)
            
            self.sid_to_conversations.setdefault(sid, set()).add(conversation_id)
            self.conversation_users.setdefault(conversation_id, set()).add(sid)
            
            await self.redis.set(RedisHelper.redis_conversation_user_session_key(conversation_id, sid), {
                'user_id': user_id,
                'joined_at': datetime.now().isoformat()
            }, ttl=3600)
            
            conversation_expiration_time = None
            
            await self.redis.sadd(RedisHelper.redis_conversation_members_key(conversation_id), sid)
            redis_expiration_time = await self.redis.get(RedisHelper.redis_conversation_expired_key(conversation_id))
            is_conversation_expired = True 
            if redis_expiration_time:
                conversation_expiration_time = Helper.conversation_expiration_calculate(redis_expiration_time)
                is_conversation_expired = False
                            
            unread_key = RedisHelper.redis_business_conversation_unread_key(
                conversation_id=str(conversation_id)
            )
            unread_status = await self.redis.hgetall(unread_key)
            unread_count = int(unread_status.get('unread_count', 0)) if unread_status else 0
            
            await self.redis.hset(unread_key, mapping={'unread_count': 0, 'last_read_message_id': '0-0'})

            await self.sio.emit('conversation_joined', {
                'conversation_id': conversation_id,
                'expiration_time': conversation_expiration_time,
                'is_conversation_expired': is_conversation_expired,
                'unread_count': unread_count
                
            }, room=sid)
            
            logger.info(f"User {user_id} joined conversation: {conversation_id}")            
        except Exception as e:
            logger.error(f"Error joining conversation: {e}")  
        
    async def _on_leave_conversation(self, sid: str, data: dict):
        try:
            if not await self._sid_is_active(sid):
                logger.warning(f"Skip leave: sid {sid} not active to leave conversation")
                return
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                await self.sio.emit('error', {'message': 'conversation_id required'}, room=sid)
                return False
                
            await self._leave_conversation_internal(sid, conversation_id)
            
        except Exception as e:
            logger.exception(f"Error leaving conversation: {e}")
            await self.sio.emit('error', {'message': 'Failed to leave conversation'}, room=sid)
            return False

    async def _leave_conversation_internal(self, sid: str, conversation_id: str):
        try:
            await self.sio.leave_room(sid=sid, room=conversation_id)
    
            self.sid_to_conversations.get(sid, set()).discard(conversation_id)
            self.conversation_users.get(conversation_id, set()).discard(sid)
            if not self.sid_to_conversations[sid]:
                del self.sid_to_conversations[sid]
            if not self.conversation_users[conversation_id]:
                del self.conversation_users[conversation_id]
                
            await self.redis.delete(RedisHelper.redis_conversation_user_session_key(conversation_id, sid))
    
            key = RedisHelper.redis_conversation_members_key(conversation_id)
            await self.redis.srem(key, sid)
            if not (await self.redis.smembers(key)):
                await self.redis.delete(key)

            await self.sio.emit('conversation_left', {
                'conversation_id': conversation_id
            }, room=sid)
            
            logger.info(f"Session {sid} left conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error leaving conversation: {e}")

####### business group     
    async def _on_join_business_group(self, sid: str, data: dict):
        try:
            if not await self._sid_is_active(sid):
                logger.info(f"Skip join: sid {sid} not active to enter the business group")
                return
            session = await self._get_session_data(sid)
            user_id = session.get("userId") if session else None
            business_profile_id = session.get("business_profile_id") if session else None
            
            if not business_profile_id:
                await self.sio.emit("error", {"message": "Missing business profile ID"}, room=sid)
                return
            
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            
            await self._join_business_group_internal(sid, phone_number_id, user_id, business_profile_id)
            
        except GlobalException as e:
            logger.error(f"Error joining business group: {e}")

    async def _join_business_group_internal(self, sid: str, phone_number_id: str, user_id: str, business_profile_id: str):
        try:
            await self.sio.enter_room(sid=sid,room= phone_number_id)
            self.user_to_business_profile[sid] = phone_number_id
            self.business_profile_users.setdefault(phone_number_id, set()).add(sid)
            
            await self.redis.set(
                RedisHelper.redis_buiness_group_user_session_key(phone_number_id, sid),
                {'user_id': user_id, 'joined_at': datetime.now().isoformat()},
                ttl=3600
            )    
            
            await self.redis.sadd(RedisHelper.redis_business_members_key(phone_number_id), sid)

            await self.sio.emit('business_group_joined', {
                'phone_number_id': phone_number_id
            }, room=sid)

            logger.info(f"User {user_id} joined business group: {phone_number_id}")
            
        except Exception as e:
            logger.error(f"Error joining business group: {e}")

    async def _on_leave_business_group(self, sid: str):
        try:
            if not await self._sid_is_active(sid):
                logger.info(f"Skip leave: sid {sid} not active to leave the business group")
                return
            session = await self._get_session_data(sid)
            business_profile_id = session.get("business_profile_id") if session else None
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            
            await self.sio.leave_room(sid=sid,room= phone_number_id)
            
            if sid in self.user_to_business_profile:
                del self.user_to_business_profile[sid]
            if phone_number_id in self.business_profile_users:
                self.business_profile_users[phone_number_id].discard(sid)
                if not self.business_profile_users[phone_number_id]:
                    del self.business_profile_users[phone_number_id]
            
            await self.redis.delete(RedisHelper.redis_buiness_group_user_session_key(phone_number_id, sid))
            
            key = RedisHelper.redis_business_members_key(phone_number_id)
            await self.redis.srem(key, sid)
            if not (await self.redis.smembers(key)):
                await self.redis.delete(key)
    
            logger.info(f"Session {sid} left business group: {phone_number_id}")
            
            await self.sio.emit('business_group_left', {
                'phone_number_id': phone_number_id
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Error leaving business group: {e}")

######## messages
    async def emit_received_message(self, message: dict, phone_number_id: str, conversation_id: str = None):
        try:
            if not phone_number_id:
                logger.warning("No phone number found in message")
                return
            
            if not conversation_id:
                logger.warning("No conversation_id found in message, cannot update conversation-specific data.")
                return
            
            message_for_stream = {
                "wa_message_id": str(message.get("message_id")),
                "created_at": message.get("timestamp"),
                "message_type": message.get("type"),
                "content": json.dumps(message.get("content")), 
                "context": json.dumps(message.get("context")) if message.get("context") else "",
                "is_from_contact": "true",  
                "message_status": "received", 
                "conversation_id": conversation_id,
            }
            
            logger.debug(f"Message for stream: {message_for_stream}")
            
            redis_stream_message_id = await self.redis.xadd(RedisHelper.redis_conversation_messages_stream_key(conversation_id), message_for_stream)
            
            logger.debug(f"Message {message.get('message_id')} added to Redis Stream with ID: {redis_stream_message_id}")
            
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id=conversation_id)
            
            members_count = await self.redis.scard(RedisHelper.redis_conversation_members_key(conversation_id))
            
            if members_count <= 0: 
                await self.redis.hincrby(unread_key, 'unread_count', 1)
                await self.redis.hset(unread_key, mapping={'last_read_message_id': '0-0'})

            updated_unread_status = await self.redis.hgetall(unread_key)
            updated_unread_count = int(updated_unread_status.get('unread_count', 0)) if updated_unread_status else 0            

            last_message_content = Helper._get_last_message_content(message_data=message)
                        
            businees_data ={"conversation_id": str(conversation_id), "last_message_content": last_message_content, "last_message_time": f"{message.get('timestamp')}" , "unread_count": updated_unread_count}
            
            await self.sio.emit(event="message_received", data=businees_data, room=phone_number_id)
            
            if conversation_id:
                message_data = {
                    "message": {
                        "wa_message_id": message.get("message_id"),
                        "created_at": message.get("timestamp"),
                        "message_type": message.get("type"),
                        "content": message.get("content"),
                        "context": message.get("context"),
                        "is_from_contact": True,
                        "message_status": "delivered",
                        "conversation_id": conversation_id,
                        "redis_stream_id": redis_stream_message_id
                    },
                    "conversation_id": conversation_id
                }
                await self.sio.emit(event="conversation_message_received", data=message_data, room=conversation_id)
            
                logger.info(f"Message emitted to business group: {phone_number_id}, conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error emitting message: {e}")

    async def emit_message_status(self, conversation_id: str, status: str, message_id: str):
        try:
            data = {
                "conversation_id": str(conversation_id),
                "status": status,
                "message_id": str(message_id),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.sio.emit(event="whatsapp_message_status", data=data, room=str(conversation_id))
            
            logger.debug(f"Message status emitted to business group: {conversation_id}")
                        
        except Exception as e:
            logger.error(f"Error emitting message status: {e}")

    async def emit_conversation_assignment(self,user_id: str, conversation_id: str, assigned_to: str,assignment_message: dict):
        
        sid = None
        if await self.redis.exists(RedisHelper.redis_socket_user_id_session_key(user_id)): 
            sid = await self.redis.get(RedisHelper.redis_socket_user_id_session_key(user_id))

        if not sid or not await self._sid_is_active(sid):
            logger.info(f"Skip leave: sid {sid} not active to leave the business group")
            return
        
        session = await self._get_session_data(sid)
        business_profile_id = session.get("business_profile_id") if session else None
        phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)

        if not phone_number_id:
            logger.info("No phone number found in message")
            return
        try:
            businees_data ={"conversation_id": str(conversation_id)}
            
            await self.sio.emit(event="conversation_assignment_businessgroup", data=businees_data, room=phone_number_id)
    
            data = {
                "conversation_id": str(conversation_id),
                "assigned_to": str(assigned_to),
                "assignment_message": assignment_message
            }
            await self.sio.emit("conversation_assignment_chat", data, room=str(conversation_id))
    
            logger.info(f"Conversation {conversation_id} assigned to {assigned_to}")
        except Exception as e:
            logger.error(f"Error emitting conversation assignment: {e}")

    async def emit_conversation_status(self,user_id: str, conversation_id: str, status: str):
        
        sid = None
        if await self.redis.exists(RedisHelper.redis_socket_user_id_session_key(user_id)): 
            sid = await self.redis.get(RedisHelper.redis_socket_user_id_session_key(user_id))

        if not sid or not await self._sid_is_active(sid):
            logger.info(f"Skip leave: sid {sid} not active to leave the business group")
            return
        session = await self._get_session_data(sid)
        business_profile_id = session.get("business_profile_id") if session else None
        phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
        
        if phone_number_id:
            businees_data ={"conversation_id": str(conversation_id), "status": status}
            
            await self.sio.emit(event="conversation_status_business_group", data=businees_data, room=phone_number_id)
        
        if conversation_id:
            data = {
                "conversation_id": str(conversation_id),
                "status": status
            }
            await self.sio.emit("conversation_status_chat", data, room=str(conversation_id))
    
            logger.info(f"Conversation {conversation_id} status updated to {status}")
            
    async def _on_mark_as_read(self, sid: str, data: dict):
        
        conversation_id = data.get("conversation_id")
        last_read_message_id = data.get("last_read_message_id")
        
        if not conversation_id or not last_read_message_id:
            await self.sio.emit('error', {'message': 'conversation_id and last_read_message_id required'}, room=sid)
            return
    
        session = await self._get_session_data(sid)
        user_id = session.get("userId") if session else None
        business_profile_id = session.get("business_profile_id") if session else None
        
        phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
        unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id=conversation_id)
    
        await self.redis.hset(unread_key, mapping={"unread_count": 0, "last_read_message_id": last_read_message_id})
    
        data = {"conversation_id": conversation_id, "unread_count": 0, "last_read_message_id": last_read_message_id}
        
        await self.sio.emit("unread_status_updated", data=data, room=phone_number_id)
        
        logger.info(f"User {user_id} marked messages as read in conversation {conversation_id}")

    async def _get_business_profile_phone_number_id(self, business_profile_id: str):
        try:
            if await self.redis.exists(RedisHelper.redis_business_phone_number_id_key(business_profile_id)):
                return await self.redis.get(RedisHelper.redis_business_phone_number_id_key(business_profile_id))
            
            bussiness_profile = await self.business_profile_service.get(business_profile_id)
            await self.redis.set(RedisHelper.redis_business_phone_number_id_key(business_profile_id), bussiness_profile.phone_number_id, ttl=86400)
            return bussiness_profile.phone_number_id
        except GlobalException as e:
            logger.error(f"Error getting business profile: {e}")
            raise

    async def _sid_is_active(self, sid: str) -> bool:
        try:
            is_active_in_redis = await self.redis.exists(RedisHelper.redis_socket_user_session_key(sid))
            
            return bool(is_active_in_redis) 
        except Exception:
            logger.exception(f"Error checking active status for SID {sid} in Redis.")
            return False

    async def _get_session_data(self, sid: str) -> Optional[Dict]:
        try:
            redis_session_data = await self.redis.get(RedisHelper.redis_socket_user_session_key(sid))
            if redis_session_data:
                logger.debug(f"Retrieved session data from Redis for sid: {sid}")
                return redis_session_data
            
            logger.info(f"No session data found in Redis for sid: {sid}")
            
        except Exception as e:
            logger.error(f"Redis failed to retrieve session data for sid {sid}: {e}")
        
        try:
            memory_session = await self.sio.get_session(sid)
            if memory_session:
                logger.info(f"Retrieved session data from memory for sid: {sid}")
                return memory_session
            
            logger.warning(f"No session data found in memory for sid: {sid}")
            
        except Exception as e:
            logger.error(f"Failed to retrieve session data from memory for sid {sid}: {e}")
        
        return None
    


#TODO unread Messages implementation