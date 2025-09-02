from fastapi import logger
from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.request.TriggerChatBotRequest import TriggerChatBotRequest
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.BaseResponse import ApiResponse
from app.events.pub.ChatBotTriggerPublisher import ChatBotTriggerPublisher
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.services.ConversationService import ConversationService



class TriggerChatBot:
    def __init__(
        self, 
        chat_bot_service: ChatBotService, 
        conversation_service: ConversationService,
        trigger_publisher:ChatBotTriggerPublisher,
        business_service: BusinessProfileService,
        contact_service : ContactService
        ):
        self.chat_bot_service = chat_bot_service
        self.conversation_service = conversation_service
        self.trigger_publisher = trigger_publisher
        self.business_service = business_service
        self.contact_service = contact_service
    
    async def execute(self,business_profile_id: str,request_body: TriggerChatBotRequest):
        try:
            business_profile : BusinessProfile = await self.business_service.get(business_profile_id)
            
            conversation : Conversation = await self.conversation_service.get(request_body.conversation_id)
            chat_bot : ChatBotMeta = await self.chat_bot_service.get(request_body.chat_bot_id)
            
            contact : Contact = await self.contact_service.get_by_business_profile_and_contact_number(business_profile.phone_number, request_body.recipient_number)
            
            publisher_data = {
                "chatbot_id": str(chat_bot.id),
                "conversation_id": str(conversation.id),
                "recipient_number": request_body.recipient_number,
                "business_phone_number_id": business_profile.phone_number_id,
                "business_token": business_profile.access_token,
                "contact_id": str(contact.id)
            }
            
            await self.trigger_publisher.trigger_chatbot_event(data_body=publisher_data)

            await self.conversation_service.update(
                conversation.id, 
                {"chatbot_triggered": True},
                commit=False
            )
            
            current_triggered = chat_bot.triggered if chat_bot.triggered else 0
            await self.chat_bot_service.update(
                chat_bot.id, 
                {"triggered": current_triggered + 1}
            )
            

            
            return ApiResponse(message="Chatbot triggered successfully", status_code=204)
        except Exception as e:
            raise GlobalException(str(e))