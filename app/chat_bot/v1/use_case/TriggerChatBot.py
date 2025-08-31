from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.request.TriggerChatBotRequest import TriggerChatBotRequest
from app.chat_bot.services.ChatBotService import ChatBotService
from app.events.pub.ChatBotTriggerPublisher import ChatBotTriggerPublisher
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.services.ConversationService import ConversationService



class TriggerChatBot:
    def __init__(
        self, 
        chat_bot_service: ChatBotService, 
        conversation_service: ConversationService,
        trigger_publisher:ChatBotTriggerPublisher
        ):
        self.chat_bot_service = chat_bot_service
        self.conversation_service = conversation_service
        self.trigger_publisher = trigger_publisher
    
    async def execute(self,request_body: TriggerChatBotRequest):
        conversation : Conversation = await self.conversation_service.get(request_body.conversation_id)
        chat_bot : ChatBotMeta = await self.chat_bot_service.get(request_body.chatbot_id)
        
        await self.trigger_publisher.trigger_chatbot_event(conversation.id, chat_bot.id, conversation.recipient_number)
        
        
        
        