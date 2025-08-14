from typing import List
from app.chat_bot.models.ChatBot import ChatBot
from app.chat_bot.models.ChatBot import FlowNode, ServiceHook
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.repository.MongoRepository import MongoCRUD
from app.utils.enums.InteractiveMessageEnum import InteractiveType
from app.utils.validators.validate_interactive_message import InteractiveMessageValidator
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService


class CreateChatBot:
    def __init__(
        self,
        chatbot_service: ChatBotService,
        business_service: BusinessProfileService,
        mongo_crud_chat_bot: MongoCRUD[ChatBot]
    ):
        self.chatbot_service = chatbot_service
        self.business_service = business_service

    async def execute(
        self,
        business_id: str,
        request_body: DynamicChatBotRequest
    ) -> ChatBotMeta:
        business_profile = await self.business_service.get(business_id)
        client_id = business_profile.client_id

        await self.chatbot_service.get_by_name(
            request_body.name,
            client_id,
            should_exist=False
        )

        validation_errors = []
        for node in request_body.nodes:
            if hasattr(node, 'type') and node.type == InteractiveType.BUTTON or node.type == InteractiveType.LIST:
                dynamic_interactive = DynamicInteractiveMessageRequest(
                    type=node.type,
                    header=node.text.get('header') if node.text else None,
                    body=node.text,
                    footer=node.text.get('footer') if node.text else None,
                    action=node.buttons or {}
                )
                validation_errors = InteractiveMessageValidator.validate_interactive_message(dynamic_interactive)
                if validation_errors:
                    raise ValueError(f"Validation failed for interactive node '{node.name}': {validation_errors}")

        domain_nodes: List[FlowNode] = []
        for node in request_body.nodes:
            svc = None
            if node.service_hook:
                svc = ServiceHook(
                    type=node.service_hook.service_type,
                    action=node.service_hook.service_action,
                    on_success=node.service_hook.on_success,
                    on_failure=node.service_hook.on_failure
                )

            domain_nodes.append(
                FlowNode(
                    id=node.name,
                    type=node.type.value,
                    text=node.text,
                    buttons=node.buttons,
                    body=node.body,
                    name=node.name,
                    is_final=node.is_final,
                    service=svc,
                    next_nodes=node.next_nodes or [],
                    position=node.position
                )
            )

        first_node = next(n for n in request_body.nodes if n.is_first)
        first_node_id = first_node.name

        chatbot_meta = ChatBotMeta(
            name=request_body.name,
            client_id=client_id,
            version=request_body.version,
            language=request_body.language,
            schema_version=1,
            first_node_id=first_node_id,
            total_nodes=len(domain_nodes)
        )

        created = await self.chatbot_service.create(chatbot_meta)
        
        chat_bot_document = ChatBot(
            id=created.id,
            name=created.name,
            version=created.version,
            default_locale=created.default_locale,
            schema_version=created.schema_version,
            nodes=domain_nodes,
            first_node_id=first_node_id,
            total_nodes=len(domain_nodes),
            created_at=created.created_at,
            updated_at=created.updated_at
        )
        
        return created