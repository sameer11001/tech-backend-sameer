from asyncio.log import logger
from uuid import UUID
from app.chat_bot.models.ChatBot import FlowNode
from app.chat_bot.models.schema.response.ChatBotFlowResponse import GetChatBotFlowResponse
from app.chat_bot.models.schema.response.FlowNodeResponseBuilder import FlowNodeResponseBuilder
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse


class GetChatBotFlow:
    def __init__(self, chat_bot_service: ChatBotService, mongo_crud_chat_bot_flow: MongoCRUD[FlowNode]):
        self.chat_bot_service = chat_bot_service
        self.mongo_crud_chat_bot_flow = mongo_crud_chat_bot_flow
        self.flow_node_response_builder = FlowNodeResponseBuilder()
        
    async def execute(self, chat_bot_id: str) -> GetChatBotFlowResponse:
        chatbot = await self.chat_bot_service.get(chat_bot_id)
        
        flow_nodes = await self.mongo_crud_chat_bot_flow.find_many({"chat_bot_id": UUID(chat_bot_id)})
        
        logger.debug(f"Found {flow_nodes} flow nodes for chatbot {chat_bot_id}")
        
        response = self.flow_node_response_builder.build_complete_flow_response(
            chatbot=chatbot,
            nodes=flow_nodes
        )
        
        return ApiResponse.success_response(data=response,message= "success" ,status_code=200)
        