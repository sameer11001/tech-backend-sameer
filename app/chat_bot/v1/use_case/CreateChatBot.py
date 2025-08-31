from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.request.CreateChatBotRequest import CreateChatBotRequest
from app.chat_bot.models.schema.response.CreateChatBotResponse import CreateChatBotResponse
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.schemas.BaseResponse import ApiResponse
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService


class CreateChatBot:
    def __init__(
        self,
        chat_bot_service: ChatBotService,
        business_service: BusinessProfileService,
    ):
        self.chatbot_service = chat_bot_service
        self.business_service = business_service

    
    async def execute(
        self,
        business_profile_id: str,
        request_body: CreateChatBotRequest
    ) -> ChatBotMeta:
        business_profile : BusinessProfile = await self.business_service.get(business_profile_id)
        client_id = business_profile.client_id

        await self.chatbot_service.get_by_name(
            request_body.name,
            client_id,
            should_exist=False
        )

        chatbot_meta = ChatBotMeta(
            name=request_body.name,
            client_id=client_id,
            version=request_body.version,
            language=request_body.language
        )

        created = await self.chatbot_service.create(chatbot_meta)
        
        response_body = CreateChatBotResponse(
            id=str(created.id),
            name=created.name,
            version=created.version,
            communicate_type=created.communicate_type,
            created_at=created.created_at.isoformat(),
            updated_at=created.updated_at.isoformat()
        )

        return ApiResponse.success_response(data=response_body)