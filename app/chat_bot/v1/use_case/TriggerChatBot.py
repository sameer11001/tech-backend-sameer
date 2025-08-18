from app.chat_bot.services.ChatBotService import ChatBotService



class TriggerChatBot:
    def __init__(self, chatbot_service: ChatBotService):
        pass
    
    async def execute(conversation_id: str, chatbot_id: str):
        ##TODO: check if conversation_id is valid and chatbot_id is valid
        pass