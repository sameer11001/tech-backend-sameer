import asyncio
from datetime import datetime
import os
from typing import Dict, Optional, Set
from socketio import AsyncServer

from app.core.logs.logger import get_logger
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException
from app.core.security.JwtUtility import JwtTokenUtils
from app.core.storage.redis import AsyncRedisService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService

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
        self.logger = get_logger("SocketMessageGateway")
        self.worker_id = os.getpid() if hasattr(os, 'getpid') else 'unknown'
        
        self._register_handlers()

    def _register_handlers(self):
        self.sio.on('connect', handler=self._on_connect)
        self.sio.on('disconnect', handler=self._on_disconnect)
        self.sio.on('join_business_group', handler=self._on_join_business_group)
        self.sio.on('leave_business_group', handler=self._on_leave_business_group)
        self.sio.on('join_conversation', handler=self._on_join_conversation)
        self.sio.on('leave_conversation', handler=self._on_leave_conversation)
        self.sio.on('mark_as_read', handler=self._on_mark_as_read)

    def _get_logger(self, sid: str, user_id: str = "", **kwargs):
        return self.logger.with_context(
            socket_session=sid,
            user_id=user_id,
            worker_id=self.worker_id,
            **kwargs
        )

    async def _add_user_to_business_group(self, sid: str, phone_number_id: str, user_id: str):
        user_session_data = {
            "user_id": user_id,
            "joined_at": datetime.now().isoformat(),
            "worker_id": self.worker_id
        }
        
        # Replace pipeline with direct calls
        await self.redis.set(
            RedisHelper.redis_buiness_group_user_session_key(phone_number_id, sid),
            user_session_data,
            ttl=3600
        )
        await self.redis.sadd(RedisHelper.redis_business_members_key(phone_number_id), sid)
        await self.redis.expire(RedisHelper.redis_business_members_key(phone_number_id), 3600)

    async def _remove_user_from_business_group(self, sid: str, phone_number_id: str):
        # Replace pipeline with direct calls
        await self.redis.delete(RedisHelper.redis_buiness_group_user_session_key(phone_number_id, sid))
        await self.redis.srem(RedisHelper.redis_business_members_key(phone_number_id), sid)

    async def _get_user_business_group(self, sid: str) -> Optional[str]:
        session = await self._get_session_data_redis(sid)
        if session:
            business_profile_id = session.get("business_profile_id")
            if business_profile_id:
                return await self._get_business_profile_phone_number_id(business_profile_id)
        return None

    async def _add_user_to_conversation(self, sid: str, conversation_id: str, user_id: str):
        conversation_session_data = {
            "user_id": user_id,
            "joined_at": datetime.now().isoformat(),
            "worker_id": self.worker_id
        }
        
        # Replace pipeline with direct calls
        await self.redis.set(
            RedisHelper.redis_conversation_user_session_key(conversation_id, sid),
            conversation_session_data,
            ttl=3600
        )
        await self.redis.sadd(RedisHelper.redis_conversation_members_key(conversation_id), sid)
        await self.redis.expire(RedisHelper.redis_conversation_members_key(conversation_id), 3600)

    async def _remove_user_from_conversation(self, sid: str, conversation_id: str):
        await self.redis.delete(RedisHelper.redis_conversation_user_session_key(conversation_id, sid))
        await self.redis.srem(RedisHelper.redis_conversation_members_key(conversation_id), sid)

    async def _get_user_conversations(self, sid: str) -> Set[str]:
        conversations = set()
        try:
            conversation_keys = await self.redis.keys("chat:conversation:*:members")
            
            for key in conversation_keys:
                parts = key.split(':')
                if len(parts) >= 3:
                    conversation_id = parts[2].strip('{}')
                    is_member = await self.redis.sismember(key, sid)
                    if is_member:
                        conversations.add(conversation_id)
                        
        except Exception as e:
            self.logger.error(f"Error getting user conversations for {sid}: {e}")
            
        return conversations

    async def _cleanup_user_state(self, sid: str):
        try:
            conversations = await self._get_user_conversations(sid)
            
            session = await self._get_session_data_redis(sid)
            if session:
                business_profile_id = session.get("business_profile_id")
                if business_profile_id:
                    phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
                    if phone_number_id:
                        await self._remove_user_from_business_group(sid, phone_number_id)
            
            for conversation_id in conversations:
                await self._remove_user_from_conversation(sid, conversation_id)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up user state for {sid}: {e}")
            
    async def _save_session_data_redis(self, sid: str, user_id: str, business_profile_id: str, claims: dict, logger):
        try:
            session_data = {
                "userId": user_id,
                "business_profile_id": business_profile_id,
                "connected_at": datetime.now().isoformat(),
                "worker_id": self.worker_id,
            }
            
            # Replace pipeline with direct calls
            await self.redis.set(RedisHelper.redis_socket_user_session_key(sid), session_data, ttl=3600)
            await self.redis.set(RedisHelper.redis_socket_user_id_session_key(user_id), sid, ttl=3600)
            
            await self.sio.save_session(sid, claims)
            await logger.adebug("Session data saved to Redis and local session")
            
        except Exception as e:
            await logger.aerror("Error saving session data", error=str(e))
            raise

    async def _get_session_data_redis(self, sid: str) -> Optional[Dict]:
        try:
            session_data = await self.redis.get(RedisHelper.redis_socket_user_session_key(sid))
            if session_data:
                return session_data
            
            try:
                return await self.sio.get_session(sid)
            except KeyError:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve session data for sid {sid}: {e}")
            return None

    async def _cleanup_session_data(self, sid: str, user_id: str):
        # Replace pipeline with direct calls
        await self.redis.delete(RedisHelper.redis_socket_user_session_key(sid))
        await self.redis.delete(RedisHelper.redis_socket_user_id_session_key(user_id))

    async def _handle_existing_session_cross_worker(self, sid: str, user_id: str, logger):
        old_user_id_key = RedisHelper.redis_socket_user_id_session_key(user_id)
        
        if await self.redis.exists(old_user_id_key):
            old_sid: Optional[str] = await self.redis.get(old_user_id_key)
            
            if old_sid and old_sid != sid:
                await logger.ainfo("Found existing session on potentially different worker", old_session=old_sid)
                
                try:
                    await self.sio.emit("force_disconnect", {"reason": "New session started"}, room=old_sid)
                    await asyncio.sleep(0.1)
                    
                    await self._cleanup_session_data(old_sid, user_id)
                    await self._cleanup_user_state(old_sid)
                    
                except Exception as disconnect_error:
                    await logger.awarning("Could not disconnect old session", error=str(disconnect_error))

    async def _on_connect(self, sid: str, environ: dict, auth: dict) -> None:
        logger = self._get_logger(sid, component='socket_connect')
        
        try:
            token = auth.get("token", None)
            if not token:
                await logger.awarning("No JWT provided - disconnecting")
                return await self.sio.disconnect(sid)
                
            try:
                await logger.adebug("Verifying JWT token")
                claims = JwtTokenUtils.verify_token(token)
            except TokenValidityException as e:
                await logger.awarning("Token verification failed", error=str(e))
                await self.sio.emit(
                    "token_expired",
                    {"message": "Token expired, please login again."},
                    room=sid
                )
                await self.sio.disconnect(sid)
                return

            user_id: str = claims["userId"]
            business_profile_id: str = claims["business_profile_id"]
            
            logger = self._get_logger(sid, user_id, business_profile_id=business_profile_id)
            await logger.ainfo("User authentication successful")
            
            await self._handle_existing_session_cross_worker(sid, user_id, logger)
            
            await self._save_session_data_redis(sid, user_id, business_profile_id, claims, logger)
            
            await self.sio.emit("session", {"session": sid}, room=sid)
            await logger.ainfo("Socket connection established successfully")
            
        except Exception as e:
            await logger.aexception("Unhandled error in socket connection", error=str(e))
            await self.sio.disconnect(sid)

    async def _on_disconnect(self, sid: str):
        logger = self._get_logger(sid, component='socket_disconnect')
        
        try:
            session = await self._get_session_data_redis(sid)
            user_id = session.get("userId") if session else None
            
            if user_id:
                logger = self._get_logger(sid, user_id)
            
            await logger.ainfo("Processing socket disconnection")
            
            await self._cleanup_user_state(sid)
            
            conversations = await self._get_user_conversations(sid)
            for conversation_id in conversations:
                try:
                    await self.sio.leave_room(sid=sid, room=str(conversation_id))
                except Exception:
                    pass
            
            phone_number_id = await self._get_user_business_group(sid)
            if phone_number_id:
                try:
                    await self.sio.leave_room(sid=sid, room=phone_number_id)
                except Exception:
                    pass
            
            if user_id:
                await self._cleanup_session_data(sid, user_id)
            
            await logger.ainfo("Socket disconnection completed")
            
        except Exception as e:
            await logger.aexception("Error during socket disconnection", error=str(e))

    async def _on_join_conversation(self, sid: str, data: dict):
        logger = self._get_logger(sid, component='join_conversation')
        
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                await logger.awarning("Join conversation failed - missing conversation_id")
                await self.sio.emit('error', {'message': 'conversation_id required'}, room=sid)
                return False
                
            session = await self._get_session_data_redis(sid)
            user_id = session.get("userId") if session else None
            business_profile_id = session.get("business_profile_id") if session else None
            
            if not user_id or not business_profile_id:
                await logger.aerror("Join conversation failed - invalid session data")
                await self.sio.emit('error', {'message': 'Invalid session'}, room=sid)
                return False
            
            logger = self._get_logger(sid, user_id, conversation_id=conversation_id, business_profile_id=business_profile_id)
            await self._join_conversation_internal(sid, conversation_id, user_id, business_profile_id, logger)
            
        except Exception as e:
            await logger.aexception("Error joining conversation", conversation_id=data.get('conversation_id'))
            await self.sio.emit('error', {'message': 'Failed to join conversation'}, room=sid)
            return False

    async def _join_conversation_internal(self, sid: str, conversation_id: str, user_id: str, business_profile_id: str, logger):
        try:
            await self.sio.enter_room(sid=sid, room=conversation_id)
            
            await self._add_user_to_conversation(sid, conversation_id, user_id)
            
            await self.redis.sadd(RedisHelper.redis_conversation_members_key(conversation_id), sid)
            await self.redis.expire(RedisHelper.redis_conversation_members_key(conversation_id), 3600)
            
            conversation_data = await self._get_conversation_state(conversation_id, logger)
            
            await self.sio.emit('conversation_joined', {
                'conversation_id': conversation_id,
                **conversation_data
            }, room=sid)
            
            await logger.ainfo("Successfully joined conversation")
            
        except Exception as e:
            await logger.aexception("Error in join conversation internal", error=str(e))

    async def _on_leave_conversation(self, sid: str, data: dict):
        logger = self._get_logger(sid, component='leave_conversation')
        
        try:
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                await logger.awarning("Leave conversation failed - missing conversation_id")
                await self.sio.emit('error', {'message': 'conversation_id required'}, room=sid)
                return False
            
            await self._leave_conversation_internal(sid, conversation_id, logger)
            
        except Exception as e:
            await logger.aexception("Error leaving conversation", conversation_id=data.get('conversation_id'))
            await self.sio.emit('error', {'message': 'Failed to leave conversation'}, room=sid)
            return False

    async def _leave_conversation_internal(self, sid: str, conversation_id: str, logger=None):
        if logger is None:
            logger = self._get_logger(sid, component='leave_conversation_internal')
            
        try:
            await self.sio.leave_room(sid=sid, room=conversation_id)
            
            await self._remove_user_from_conversation(sid, conversation_id)
            
            members_count = await self.redis.scard(RedisHelper.redis_conversation_members_key(conversation_id))
            if members_count == 0:
                await self.redis.delete(RedisHelper.redis_conversation_members_key(conversation_id))

            await self.sio.emit('conversation_left', {
                'conversation_id': conversation_id
            }, room=sid)
            
            await logger.ainfo("Successfully left conversation", conversation_id=conversation_id)
            
        except Exception as e:
            await logger.aexception("Error leaving conversation internal", 
                                    conversation_id=conversation_id, error=str(e))

    async def _on_join_business_group(self, sid: str, data: dict):
        logger = self._get_logger(sid, component='join_business_group')
        
        try:
            session = await self._get_session_data_redis(sid)
            user_id = session.get("userId") if session else None
            business_profile_id = session.get("business_profile_id") if session else None
            
            if not business_profile_id:
                await logger.aerror("Missing business profile ID for business group join")
                await self.sio.emit("error", {"message": "Missing business profile ID"}, room=sid)
                return
            
            logger = self._get_logger(sid, user_id, business_profile_id=business_profile_id)
            
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            await self._join_business_group_internal(sid, phone_number_id, user_id, business_profile_id, logger)
            
        except GlobalException as e:
            await logger.aexception("Error joining business group", error=str(e))

    async def _join_business_group_internal(self, sid: str, phone_number_id: str, user_id: str, business_profile_id: str, logger):
        try:
            await self.sio.enter_room(sid=sid, room=phone_number_id)
            
            await self._add_user_to_business_group(sid, phone_number_id, user_id)
            
            await self.redis.sadd(RedisHelper.redis_business_members_key(phone_number_id), sid)
            await self.redis.expire(RedisHelper.redis_business_members_key(phone_number_id), 3600)

            await self.sio.emit('business_group_joined', {
                'phone_number_id': phone_number_id
            }, room=sid)

            await logger.ainfo("Successfully joined business group", phone_number_id=phone_number_id)
            
        except Exception as e:
            await logger.aexception("Error in join business group internal", 
                                    phone_number_id=phone_number_id, error=str(e))

    async def _on_leave_business_group(self, sid: str):
        logger = self._get_logger(sid, component='leave_business_group')
        await self._leave_business_group_internal(sid, logger)

    async def _leave_business_group_internal(self, sid: str, logger=None):
        if logger is None:
            logger = self._get_logger(sid, component='leave_business_group_internal')
            
        try:
            session = await self._get_session_data_redis(sid)
            business_profile_id = session.get("business_profile_id") if session else None
            
            if not business_profile_id:
                await logger.awarning("No business profile ID found for leaving business group")
                return
                
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            
            await self.sio.leave_room(sid=sid, room=phone_number_id)
            
            await self._remove_user_from_business_group(sid, phone_number_id)
            
            members_count = await self.redis.scard(RedisHelper.redis_business_members_key(phone_number_id))
            if members_count == 0:
                await self.redis.delete(RedisHelper.redis_business_members_key(phone_number_id))
    
            await self.sio.emit('business_group_left', {
                'phone_number_id': phone_number_id
            }, room=sid)
            
            await logger.ainfo("Successfully left business group", phone_number_id=phone_number_id)
            
        except Exception as e:
            await logger.aexception("Error leaving business group", error=str(e))

    async def _on_mark_as_read(self, sid: str, data: dict):
        logger = self._get_logger(sid, component='mark_as_read')
        
        try:
            conversation_id = data.get("conversation_id")
            last_read_message_id = data.get("last_read_message_id")
            
            if not conversation_id or not last_read_message_id:
                await logger.awarning("Mark as read failed - missing required fields")
                await self.sio.emit('error', {
                    'message': 'conversation_id and last_read_message_id required'
                }, room=sid)
                return
        
            session = await self._get_session_data_redis(sid)
            user_id = session.get("userId") if session else None
            business_profile_id = session.get("business_profile_id") if session else None
            
            logger = self._get_logger(sid, user_id, conversation_id=conversation_id, last_read_message_id=last_read_message_id)
            
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id)
        
            await self.redis.hset_unread_consistent(
                unread_key, 
                mapping={"unread_count": 0, "last_read_message_id": last_read_message_id}
            )
        
            response_data = {
                "conversation_id": conversation_id, 
                "unread_count": 0, 
                "last_read_message_id": last_read_message_id
            }
            
            await self.sio.emit("unread_status_updated", data=response_data, room=phone_number_id)
            await logger.ainfo("Messages marked as read successfully")
            
        except Exception as e:
            await logger.aexception("Error marking messages as read", error=str(e))

    async def emit_received_message(self, message: dict, phone_number_id: str, conversation_id: str = None):
        logger = self._get_logger("system", component="message_emit", 
                                phone_number_id=phone_number_id, 
                                conversation_id=str(conversation_id),
                                message_id=message.get("message_id"))
        
        try:
            if not phone_number_id or not conversation_id:
                await logger.awarning("Cannot emit message - missing phone number ID or conversation ID")
                return
            
            await logger.adebug("Processing received message for emission")
            
            message_for_stream = {
                "wa_message_id": str(message.get("message_id")),
                "created_at": message.get("timestamp"),
                "message_type": message.get("type"),
                "content": message.get("content"), 
                "context": message.get("context") if message.get("context") else "",
                "is_from_contact": "true",  
                "message_status": "received", 
                "conversation_id": str(conversation_id),
            }
            
            redis_stream_message_id = await self.redis.xadd(
                RedisHelper.redis_conversation_messages_stream_key(conversation_id),
                message_for_stream,
                use_json=True
            )
            
            await logger.adebug("Message added to Redis stream", stream_id=redis_stream_message_id)
            
            unread_data = await self._update_unread_count(conversation_id, logger)
            
            last_message_content = Helper._get_last_message_content(message_data=message)
            business_data = {
                "conversation_id": str(conversation_id), 
                "last_message_content": last_message_content, 
                "last_message_time": f"{message.get('timestamp')}", 
                "unread_count": unread_data['unread_count']
            }
            
            await self.sio.emit(event="message_received", data=business_data, room=phone_number_id)
            
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
                        "conversation_id": str(conversation_id),
                        "redis_stream_id": redis_stream_message_id
                    },
                    "conversation_id": str(conversation_id)
                }
                await self.sio.emit(event="conversation_message_received", data=message_data, room=str(conversation_id))
            
            await logger.ainfo("Message emitted successfully to all recipients")
            
        except Exception as e:
            await logger.aexception("Error emitting received message", error=str(e))

    async def emit_chatbot_reply_message(self, payload: dict):
        logger = self._get_logger("system", component="chatbot_reply", 
                                conversation_id=payload.get("conversation_id"))
        
        try:
            business_data = payload.get("business_data", {})
            business_phone_number_id = business_data.get("business_phone_number_id")
            
            if not business_phone_number_id:
                await logger.awarning("Cannot emit chatbot reply - no business phone number ID")
                return
                
            await logger.adebug("Processing chatbot reply message")
            
            await self.emit_received_message(
                message=payload.get("message"), 
                phone_number_id=business_phone_number_id, 
                conversation_id=payload.get("conversation_id")
            )
            
            await logger.ainfo("Chatbot reply message emitted successfully")
        
        except Exception as e:
            await logger.aexception("Error emitting chatbot reply message", error=str(e))

    async def emit_message_status(self, conversation_id: str, status: str, message_id: str):
        logger = self._get_logger("system", component="message_status",
                                conversation_id=conversation_id,
                                message_id=message_id,
                                status=status)
        
        try:
            data = {
                "conversation_id": str(conversation_id),
                "status": status,
                "message_id": str(message_id),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.sio.emit(event="whatsapp_message_status", data=data, room=str(conversation_id))
            await logger.adebug("Message status emitted successfully")
                        
        except Exception as e:
            await logger.aexception("Error emitting message status", error=str(e))

    async def emit_conversation_assignment(self, user_id: str, conversation_id: str, assigned_to: str, assignment_message: dict):
        logger = self._get_logger("system", component="conversation_assignment",
                                conversation_id=str(conversation_id),
                                user_id=user_id,
                                assigned_to=assigned_to)
        
        try:
            user_sid = await self.redis.get(RedisHelper.redis_socket_user_id_session_key(user_id))
            
            if not user_sid:
                await logger.awarning("Skip assignment emit - user not connected", user_id=user_id)
                return

            session = await self._get_session_data_redis(user_sid)
            if not session:
                await logger.awarning("Skip assignment emit - no session data found")
                return
            
            business_profile_id = session.get("business_profile_id")
            if not business_profile_id:
                await logger.awarning("Skip assignment emit - no business profile ID")
                return

            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            if not phone_number_id:
                await logger.awarning("No phone number found for assignment emit")
                return
                
            business_data = {"conversation_id": str(conversation_id)}
            await self.sio.emit(
                event="conversation_assignment_businessgroup", 
                data=business_data, 
                room=phone_number_id
            )
    
            conversation_data = {
                "conversation_id": str(conversation_id),
                "assigned_to": str(assigned_to),
                "assignment_message": assignment_message
            }
            await self.sio.emit(
                "conversation_assignment_chat", 
                conversation_data, 
                room=str(conversation_id)
            )
    
            await logger.ainfo("Conversation assignment emitted successfully")
            
        except Exception as e:
            await logger.aexception("Error emitting conversation assignment", error=str(e))

    async def emit_conversation_status(self, user_id: str, conversation_id: str, status: str):
        logger = self._get_logger("system", component="conversation_status",
                                conversation_id=str(conversation_id),
                                user_id=user_id,
                                status=status)
        
        try:
            user_sid = await self.redis.get(RedisHelper.redis_socket_user_id_session_key(user_id))
            
            if not user_sid:
                await logger.awarning("Skip status emit - user not connected", user_id=user_id)
                return

            session = await self._get_session_data_redis(user_sid)
            if not session:
                await logger.awarning("Skip status emit - no session data found")
                return
                
            business_profile_id = session.get("business_profile_id")
            if not business_profile_id:
                await logger.awarning("Skip status emit - no business profile ID")
                return

            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            
            if phone_number_id:
                business_data = {"conversation_id": str(conversation_id), "status": status}
                await self.sio.emit(
                    event="conversation_status_business_group", 
                    data=business_data, 
                    room=phone_number_id
                )
            
            conversation_data = {
                "conversation_id": str(conversation_id),
                "status": status
            }
            await self.sio.emit(
                "conversation_status_chat", 
                conversation_data, 
                room=str(conversation_id)
            )
                
            await logger.ainfo("Conversation status emitted successfully")
            
        except Exception as e:
            await logger.aexception("Error emitting conversation status", error=str(e))
            
    async def emit_create_new_conversation(self, conversation_data: dict, business_profile_id: str):
        logger = self._get_logger("system", component="new_conversation",
                                business_profile_id=business_profile_id,
                                conversation_id=conversation_data.get("conversation_id"))
        
        try:
            phone_number_id = await self._get_business_profile_phone_number_id(business_profile_id)
            
            if phone_number_id:
                await self.sio.emit(
                    event="new_conversation", 
                    data=conversation_data, 
                    room=phone_number_id
                )
                await logger.ainfo("New conversation emitted successfully", phone_number_id=phone_number_id)
            else:
                await logger.awarning("Cannot emit new conversation - no phone number ID")
                
        except Exception as e:
            await logger.aexception("Error emitting new conversation", error=str(e))

    async def _get_conversation_state(self, conversation_id: str, logger) -> dict:
        try:
            redis_expiration_time = await self.redis.get(
                RedisHelper.redis_conversation_expired_key(conversation_id)
            )
            
            conversation_expiration_time = None
            is_conversation_expired = True
            
            if redis_expiration_time:
                conversation_expiration_time = Helper.conversation_expiration_calculate(redis_expiration_time)
                is_conversation_expired = False
            
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id)
            unread_status = await self.redis.hgetall_unread_consistent(unread_key)
            unread_count = self._extract_unread_count(unread_status)
            
            await self.redis.hset_unread_consistent(
                unread_key,
                {'unread_count': 0, 'last_read_message_id': '0-0'}
            )
            
            return {
                'expiration_time': conversation_expiration_time,
                'is_conversation_expired': is_conversation_expired,
                'unread_count': unread_count
            }
            
        except Exception as e:
            await logger.aerror("Error getting conversation state", error=str(e))
            return {
                'expiration_time': None,
                'is_conversation_expired': True,
                'unread_count': 0
            }

    async def _get_business_profile_phone_number_id(self, business_profile_id: str):
        logger = self._get_logger("system", component="business_profile_lookup",
                                business_profile_id=business_profile_id)
        
        try:
            cache_key = RedisHelper.redis_business_phone_number_id_key(business_profile_id)
            
            if await self.redis.exists(cache_key):
                phone_number_id = await self.redis.get(cache_key)
                await logger.adebug("Retrieved phone number ID from cache", phone_number_id=phone_number_id)
                return phone_number_id
            
            await logger.adebug("Fetching business profile from service")
            business_profile = await self.business_profile_service.get(business_profile_id)
            
            await self.redis.set(cache_key, business_profile.phone_number_id, ttl=86400)
            
            await logger.adebug("Business profile fetched and cached", 
                                phone_number_id=business_profile.phone_number_id)
            return business_profile.phone_number_id
            
        except GlobalException as e:
            await logger.aexception("Error getting business profile", error=str(e))
            raise
        except Exception as e:
            await logger.aexception("Unexpected error getting business profile", error=str(e))
            return None

    async def _update_unread_count(self, conversation_id: str, logger) -> dict:
        try:
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id)
            members_count = await self.redis.scard(RedisHelper.redis_conversation_members_key(conversation_id))
            
            if members_count <= 0:
                await self.redis.hincrby(unread_key, 'unread_count', 1)
                await self.redis.hset_unread_consistent(unread_key, {'last_read_message_id': '0-0'})
            
            updated_unread_status = await self.redis.hgetall_unread_consistent(unread_key)
            updated_unread_count = self._extract_unread_count(updated_unread_status)
            
            return {'unread_count': updated_unread_count}
            
        except Exception as e:
            await logger.aerror("Error updating unread count", error=str(e))
            return {'unread_count': 0}

    def _extract_unread_count(self, unread_status: dict) -> int:
        if not unread_status:
            return 0
        
        unread_count_raw = unread_status.get('unread_count', 0)
        
        try:
            if isinstance(unread_count_raw, int):
                return unread_count_raw
            elif isinstance(unread_count_raw, str):
                if unread_count_raw.isdigit():
                    return int(unread_count_raw)
                elif unread_count_raw.replace('.', '', 1).isdigit():
                    return int(float(unread_count_raw))
                else:
                    return 0
            elif isinstance(unread_count_raw, (float, bytes)):
                return int(unread_count_raw)
            else:
                return 0
        except (ValueError, TypeError):
            return 0