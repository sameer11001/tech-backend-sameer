from asyncio.log import logger
from base64 import b64decode
from io import BytesIO
import io
from typing import Any, Dict, List

from fastapi import UploadFile
import uuid6
from app.chat_bot.models.ChatBot import FlowNode, ServiceHook
from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodBodyRequest import ContentItem, MessageContentNodeRequest, QuestionContentNodeRequest
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodeRequest import DynamicFlowNodeRequest
from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.chat_bot.services.ChatBotService import ChatBotService

from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.core.services.S3Service import S3Service
from app.utils.enums.FlowNodeType import FlowNodeType
from app.utils.enums.InteractiveMessageEnum import HeaderType, InteractiveType
from app.utils.enums.MessageContentType import MessageContentType
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi


class AddFlowNode:
    def __init__(
        self,
        chat_bot_service: ChatBotService,
        business_service: BusinessProfileService,
        whatsapp_media_api: WhatsAppMediaApi,
        s3_bucket_service : S3Service,
        aws_region:str, 
        aws_s3_bucket_name:str,
        mongo_crud_chat_bot: MongoCRUD[FlowNode]
    ):
        self.chatbot_service = chat_bot_service
        self.business_service = business_service
        self.whatsapp_media_api = whatsapp_media_api
        self.s3_bucket_service = s3_bucket_service
        self.aws_region = aws_region
        self.aws_s3_bucket_name = aws_s3_bucket_name
        self.mongo_crud_chat_bot = mongo_crud_chat_bot
    
    async def execute(
        self,
        business_profile_id: str,
        request_body: DynamicChatBotRequest
    ) :
        chat_bot = await self.chatbot_service.get(
            request_body.chatbot_id, 
        )
        
        await self._delete_existing_flow_nodes(chat_bot_id=chat_bot.id)
        
        for node in request_body.nodes:
            domain_node : FlowNode = await self.dispatch_nodes(node, business_profile_id)
            domain_node.chat_bot_id = chat_bot.id
            await self.mongo_crud_chat_bot.create(domain_node)
        
        return ApiResponse.success_response(data=None,message="added successfully" ,status_code=204)
    
    async def dispatch_nodes(self, node: DynamicFlowNodeRequest,business_id : str) -> FlowNode:
        content_payload = None
        service_hook = None
        node_buttons = []
        
        if node.type == FlowNodeType.INTERACTIVE_BUTTONS:
            content_payload, node_buttons = await self._handle_interactive_buttons(node, business_id)
                    
        elif node.type == FlowNodeType.MESSAGE:
            content_payload = await self._handle_message_node(node, business_id)
                
        elif node.type == FlowNodeType.QUESTION:
            content_payload = await self._handle_question_node(node)
                
        elif node.type == FlowNodeType.OPERATION:
            service_hook = self._handle_operation_node(node)
            
        domain_node = FlowNode(
            id=node.id,
            type=node.type,
            buttons=node_buttons,
            body=content_payload, 
            is_final=node.is_final,
            is_first=node.is_first,
            next_nodes=node.next_nodes,
            position=node.position,
            service_hook=service_hook
        ) 
        
        return domain_node     

    async def _handle_interactive_buttons(
        self, 
        node: DynamicFlowNodeRequest, 
        business_id: str
    ) -> tuple[dict, list[dict]]:
    
        if not node.body or not node.body.body_button:
            raise ValueError("Interactive button node must have body_button")
    
        button_body: DynamicInteractiveMessageRequest = node.body.body_button
        content_payload = {"interactive_type": button_body.type.value, "whatsapp_interactive": {}}
        node_buttons = []
    
        whatsapp_interactive = {"type": button_body.type.value}
    
        if button_body.header:
            header_data = await self._build_interactive_header(button_body.header, business_id)
            whatsapp_interactive["header"] = header_data["whatsapp_header"]
            content_payload["header"] = header_data["header_metadata"]
    
        whatsapp_interactive["body"] = {"text": button_body.body.text}
        content_payload["body_text"] = button_body.body.text
    
        if button_body.footer:
            whatsapp_interactive["footer"] = {"text": button_body.footer.text}
            content_payload["footer_text"] = button_body.footer.text
    
        if button_body.action:
            if button_body.type == InteractiveType.BUTTON and button_body.action.buttons:
                whatsapp_buttons = []
                for idx, btn in enumerate(button_body.action.buttons):
                    reply_id = btn.reply.id
                    reply_title = btn.reply.title
                    next_node_id = btn.reply.next_node_id
    
                    whatsapp_buttons.append({
                        "type": "reply",
                        "reply": {
                            "id": reply_id,
                            "title": reply_title
                        }
                    })
    
                    node_buttons.append({
                        "type": "reply",
                        "id": reply_id,
                        "title": reply_title,
                        "next_node_id": next_node_id
                    })
    
                whatsapp_interactive["action"] = {"buttons": whatsapp_buttons}
    
            elif button_body.type == InteractiveType.LIST and button_body.action.sections:
                whatsapp_sections = []
                for section in button_body.action.sections:
                    whatsapp_rows = []
                    for row in section.rows:
                        whatsapp_row = {"id": row.id, "title": row.title}
                        if hasattr(row, "description") and row.description:
                            whatsapp_row["description"] = row.description
                        whatsapp_rows.append(whatsapp_row)
    
                        node_buttons.append({
                            "type": "list_reply",
                            "id": row.id,
                            "title": row.title,
                            "description": getattr(row, "description", None),
                            "section_title": getattr(section, "title", None),
                            "next_node_id": getattr(row, "next_node_id", None)
                        })
    
                    whatsapp_section = {"rows": whatsapp_rows}
                    if getattr(section, "title", None):
                        whatsapp_section["title"] = section.title
                    whatsapp_sections.append(whatsapp_section)
    
                whatsapp_interactive["action"] = {
                    "button": button_body.action.button or "Select an option",
                    "sections": whatsapp_sections
                }
    
        content_payload["whatsapp_interactive"] = whatsapp_interactive
        return content_payload, node_buttons


    async def _handle_message_node(
        self, 
        node: DynamicFlowNodeRequest, 
        business_id: str
    ) -> Dict[str, Any]:
        
        if not node.body or not node.body.body_message:
            raise ValueError("Message node must have body_message")
            
        message_body: MessageContentNodeRequest = node.body.body_message
        
        if not message_body.content_items:
            raise ValueError("MESSAGE node must include at least one content item")
    
        processed_content = {
            "content_items": [],
            "has_text": False,
            "has_media": False,
        }
        
        for item in message_body.content_items:
            processed_item = await self._process_content_item(item, business_id)
            processed_content["content_items"].append(processed_item)
            
            if item.type == MessageContentType.TEXT:
                processed_content["has_text"] = True
            else:
                processed_content["has_media"] = True
        
        return processed_content

    async def _process_content_item(
        self, 
        content_item: ContentItem, 
        business_id: str
    ) -> Dict[str, Any]:
        
        processed_item = {
            "type": content_item.type.value,
            "order": content_item.order,
        }
        
        if content_item.type == MessageContentType.TEXT:
            processed_item["content"] = {
                "text_body": content_item.content["text_body"]
            }
        else:
            try:
                media_content = await self._process_media_upload(
                    content_item.content, 
                    business_id
                )
                processed_item["content"] = media_content
                
            except Exception as e:
                raise ValueError(f"Failed to process {content_item.type.value} content: {str(e)}")
        
        return processed_item

    async def _handle_question_node(self, node: DynamicFlowNodeRequest) -> Dict[str, Any]:
        
        if not node.body or not node.body.body_question:
            raise ValueError("Question node must have body_question")
            
        question_body: QuestionContentNodeRequest = node.body.body_question
        
        return {
            "question_text": question_body.question_text,
            "answer_variant": question_body.answer_variant,
            "accept_media_response": question_body.accept_media_response
        }

    def _handle_operation_node(self, node: DynamicFlowNodeRequest) -> ServiceHook:
        
        if not node.service_hook:
            return None
            
        return ServiceHook(
            service_type=node.service_hook.service_type,
            service_action=node.service_hook.service_action,
            on_success=node.service_hook.on_success,
            on_failure=node.service_hook.on_failure
        )

    async def _build_interactive_header(
        self, 
        header: Any, 
        business_id: str
    ) -> Dict[str, Any]:
        
        if header.type == HeaderType.TEXT:
            return {
                "whatsapp_header": {
                    "type": "text",
                    "text": header.text
                },
                "header_metadata": {
                    "type": "text",
                    "text": header.text
                }
            }
        
        elif header.type == HeaderType.MEDIA:
            if not header.media:
                raise ValueError("Media header type requires media content")
            
            media_content = await self._process_media_upload(header.media, business_id)
            
            content_type = media_content["content_type"].lower()
            media_id = media_content["media_id"]
    
            if content_type == "image":
                whatsapp_header = {"type": "image", "image": {"id": media_id}}
            elif content_type == "video":
                whatsapp_header = {"type": "video", "video": {"id": media_id}}
            else:
                whatsapp_header = {
                    "type": "document",
                    "document": {"id": media_id, "filename": media_content["file_name"]}
                }
    
            header_metadata = {
                **media_content,  
                "type": content_type
            }
    
            return {
                "whatsapp_header": whatsapp_header,
                "header_metadata": header_metadata
            }
        
        else:
            raise ValueError(f"Unsupported header type: {header.type}")


    async def _process_media_upload(
        self, 
        media_content: Dict[str, Any], 
        business_id: str
    ) -> Dict[str, Any]:
        
        logger.debug(f"Processing media upload. Content keys: {list(media_content.keys())}")
        logger.debug(f"Media content structure: {type(media_content)}")
        
        if "base64_data" in media_content:
            try:
                logger.debug("Processing base64_data content")
                media_bytes = self._decode_base64_media(media_content["base64_data"])
                
            except Exception as e:
                logger.error(f"Failed to decode base64 media: {str(e)}")
                raise ValueError(f"Failed to decode base64 media: {str(e)}")
                
        elif "bytes" in media_content:
            logger.debug("Processing bytes content")
            media_bytes_content = media_content["bytes"]
            
            logger.debug(f"Bytes content type: {type(media_bytes_content)}")
            logger.debug(f"Bytes content value (first 100 chars if string): {str(media_bytes_content)[:100] if isinstance(media_bytes_content, str) else 'Not a string'}")
            
            if isinstance(media_bytes_content, BytesIO):
                logger.debug("Bytes content is already BytesIO")
                media_bytes = media_bytes_content
            elif isinstance(media_bytes_content, bytes):
                logger.debug("Converting raw bytes to BytesIO")
                media_bytes = BytesIO(media_bytes_content)
            elif isinstance(media_bytes_content, str):
                logger.debug("Processing string bytes content")

                try:
                    logger.debug("Attempting base64 decode of string")
                    decoded_bytes = b64decode(media_bytes_content)
                    media_bytes = BytesIO(decoded_bytes)
                    logger.debug("Successfully decoded string as base64")
                except Exception as base64_error:
                    logger.debug(f"Base64 decode failed: {base64_error}")
                    try:
                        logger.debug("Attempting UTF-8 encode of string")
                        media_bytes = BytesIO(media_bytes_content.encode('utf-8'))
                        logger.debug("Successfully encoded string as UTF-8")
                    except Exception as utf8_error:
                        logger.error(f"Failed to process string bytes content. Base64 error: {base64_error}, UTF-8 error: {utf8_error}")
                        raise ValueError(f"Failed to process string bytes content: base64 decode failed ({base64_error}), UTF-8 encode failed ({utf8_error})")
            elif hasattr(media_bytes_content, 'read'):
                logger.debug("Bytes content appears to be a file-like object")
                try:
                    if hasattr(media_bytes_content, 'seek'):
                        media_bytes_content.seek(0)
                    content = media_bytes_content.read()
                    media_bytes = BytesIO(content)
                    logger.debug("Successfully read from file-like object")
                except Exception as e:
                    logger.error(f"Failed to read from file-like object: {str(e)}")
                    raise ValueError(f"Failed to read from file-like object: {str(e)}")
            else:
                logger.error(f"Unsupported bytes content type: {type(media_bytes_content)}")
                raise ValueError(f"Unsupported bytes content type: {type(media_bytes_content)}. Expected BytesIO, bytes, string, or file-like object. Received: {type(media_bytes_content)}")
        else:
            logger.error(f"Media content missing both 'base64_data' and 'bytes' keys. Available keys: {list(media_content.keys())}")
            raise ValueError("Media content must contain either 'base64_data' or 'bytes'")
        
        mime_type = media_content.get("mime_type", "")
        file_name = media_content.get("file_name") or f"{uuid6.uuid7()}"
        
        logger.debug(f"File name: {file_name}, MIME type: {mime_type}")
        
        if "." not in file_name and mime_type:
            extension = mime_type.split("/")[-1]
            file_name = f"{file_name}.{extension}"
            logger.debug(f"Updated file name with extension: {file_name}")
            
        try:
            bytes_value = media_bytes.getvalue()
            logger.debug(f"Successfully retrieved bytes value. Length: {len(bytes_value)}")
        except Exception as e:
            logger.error(f"Failed to get bytes value: {str(e)}")
            raise ValueError(f"Failed to get bytes value from BytesIO: {str(e)}")
            
        upload_file = UploadFile(
            filename=file_name,
            file=io.BytesIO(bytes_value),  
        )
        
        business_profile = await self.business_service.get(business_id)
        
        try:
            logger.debug("Uploading media to WhatsApp")
            media_resp = await self.whatsapp_media_api.upload_media(
                business_profile.phone_number_id,
                business_profile.access_token,
                upload_file
            )
            
            media_id = media_resp["id"]
            logger.debug(f"WhatsApp media upload successful. Media ID: {media_id}")
        except Exception as e:
            logger.error(f"Failed to upload media to WhatsApp: {str(e)}")
            raise ValueError(f"Failed to upload media to WhatsApp: {str(e)}")
        
        content_type = mime_type.split('/')[0] if mime_type else "unknown"
        
        try:
            logger.debug("Uploading media to S3")
            upload_file.file.seek(0)
            
            s3_key = self.s3_bucket_service.upload_fileobj(
                upload_file.file, file_name=file_name
            )
            
            cdn_url = self.s3_bucket_service.get_cdn_url(s3_key)
            logger.debug(f"S3 upload successful. S3 key: {s3_key}, CDN URL: {cdn_url}")
        except Exception as e:
            logger.error(f"Failed to upload media to S3: {str(e)}")
            raise ValueError(f"Failed to upload media to S3: {str(e)}")
    
        result = {
            "cdn_url": cdn_url,
            "s3_key": s3_key,
            "media_id": media_id,
            "file_name": file_name,
            "content_type": content_type,
            "mime_type": mime_type
        }
        
        logger.debug(f"Media upload completed successfully: {result}")
        return result

    def _decode_base64_media(self, base64_data: str) -> BytesIO:

        try:
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',', 1)[1]
            
            decoded_bytes = b64decode(base64_data)
            return BytesIO(decoded_bytes)
            
        except Exception as e:
            raise ValueError(f"Failed to decode base64 data: {str(e)}")
        

    async def _delete_existing_flow_nodes(self, chat_bot_id: str) -> None:

        try:
            logger.debug(f"Starting deletion of existing flow nodes for chatbot {chat_bot_id}")
            
            existing_nodes = await self.mongo_crud_chat_bot.find_many({"chat_bot_id": chat_bot_id})
            
            if not existing_nodes:
                logger.debug(f"No existing flow nodes found for chatbot {chat_bot_id}")
                return
            
            logger.debug(f"Found {len(existing_nodes)} existing flow nodes to delete")
            
            s3_keys_to_delete = []
            
            for node in existing_nodes:
                s3_keys_from_node = self._extract_s3_keys_from_node(node)
                s3_keys_to_delete.extend(s3_keys_from_node)
            
            if s3_keys_to_delete:
                logger.debug(f"Deleting {len(s3_keys_to_delete)} S3 media files")
                await self._delete_s3_media_files(s3_keys_to_delete)
            
            delete_result = await self.mongo_crud_chat_bot.delete_many({"chat_bot_id": chat_bot_id})
            logger.debug(f"Deleted {delete_result.deleted_count if delete_result else 0} flow nodes from database")
            
            logger.debug("Successfully completed deletion of existing flow nodes and media")
            
        except Exception as e:
            logger.error(f"Error deleting existing flow nodes for chatbot {chat_bot_id}: {str(e)}")

    def _extract_s3_keys_from_node(self, node: FlowNode) -> List[str]:
        s3_keys = []
    
        try:
            if not node.body:
                return s3_keys
    
            content_items = node.body.get("content_items", [])
            for item in content_items:
                if item.get("type") in ["image", "video", "document", "audio"]:
                    content = item.get("content", {})
                    s3_key = content.get("s3_key")
                    if s3_key:
                        s3_keys.append(s3_key)
    
            header_meta = node.body.get("header", {})
            if isinstance(header_meta, dict):
                s3_key = header_meta.get("s3_key")
                if s3_key:
                    s3_keys.append(s3_key)
    
        except Exception as e:
            logger.error(f"Error extracting S3 keys from node {getattr(node, 'id', None)}: {str(e)}")
    
        return s3_keys
    
    async def _delete_s3_media_files(self, s3_keys: List[str]) -> None:
        for s3_key in s3_keys:
            try:
                logger.debug(f"Deleting S3 file: {s3_key}")
                self.s3_bucket_service.delete_file(s3_key)
                logger.debug(f"Successfully deleted S3 file: {s3_key}")
            except Exception as e:
                logger.error(f"Failed to delete S3 file {s3_key}: {str(e)}")
                continue