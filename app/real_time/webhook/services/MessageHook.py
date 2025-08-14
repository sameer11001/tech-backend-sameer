from datetime import datetime, timedelta, timezone
import io
from typing import Any, Dict, List, Optional

from app.annotations.services.ContactService import ContactService
from app.core.broker.WhatsappMessagePublisher import WhatsappMessagePublisher
from app.core.config.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.storage.redis import AsyncRedisService
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.user_management.user.models.Client import Client
from app.user_management.user.models.Team import Team
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.TeamService import TeamService
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.utils.Helper import Helper
from app.whatsapp.team_inbox.models.Assignment import Assignment
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.ConversationTeamLink import ConversationTeamLink
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.operations.SaveMessage import SaveMessage
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService
from app.core.services.S3Service import S3Service
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi
from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus
from app.annotations.models.Contact import Contact

logger = get_logger(__name__)

class MessageHook:
    def __init__(
        self,
        message_service: MessageService,
        conversation_service: ConversationService,
        save_message: SaveMessage,
        contact_service: ContactService,
        client_service: ClientService,
        assignment_service: AssignmentService,
        team_service: TeamService,
        business_profile_service: BusinessProfileService,
        message_publisher: WhatsappMessagePublisher,
        media_api: WhatsAppMediaApi,
        redis_service: AsyncRedisService,
        socket_message: SocketMessageGateway,
        mongo_message: MongoCRUD[Message],
        s3_service: S3Service,
        aws_s3_bucket: str,
        aws_region: str,
    ):
        self.message_service = message_service
        self.conversation_service = conversation_service
        self.save_message = save_message
        self.contact_service = contact_service
        self.client_service = client_service
        self.assignment_service = assignment_service
        self.team_service = team_service
        self.business_profile_service = business_profile_service
        self.message_publisher = message_publisher
        self.media_api = media_api
        self.redis_service = redis_service
        self.socket_message = socket_message
        self.mongo_message = mongo_message
        self.s3_service = s3_service
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_region = aws_region


    async def handle_messages(self, payload: Dict[str, Any]) -> Optional[Any]:
        if any(m.get("errors") for m in payload.get("messages", [])):
            logger.warning("message has errors unsupported message type and skipping")
            return None 
        
        try:
            if payload.get("messages"):
                return await self.handle_received_messages(payload)
            if payload.get("statuses"):
                return await self.handle_statuses(payload)

        except Exception:
            pass
        return None

    async def handle_received_messages(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        metadata = payload.get("metadata", {})
        display_number = metadata.get("display_phone_number")
        phone_id = metadata.get("phone_number_id")

        profile = await self.business_profile_service.get_by_phone_number_id(str(phone_id))
        access_token = profile.access_token
        contact_info = self._extract_contact_info(payload.get("contacts", []))

        for msg in payload.get("messages", []):
            
            data = self._create_base_message_data(msg, display_number, phone_id, contact_info)
            await self._process_message(msg, data, phone_id, access_token)
            await self._handle_context(data, msg)
            
            conversation : Conversation = await self.get_or_create_conversation(
                msg["from"], f'+{display_number}', contact_info
            )
            logger.info(f"this is data context: {data}")
            await self.socket_message.emit_received_message(message=data,phone_number_id=phone_id,conversation_id=str(conversation.id))
            await self._set_conversation_expiration(conversation.id)
            await self.save_message.process_message(message_data=data,conversation_id= conversation.id,contact_id= conversation.contact_id)

    async def _process_message(
        self, msg: Dict[str, Any], data: Dict[str, Any], phone_id: str, access_token: str
    ) -> None:
        msg_type = msg.get("type")
        if msg_type in ("image", "video", "audio", "document"):
            await self._handle_incoming_media(msg, data, phone_id, access_token)
        else:
            self._process_message_content(data, msg, msg_type)
        logger.info(f"this is the data: {data} and this is the message: {msg}")

    async def _handle_incoming_media(
        self,
        msg: Dict[str, Any],
        data: Dict[str, Any],
        phone_id: str,
        access_token: str,
    ) -> None:
        msg_type = msg.get("type")
        media = msg.get(msg_type, {})
        media_id = media.get("id")

        try:
            
            media_info = await self.media_api.retrieve_media_url(media_id, phone_id, access_token)

            media_url = media_info.get("url")
            file_bytes = await self.media_api.download_media(media_url, access_token)
            file_stream = io.BytesIO(file_bytes)
            file_stream.seek(0)
            
            filename = media.get("filename") or f"{media_id}.{self._get_file_extension(media.get('mime_type'))}"
            
            # Upload to S3
            s3_key = self.s3_service.upload_fileobj(file=file_stream, file_name=filename)
            cdn_url = f"https://{self.aws_s3_bucket}.s3.{self.aws_region}.amazonaws.com/{s3_key}"

            # Set content based on media type
            base_content = {
                "media_id": media_id,
                "mime_type": media.get("mime_type"),
                "cdn_url": cdn_url,
            }

            if msg_type in ("image", "video", "document", "audio"):
                base_content["caption"] = media.get("caption", "")
                
            if msg_type == "document":
                base_content["filename"] = media.get("filename", "")

            data["content"] = base_content

        except Exception as e:
            data["content"] = {
                "media_id": media_id,
                "mime_type": media.get("mime_type"),
                "caption": media.get("caption", "") if msg_type in ("image", "video") else "",
                "filename": media.get("filename", "") if msg_type == "document" else "",
            }

    def _get_file_extension(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "video/mp4": "mp4",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "application/pdf": "pdf",
            "text/plain": "txt",
            "text/csv": "csv",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        }
        return mime_map.get(mime_type, "bin")

    async def _handle_context(self, data: Dict[str, Any], msg: Dict[str, Any]) -> None:
        if not msg.get("context"):
            data["context"] = None
            return
        try:
            context_message_id = msg.get("context", {}).get("id")
            
            original_message = await self.mongo_message.find_one({"wa_message_id": context_message_id})
            
            logger.debug(f"Original message: {original_message}")

            if original_message:
                logger.debug(f"Original message found for context ID: {original_message.wa_message_id}")
                
                data["context"] = original_message.content

                logger.debug(f"Context set for reply to message: {context_message_id}")
            else:
                logger.warning(f"Original message not found for context ID: {context_message_id}")
                data["context"] = {
                    "replied_message_id": context_message_id
                }
                
        except Exception as e:
            logger.error(f"Error handling context: {e}")
            data["context"] = None

    async def get_or_create_conversation(
        self,
        from_number: str,
        client_number: str,
        contact_info: Dict[str, Any],
    ) -> Conversation:
        convo : Conversation = await self.conversation_service.find_by_contact_and_client_number(
            contact_phone_number=from_number,
            client_phone_number=client_number,
        )
        if convo:
            if not convo.is_open:
                convo.is_open = True
                convo = await self.conversation_service.update(convo.id, {"is_open": True})
            return convo

        client = await self.client_service.get_by_business_profile_number(client_number)
        contact = await self.contact_service.get_by_client_and_contact_number(client_number, from_number)
        country, national = Helper.number_parsed(from_number)
        
        logger.info(f"country: {country}, national: {national} and contact: {contact}")
        
        if contact is None:
            contact = await self.contact_service.create(
                Contact(
                    name=contact_info.get("profile_name"),
                    country_code=str(country),
                    phone_number=str(national),
                    source="whatsapp",
                    status="valid",
                    client_id=client.id,
                )
            )

        assign = await self.assignment_service.create(
            Assignment(user_id="01984da8-a56b-7ed8-99d7-ce2be8baf6b4", assigned_by="01984da8-a56b-7ed8-99d7-ce2be8baf6b4")
        )
        default_team : Team = await self.team_service.get_default_team_by_client_id(client.id)
        
        logger.info(f"default_team: {default_team} and assign: {assign} and contact: {contact}")
        conversation : Conversation = Conversation(
            contact_id=contact.id,
            client_id=client.id,
            assignment_id=assign.id,
            status=ConversationStatus.OPEN,
            is_open=True
        )
        conversation_team_link = ConversationTeamLink(
            conversation=conversation,
            team=default_team
        )
            
        conversation.teams.append(conversation_team_link)
        return await self.conversation_service.create(conversation)

    async def _set_conversation_expiration(self, conversation_id: Any) -> None:
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        key = RedisHelper.redis_conversation_expired_key(conversation_id)
        await self.redis_service.set(key=key, value=tomorrow, ttl=86400)

    async def handle_statuses(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        statuses = payload.get("statuses", [])
        meta = payload.get("metadata", {})
        details = []

        for st in statuses:
            entry = {
                "metadata": {
                    "display_phone_number": meta.get("display_phone_number"),
                    "phone_number_id": meta.get("phone_number_id"),
                },
                "wa_message_id": st.get("id"),
                "recipient_id": st.get("recipient_id"),
                "status": st.get("status"),
                "timestamp": st.get("timestamp"),
            }
            logger.info(f"publishing status: {entry}")
            await self.message_publisher.send_message(entry)
            message_document = await self.mongo_message.find_one({"wa_message_id": st.get("id")})
            logger.info(f"message_status_document: {message_document.conversation_id} , message_id: {message_document.id} and status: {st.get('status')}")
            await self.socket_message.emit_message_status(conversation_id=message_document.conversation_id, status=st.get("status"), message_id=message_document.id)

    def _extract_contact_info(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not contacts:
            return {"profile_name": None, "wa_id": None}
        c = contacts[0]
        return {
            "profile_name": c.get("profile", {}).get("name"),
            "wa_id": c.get("wa_id"),
        }

    def _create_base_message_data(
        self,
        msg: Dict[str, Any],
        display_number: str,
        phone_id: str,
        contact_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        base = {
            "message_id": msg.get("id"),
            "sender": msg.get("from"),
            "timestamp": msg.get("timestamp"),
            "type": msg.get("type"),
            "context": None,  
            "content": {},
            "metadata": {
                "display_phone_number": display_number,
                "phone_number_id": phone_id,
                "is_sent_by_business": False,
            },
            "contact": contact_info,
        }
        return base

    def _process_message_content(
        self,
        base: Dict[str, Any],
        msg: Dict[str, Any],
        msg_type: str,
    ) -> None:
        handlers = {
            "text": self.handle_text_message,
            "interactive": self.handle_interactive_message,
            "location": self.handle_location_message,
            "reaction": self.handle_reaction_message,
        }
        if fn := handlers.get(msg_type):
            base["content"] = fn(msg)
        else:
            base["content"] = {}

    def handle_text_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        return {"text": msg.get("text", {}).get("body")}

    def handle_interactive_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        interactive = msg.get("interactive", {})
        return {
            "interactive_type": interactive.get("type"),
            "interactive": interactive
        }

    def handle_location_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        loc = msg.get("location", {})
        return {
            "latitude": loc.get("latitude"), 
            "longitude": loc.get("longitude"),
            "name": loc.get("name"),
            "address": loc.get("address")
        }

    def handle_reaction_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        react = msg.get("reaction", {})
        return {
            "message_id": react.get("message_id"), 
            "emoji": react.get("emoji")
        }
    