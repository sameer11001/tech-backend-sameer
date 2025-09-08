import io
import json
from uuid import UUID
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.services.ChatBotService import ChatBotService
from app.events.pub.ChatBotTriggerPublisher import ChatBotTriggerPublisher
from app.user_management.user.models.Client import Client
from app.utils.Helper import Helper
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from app.annotations.services.ContactService import ContactService
from app.chat_bot.models.ChatBot import FlowNode
from app.chat_bot.services.ChatbotContextService import ChatbotContextService
from app.events.pub.ChatbotFlowPublisher import ChatbotFlowPublisher
from app.events.pub.MessageReceivedPublisher import MessageHookReceivedPublisher
from app.events.pub.WhatsappMessagePublisher import WhatsappMessagePublisher
from app.core.logs.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.storage.redis import AsyncRedisService
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.user_management.user.models.Team import Team
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.TeamService import TeamService
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.team_inbox.models.schema.response.ConversationWithContact import ConversationWithContact
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
        chatbot_service: ChatBotService,
        message_publisher: WhatsappMessagePublisher,
        chatbot_context_service: ChatbotContextService,
        chatbot_flow_publisher: ChatbotFlowPublisher,
        chatbot_trigger_publisher: ChatBotTriggerPublisher,
        media_api: WhatsAppMediaApi,
        redis_service: AsyncRedisService,
        socket_message: SocketMessageGateway,
        mongo_message: MongoCRUD[Message],
        mongo_flow: MongoCRUD[FlowNode],
        s3_service: S3Service,
        message_hook_received_publisher: MessageHookReceivedPublisher,
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
        self.chatbot_service = chatbot_service
        self.message_publisher = message_publisher
        self.chatbot_trigger_publisher = chatbot_trigger_publisher
        self.media_api = media_api
        self.redis_service = redis_service
        self.socket_message = socket_message
        self.mongo_message = mongo_message
        self.mongo_flow = mongo_flow
        self.s3_service = s3_service
        self.message_hook_received_publisher = message_hook_received_publisher
        self.aws_s3_bucket = aws_s3_bucket
        self.aws_region = aws_region
        self.chatbot_context_service = chatbot_context_service
        self.chatbot_flow_publisher = chatbot_flow_publisher
        self.logger = get_logger("MessageHook")

    def _get_logger(self, phone_id: str = "", message_id: str = "", conversation_id: str = "", **kwargs):
        return self.logger.with_context(
            phone_id=phone_id,
            message_id=message_id,
            conversation_id=conversation_id,
            component='message_processing',
            **kwargs
        )

    async def handle_messages(self, payload: Dict[str, Any]) -> Optional[Any]:
        phone_id = payload.get("metadata", {}).get("phone_number_id", "")
        logger = self._get_logger(phone_id=phone_id, operation='handle_messages')
        
        if any(m.get("errors") for m in payload.get("messages", [])):
            await logger.awarning("Message has errors, unsupported message type - skipping")
            return None
        
        try:
            if payload.get("messages"):
                await logger.adebug("Processing received messages", message_count=len(payload.get("messages", [])))
                return await self.handle_received_messages(payload)
            
            if payload.get("statuses"):
                await logger.adebug("Processing message statuses", status_count=len(payload.get("statuses", [])))
                return await self.handle_statuses(payload)
            
        except Exception as e:
            await logger.aexception("Unhandled error in message processing", error=str(e))
        return None

    async def handle_received_messages(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        metadata = payload.get("metadata", {})
        display_number = metadata.get("display_phone_number")
        phone_id = metadata.get("phone_number_id")
        
        logger = self._get_logger(phone_id=phone_id, operation='handle_received_messages')
        
        profile : BusinessProfile = await self.business_profile_service.get_by_phone_number_id(str(phone_id))
        access_token = profile.access_token
        contact_info = self._extract_contact_info(payload.get("contacts", []))

        await logger.adebug("Processing incoming messages", 
                            display_number=display_number,
                            contact_wa_id=contact_info.get("wa_id"))

        for msg in payload.get("messages", []):
            message_id = msg.get("id", "")
            
            data = self._create_base_message_data(msg, display_number, phone_id, contact_info)
            await self._process_message(msg, data, phone_id, access_token, logger)
            await self._handle_context(data, msg, logger)
            
            conversation: Conversation = await self.get_or_create_conversation(
                msg["from"], f'+{display_number}', contact_info, profile, logger
            )
            
            msg_type = msg.get("type")
            
            await self.message_hook_received_publisher.publish_message(
                message_body=data, conversation_id=str(conversation.id),recipient_number=f'+{display_number}'
            )
            if msg_type == "interactive":
                await self._handle_chatbot_interaction(msg, conversation, logger)
                data["type"] = "button_interactive"

            await self.socket_message.emit_received_message(
                message=data, phone_number_id=phone_id, conversation_id=str(conversation.id)
            )

            await logger.adebug("Message data processed", message_type=msg_type)

            await logger.adebug(f"Message sent to socket {data}", message_type=msg_type)
            
            await self._set_conversation_expiration(conversation.id, logger)
                        
            await self.save_message.process_message(
                message_data=data, conversation_id=conversation.id, contact_id=conversation.contact_id
            )
            

    async def _handle_chatbot_interaction(self, msg: Dict[str, Any], conversation: Conversation, 
                                        logger):
        interactive = msg.get("interactive", {})
        interactive_type = interactive.get("type")
        
        await logger.adebug("Processing chatbot interaction", interaction_type=interactive_type)
        
        if interactive_type == "button_reply":
            button_reply = interactive.get("button_reply", {})
            button_id = button_reply.get("id")
            await self._process_chatbot_button_click(conversation, button_id, msg, logger)
        
        elif interactive_type == "list_reply":
            list_reply = interactive.get("list_reply", {})
            list_id = list_reply.get("id")
            await self._process_chatbot_list_selection(conversation, list_id, msg, logger)

    async def _handle_text_response_to_chatbot(self, msg: Dict[str, Any], conversation: Conversation, 
                                                logger):
        try:
            chatbot_context = await self.chatbot_context_service.get_chatbot_context(conversation.id)
            
            if not chatbot_context:
                await logger.adebug("No chatbot context found for conversation")
                return  
                
            if chatbot_context.get("waiting_for_response") and chatbot_context.get("node_type") == "question":
                current_node_id = chatbot_context.get("current_node_id")
                chatbot_id = chatbot_context.get("chatbot_id")
                
                text_content = msg.get("text", {}).get("body", "")
                
                business_data = await self._get_business_data_for_conversation(conversation, msg, logger)
                
                flow_payload = {
                    "conversation_id": str(conversation.id),
                    "current_node_id": current_node_id,
                    "user_response": text_content,
                    "business_data": business_data
                }
                
                await self.chatbot_flow_publisher.publish_flow_node_event(flow_payload)
                await logger.adebug("Published chatbot flow event for text response", 
                                text_preview=text_content[:50])
                
        except Exception as e:
            await logger.aexception("Error handling text response to chatbot", error=str(e))

    async def _process_chatbot_button_click(self, conversation: Conversation, button_id: str, 
                                            msg: Dict[str, Any], logger):
        if conversation.chatbot_triggered:
            try:
                
                chatbot_context = await self.chatbot_context_service.get_chatbot_context(str(conversation.id))
                
                chat_bot_id = conversation.chatbot_id
                
                if not chatbot_context:
                    first_node : FlowNode = await self.mongo_flow.find_one(query= {
                        "chat_bot_id": chat_bot_id,
                        "is_first": True
                    })
                    await self.chatbot_context_service.set_chatbot_context(
                        conversation_id = str(conversation.id), 
                        chatbot_id = chat_bot_id,
                        current_node_id = first_node.id
                        
                    )
                    chatbot_context = {
                        "current_node_id": first_node.id,
                        "chatbot_id": chat_bot_id
                    }
                    
                current_node_id = chatbot_context.get("current_node_id")
                chatbot_id = chatbot_context.get("chatbot_id")
                
                if not current_node_id or not chatbot_id:
                    await logger.adebug("Invalid chatbot context for conversation")
                    return
                
                flow_node_by_button_id: FlowNode = await self.mongo_flow.find_one({
                    "chat_bot_id": UUID(chatbot_id) if isinstance(chatbot_id, str) else chatbot_id,
                    "type": "interactive_buttons", 
                    "buttons.id": button_id, 
                })
                
                if not flow_node_by_button_id:
                    await logger.adebug("Flow node not found for button click", 
                                        button_id=button_id, 
                                        chatbot_id=str(chatbot_id))
                    return
                    
                business_data = await self._get_business_data_for_conversation(conversation, msg, logger)
                
                flow_payload = {
                    "conversation_id": str(conversation.id),
                    "current_node_id": flow_node_by_button_id.id,
                    "button_id": button_id,
                    "business_data": business_data
                }
                
                await self.chatbot_flow_publisher.flow_node_event(flow_payload)
                
                await self.chatbot_context_service.extend_context_ttl(str(conversation.id))
                
                await logger.adebug("Published chatbot flow event for button click", button_id=button_id)
                
            except Exception as e:
                await logger.aexception("Error processing chatbot button click", error=str(e), button_id=button_id)
                
    async def _process_chatbot_list_selection(self, conversation: Conversation, list_id: str, 
                                            msg: Dict[str, Any], logger):
        await self._process_chatbot_button_click(conversation, list_id, msg, logger)

    async def _get_business_data_for_conversation(self, conversation: Conversation, msg: Dict[str, Any], 
                                                    logger) -> Dict[str, Any]:
        try:
            metadata = msg.get("metadata", {})
            phone_id = metadata.get("phone_number_id")
            
            business_token = None
            
            if phone_id:
                try:
                    profile = await self.business_profile_service.get_by_phone_number_id(str(phone_id))
                    business_token = profile.access_token
                    await logger.adebug("Got business data from metadata", phone_id=phone_id)
                except Exception as e:
                    await logger.awarning(f"Failed to get profile from phone_id: {e}")
                    phone_id = None  
            
            if not business_token or not phone_id:
                client = await self.client_service.get(conversation.client_id)
                
                profile = await self.business_profile_service.get_by_client_id(str(client.id))
                
                if profile:
                    business_token = profile.access_token
                    phone_id = profile.phone_number_id
                    await logger.adebug("Got business data from client profile", client_id=str(client.id))
                else:
                    await logger.aerror("No business profile found for client", client_id=str(client.id))
                    raise ValueError(f"No business profile found for client {client.id}")
            
            recipient_number = msg.get("from")
            if not recipient_number:
                contact = await self.contact_service.get(conversation.contact_id)
                recipient_number = f"{contact.country_code}{contact.phone_number}"
            
            return {
                "business_token": business_token,
                "business_phone_number_id": phone_id,
                "recipient_number": recipient_number,
                "contact_id": str(conversation.contact_id),
                "client_id": str(conversation.client_id),
                "chatbot_id": str(conversation.chatbot_id) if hasattr(conversation, 'chatbot_id') else None
            }
            
        except Exception as e:
            await logger.aexception("Error getting business data", error=str(e))
            raise

    async def _process_message(self, msg: Dict[str, Any], data: Dict[str, Any], 
                             phone_id: str, access_token: str, logger) -> None:
        msg_type = msg.get("type")
        if msg_type in ("image", "video", "audio", "document"):
            await self._handle_incoming_media(msg, data, phone_id, access_token, logger)
        else:
            self._process_message_content(data, msg, msg_type)
        await logger.adebug("Message processed", message_type=msg_type)

    async def _handle_incoming_media(self, msg: Dict[str, Any], data: Dict[str, Any], 
                                   phone_id: str, access_token: str, logger) -> None:
        msg_type = msg.get("type")
        media = msg.get(msg_type, {})
        media_id = media.get("id")
        
        await logger.adebug("Processing incoming media", media_type=msg_type, media_id=media_id)
        
        try:
            media_info = await self.media_api.retrieve_media_url(media_id, phone_id, access_token)
            media_url = media_info.get("url")
            file_bytes = await self.media_api.download_media(media_url, access_token)
            file_stream = io.BytesIO(file_bytes)
            file_stream.seek(0)
            filename = media.get("filename") or f"{media_id}.{self._get_file_extension(media.get('mime_type'))}"

            s3_key = self.s3_service.upload_fileobj(file=file_stream, file_name=filename)
            cdn_url = self.s3_service.get_cdn_url(s3_key)

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
            
            await logger.adebug("Media uploaded successfully", s3_key=s3_key)
            
        except Exception as e:
            await logger.aexception("Failed to process media, using fallback", error=str(e))
            data["content"] = {
                "media_id": media_id,
                "mime_type": media.get("mime_type"),
                "caption": media.get("caption", "") if msg_type in ("image", "video") else "",
                "filename": media.get("filename", "") if msg_type == "document" else "",
            }

    def _get_file_extension(self, mime_type: str) -> str:
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

    async def _handle_context(self, data: Dict[str, Any], msg: Dict[str, Any], logger) -> None:
        context = msg.get("context")
        if not context:
            data["context"] = None
            return

        try:
            if "referred_product" in context:
                data["context"] = {
                    "type": "product_inquiry",
                    "catalog_id": context["referred_product"].get("catalog_id"),
                    "product_retailer_id": context["referred_product"].get("product_retailer_id"),
                    "from": context.get("from"),
                    "message_id": context.get("id")
                }
                await logger.adebug("Product inquiry context set", context_type="product_inquiry")
                return

            context_message_id = context.get("id")
            if context_message_id:
                original_message = await self.mongo_message.find_one({"wa_message_id": context_message_id})
                await logger.adebug("Looking up original message for context", original_message_id=context_message_id)
                
                if original_message:
                    await logger.adebug("Original message found for context")
                    data["context"] = {
                        "type": "reply",
                        "original_content": original_message.content,
                        "replied_message_id": context_message_id
                    }
                else:
                    await logger.awarning("Original message not found for context", context_message_id=context_message_id)
                    data["context"] = {
                        "type": "reply",
                        "replied_message_id": context_message_id
                    }
        except Exception as e:
            await logger.aexception("Error handling context", error=str(e))
            data["context"] = None

    async def _should_trigger_chatbot(self, from_number: str, client_number: str, logger) -> bool:
        try:
            contact = await self.contact_service.get_by_business_profile_and_contact_number(
                client_number, from_number
            )
            
            if contact is None:
                await logger.adebug("New contact - triggering chatbot")
                return True
            
            conversation = await self.conversation_service.find_by_contact_and_client_number(
                contact_phone_number=from_number, 
                client_phone_number=client_number
            )
            
            if conversation is None:
                await logger.adebug("No conversation for existing contact - triggering chatbot")
                return True
            
            expiration_key = RedisHelper.redis_conversation_expired_key(conversation.id)
            is_active = await self.redis_service.exists(expiration_key)
            
            if not is_active:
                await logger.adebug("Conversation expired - triggering chatbot")
                return True
            
            await logger.adebug("Active conversation exists - no chatbot trigger needed")
            return False
            
        except Exception as e:
            await logger.aexception("Error checking chatbot trigger", error=str(e))
            return False


    async def get_or_create_conversation(self, from_number: str, client_number: str, 
                                        contact_info: Dict[str, Any], business_profile: BusinessProfile, 
                                        logger) -> Conversation:
        
        should_trigger = await self._should_trigger_chatbot(from_number, client_number, logger)
        
        convo: Conversation = await self.conversation_service.find_by_contact_and_client_number(
            contact_phone_number=from_number, client_phone_number=client_number,
        )
        
        client : Client = await self.client_service.get_by_business_profile_number(client_number)
        default_chatbot : ChatBotMeta = await self.chatbot_service.get_default_by_client_id(client.id)
        
        if convo:
            if not convo.is_open:
                convo.is_open = True
                convo = await self.conversation_service.update(convo.id, {"is_open": True})
                await logger.adebug("Reopened existing conversation", conversation_id=str(convo.id))
            
            if should_trigger:
                await self.chatbot_trigger_publisher.trigger_chatbot_event({
                    "conversation_id": str(convo.id),
                    "chatbot_id": str(default_chatbot.id),
                    "business_token": business_profile.access_token,
                    "business_phone_number_id": business_profile.phone_number_id,
                    "recipient_number": f"+{from_number}"
                })
                
                await logger.adebug("Triggered chatbot for existing conversation")
                await self.socket_message.emit_chatbot_triggered_status(conversation_id=str(convo.id), business_profile_id=str(business_profile.id), chatbot_triggered=True)
            
            return convo
            
        contact = await self.contact_service.get_by_business_profile_and_contact_number(client_number, from_number)
        country, national = Helper.number_parsed(from_number)
        
        await logger.adebug("Creating new conversation", country=country, national=national, contact_exists=bool(contact))
    
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
            await logger.adebug("Created new contact", contact_id=str(contact.id))
        
        default_team: Team = await self.team_service.get_default_team_by_client_id(client.id)
    
        conversation: Conversation = Conversation(
            contact_id=contact.id,
            client_id=client.id,
            status=ConversationStatus.OPEN,
            is_open=True,
            chatbot_triggered=True  
        )
        conversation_team_link = ConversationTeamLink(
            conversation=conversation, team=default_team
        )
        conversation.teams.append(conversation_team_link)
        conversation_created = await self.conversation_service.create(conversation)
        
        conversation_body = ConversationWithContact(
            id=str(conversation_created.id),
            contact_id=str(contact.id),
            client_id=str(client.id),
            status=conversation_created.status,
            is_open=conversation_created.is_open,
            contact_name=contact.name,
            contact_phone_number=contact.phone_number,
            country_code_phone_number=contact.country_code,
            conversation_is_expired=False,
            conversation_expiration_time="23:59:59",
            unread_count=0,
            last_message="",
            last_message_time=datetime.now(timezone.utc).isoformat()
        )
        conversation_data = json.loads(conversation_body.model_dump_json())
        await self.socket_message.emit_create_new_conversation(conversation_data, business_profile_id)
        
        await self.chatbot_trigger_publisher.trigger_chatbot_event({
            "conversation_id": str(conversation_created.id)
        })
        await logger.adebug("Created new conversation and triggered chatbot", conversation_id=str(conversation_created.id))
        await self.socket_message.emit_chatbot_triggered_status(conversation_id=str(conversation_created.id), business_profile_id=business_profile_id, chatbot_triggered=True)
        return conversation_created

    async def _set_conversation_expiration(self, conversation_id: Any, logger) -> None:
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        key = RedisHelper.redis_conversation_expired_key(conversation_id)
        await self.redis_service.set(key=key, value=tomorrow, ttl=86400)
        await logger.adebug("Set conversation expiration", conversation_id=str(conversation_id))

    async def handle_statuses(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        statuses = payload.get("statuses", [])
        meta = payload.get("metadata", {})
        phone_id = meta.get("phone_number_id", "")
        
        logger = self._get_logger(phone_id=phone_id, operation='handle_statuses')
        details = []
        
        for st in statuses:
            message_id = st.get("id")
            status = st.get("status")
            
            entry = {
                "metadata": {
                    "display_phone_number": meta.get("display_phone_number"),
                    "phone_number_id": meta.get("phone_number_id"),
                },
                "wa_message_id": message_id,
                "recipient_id": st.get("recipient_id"),
                "status": status,
                "timestamp": st.get("timestamp"),
            }
            await logger.adebug("Publishing status update", status=status)
            
            await self.message_publisher.send_message(entry)
            message_document = await self.mongo_message.find_one({"wa_message_id": message_id})
            
            if message_document:
                await logger.adebug("Emitting message status update", 
                                        conversation_id=str(message_document.conversation_id),
                                        status=status)
                
                await self.socket_message.emit_message_status(
                    conversation_id=message_document.conversation_id, 
                    status=status, 
                    message_id=message_document.id
                )
            else:
                await logger.awarning("Message document not found for status update")

    def _extract_contact_info(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not contacts:
            return {"profile_name": None, "wa_id": None}
        c = contacts[0]
        return {
            "profile_name": c.get("profile", {}).get("name"),
            "wa_id": c.get("wa_id"),
        }

    def _create_base_message_data(
        self, msg: Dict[str, Any], display_number: str, phone_id: str, contact_info: Dict[str, Any],
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
        self, base: Dict[str, Any], msg: Dict[str, Any], msg_type: str,
    ) -> None:
        handlers = {
            "text": self.handle_text_message,
            "interactive": self.handle_interactive_message,
            "button": self.handle_button_message,  
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
        interactive_type = interactive.get("type")
        
        base_content = {
            "interactive_type": interactive_type,
            "interactive": interactive
        }
        
        if interactive_type == "button_reply":
            button_reply = interactive.get("button_reply", {})
            base_content.update({
                "button_id": button_reply.get("id"),
                "button_title": button_reply.get("title"),
                "user_selection": {
                    "type": "button",
                    "id": button_reply.get("id"),
                    "title": button_reply.get("title")
                }
            })
        
        elif interactive_type == "list_reply":
            list_reply = interactive.get("list_reply", {})
            base_content.update({
                "list_id": list_reply.get("id"),
                "list_title": list_reply.get("title"),
                "list_description": list_reply.get("description"),
                "user_selection": {
                    "type": "list",
                    "id": list_reply.get("id"),
                    "title": list_reply.get("title"),
                    "description": list_reply.get("description")
                }
            })
        
        return base_content

    def handle_button_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        button = msg.get("button", {})
        return {
            "button_type": "quick_reply",
            "button_text": button.get("text"),
            "button_payload": button.get("payload"),
            "user_selection": {
                "type": "quick_reply",
                "text": button.get("text"),
                "payload": button.get("payload")
            }
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