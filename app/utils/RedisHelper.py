class RedisHelper:
    ############################################ app
    @staticmethod
    def redis_refresh_token_key(hashed_token: str) -> str:
        return f"auth:refresh_token:{{{hashed_token}}}"
    
    @staticmethod
    def redis_roles() -> str:
        return f"auth_roles"
    
    @staticmethod
    def redis_client_buiness_data_key(client_id: str) -> str:
        return f"auth:client:{{{client_id}}}:business_profile_data"
    
    @staticmethod
    def redis_user_data_key(user_id: str) -> str:
        return f"auth:user:data:{{{user_id}}}"
    
    @staticmethod
    def redis_user_info_key(user_id: str) -> str:
        return f"auth:user:info:{{{user_id}}}"
    
    ############################################## conversation and team inbox
    @staticmethod
    def redis_team_online_key(team_id: str) -> str:
        return f"teaminbox:conversation_teams_online:{{{team_id}}}"
    
    @staticmethod
    def redis_conversation_expired_key(conversation_id: str) -> str:
        return f"teaminbox:conversation:{{{conversation_id}}}:closed_session"
    
    @staticmethod
    def redis_conversation_last_message_key(conversation_id: str) -> str:
        return f"teaminbox:conversation:{{{conversation_id}}}:last_message"
    
    @staticmethod
    def redis_conversation_last_message_data(last_message: str,last_message_time: str) -> dict:
        return {"last_message": last_message, "last_message_time": last_message_time}
    
    ############################################## broadcast
    
    @staticmethod
    def redis_broadcast_schedule_key(broadcast_id: str) -> str:
        return f"broadcast:{{{broadcast_id}}}:schedule"
    
    @staticmethod
    def redis_broadcast_data_key(broadcast_id: str) -> str:
        return f"broadcast:{{{broadcast_id}}}:data"
    
    @staticmethod
    def redis_broadcast_list_of_numbers_key(broadcast_id: str) -> str:
        return f"broadcast:{{{broadcast_id}}}:contact_list"
    
    ############################################## socket
    
    @staticmethod
    def redis_business_phone_number_id_key(business_profile_id: str) -> str:
        return f"business_phone_number_id:{{{business_profile_id}}}"
    
    @staticmethod
    def redis_socket_user_session_key(sid: str) -> str:
        return f"chat:user:user_info:{{{sid}}}"
    
    @staticmethod
    def redis_session_business_key(sid: str) -> str:
        return f"chat:business_group:user_sid:{{{sid}}}"
    
    @staticmethod
    def redis_socket_user_id_session_key(user_id: str) -> str:
        return f"chat:user:sid:{{{user_id}}}"
    
    @staticmethod
    def redis_buiness_group_user_session_key(phone_number_id: str, sid: str) -> str:
        return f"chat:business_group:{{{phone_number_id}}}:user_sid:{sid}"
    
    @staticmethod
    def redis_business_members_key(phone_number_id: str) -> str:
        return f"chat:business_group:{{{phone_number_id}}}:members"
    
    @staticmethod
    def redis_business_room_key(phone_number_id: str) -> str:
        return f"chat:business_group:{{{phone_number_id}}}:room"
    
    @staticmethod
    def redis_conversation_members_key(conversation_id: str) -> str:
        return f"chat:conversation:{{{conversation_id}}}:members"
    
    @staticmethod
    def redis_conversation_room_key(conversation_id: str) -> str:
        return f"chat:conversation:{{{conversation_id}}}:room"
    
    @staticmethod
    def redis_conversation_user_session_key(conversation_id: str, sid: str) -> str:
        return f"chat:conversation:{{{conversation_id}}}:user_sid:{{{sid}}}"
    
    @staticmethod
    def redis_conversation_messages_stream_key(conversation_id: str) -> str:
        return f"chat:conversation:{{{conversation_id}}}:messages_stream"
    
    @staticmethod
    def redis_business_conversation_unread_key(conversation_id: str) -> str:
        return f"chat:conversation:{{{conversation_id}}}:unread"
    
    ############################################## chatbot
    
    @staticmethod
    def redis_chatbot_context_key(conversation_id: str) -> str:
        return f"chatbot_context:conversation:{conversation_id}"
    
    @staticmethod
    def redis_chatbot_button_key(chatbot_id: str, current_node_id: str, btn_id: str) -> str:
        return  f"chatbot:{chatbot_id}:node:{current_node_id}:buttons:{btn_id}"
    
    @staticmethod
    def redis_chatbot_contact_data_key(conversation_id: str) -> str:
        return f"chatbot:contact_data:conversation:{conversation_id}"
    