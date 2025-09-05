from app.chat_bot.v1.use_case.TriggerChatBot import TriggerChatBot
from app.core.config.container_imports import *

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            'app.user_management.user.v1.controllers.UserController',
            'app.user_management.auth.v1.controllers.AuthController',
            'app.user_management.user.v1.controllers.TeamController',
            'app.whatsapp.business_profile.v1.controller.BusinessProfileController',
            'app.whatsapp.template.v1.controller.TemplateController',
            'app.whatsapp.media.v1.controller.WhatsappMediaController',
            'app.annotations.v1.controllers.AttributeController',
            'app.annotations.v1.controllers.ContactController',
            'app.annotations.v1.controllers.TagController',
            'app.whatsapp.team_inbox.v1.controllers.MessageController',
            'app.whatsapp.broadcast.controller.BroadCastController',
            'app.real_time.webhook.controller.WebhookController',
            'app.whatsapp.team_inbox.v1.controllers.TeamInboxController',
            'app.core.exceptions.ErrorHandler',
            'app.core.controllers.BaseController',
            'app.annotations.v1.controllers.NoteController',
            'app.chat_bot.v1.controllers.ChatBotController',
            'app.events.app_events_route',
            'app.events.sub.ChatBotReplyEvent'
        ]
    )
    
    #----- CONFIG -----
    config = providers.Configuration()
    config.from_pydantic(Settings())
    
    socket_redis_manager = providers.Singleton(
        AsyncRedisManager,
        url = config.CACHE_URL,
        write_only=False,
    )
    
    #----- socket -----
    sio: AsyncServer= providers.Singleton(
        AsyncServer,
        async_mode="asgi",
        client_manager=socket_redis_manager,
        cors_allowed_origins=["https://dev.prog-gate.cloud","http://localhost:4200"],
        transports=['websocket', 'polling'], 
        
        logger=False, 
        engineio_logger=False, 
        
        ping_timeout=60,
        ping_interval=25,        
    )
    
    #----- AWS Config -----
    boto_config = providers.Singleton(
        BotoConfig,
        region_name=config.AWS_REGION,
        signature_version='v4',
        retries={'max_attempts': 5, 'mode': 'standard'}
    )
    
    aws_session = providers.Singleton(
        boto3.Session,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION
    )
    
    s3_bucket_client = providers.Singleton(
        lambda session, boto_cfg: session.client('s3', config=boto_cfg),
        session=aws_session,
        boto_cfg=boto_config
    )
    transfer_config = providers.Singleton(
        TransferConfig,
        multipart_threshold=1024 * 25,
        max_concurrency=10,
        multipart_chunksize=1024 * 25,
        num_download_attempts=5,
        max_io_queue=100,
        use_threads=True
    )
    
    s3_bucket_service = providers.Factory(
        S3Service,
        s3_client=s3_bucket_client,
        bucket_name=config.S3_BUCKET_NAME,
        transfer_config=transfer_config,
        aws_region=config.AWS_REGION,
        aws_s3_bucket_name=config.S3_BUCKET_NAME
    )
    
    #----- STORAGE Config -----
    psql = providers.Singleton(PostgresDatabase, db_url = config.POSTGRES_DATABASE_URL)
    session = providers.Factory(
        lambda db_instance: db_instance.create_session(),        
        db_instance=psql
    )

    http_client = providers.Singleton(httpx.AsyncClient, timeout=120)

    mongo_db = providers.Singleton(MongoDB, db_url = config.MONGO_URI, db_name = config.MONGO_DB)
    
    mongo_init_context = providers.Resource(
        lambda mongo_db: mongo_db.init_db([Message, Template, FlowNode, Logger]),
        mongo_db=mongo_db,
    )
    mongo_crud_message = providers.Singleton(MongoCRUD, model = Message) 
    mongo_crud_template = providers.Singleton(MongoCRUD, model = Template) 
    mongo_crud_chat_bot = providers.Singleton(MongoCRUD, model=FlowNode)
    mongo_crud_logger = providers.Singleton(MongoCRUD, model=Logger)
    
    log_crud = providers.Singleton(LogCRUD)
    
    rabbitmq_settings = providers.Singleton(
        RabbitMQSettings,
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        username=config.RABBITMQ_DEFAULT_USER,
        password=config.RABBITMQ_DEFAULT_PASS,
        vhost=config.RABBITMQ_VHOST,
    )
    
    rabbitmq_connection = providers.Singleton(
        RabbitMQBroker,
        settings=rabbitmq_settings
    )
    
    async_redis_service = providers.Resource(
        AsyncRedisService,
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=None,
        namespace="",
        default_ttl=config.REDIS_TTL,
        use_msgpack=True,
        
    )
    
    #----- pub/sub -----
    message_publisher = providers.Singleton(WhatsappMessagePublisher, connection=rabbitmq_connection)
    message_broadcast_publisher = providers.Singleton(MessageBroadcastPublisher, connection=rabbitmq_connection)
    chat_bot_trigger_publisher = providers.Singleton(ChatBotTriggerPublisher, connection=rabbitmq_connection)
    chat_bot_flow_publisher = providers.Singleton(ChatbotFlowPublisher, connection=rabbitmq_connection)
    message_hook_received_publisher = providers.Singleton(MessageHookReceivedPublisher, connection=rabbitmq_connection)
    system_logs_publisher = providers.Singleton(SystemLogsPublisher, connection=rabbitmq_connection)
    test_publisher = providers.Singleton(TestPublisher, connection=rabbitmq_connection)
    
    #----- REPOSITORIES -----
    user_repository = providers.Factory(UserRepository, session= session)
    team_repository = providers.Factory(TeamRepository, session= session)
    client_repository = providers.Factory(ClientRepository, session= session)
    refresh_token_repository = providers.Factory(RefreshTokenRepository, session= session)
    role_repository = providers.Factory(RoleRepository, session= session)
    business_profile_repository = providers.Factory(BusinessProfileRepository, session= session)
    tag_repository = providers.Factory(TagRepository, session= session)
    attribute_repository = providers.Factory(AttributeRepository, session= session)
    contact_repository = providers.Factory(ContactRepository, session= session)
    message_repository = providers.Factory(MessageRepository, session= session)
    template_repository = providers.Factory(TemplateRepository, session= session)
    conversation_repository = providers.Factory(ConversationRepository, session= session)
    assignment_repository = providers.Factory(AssignmentRepository, session= session)
    broadcast_repository = providers.Factory(BroadcastRepository, session= session)
    note_repository = providers.Factory(NoteRepository, session= session)
    chat_bot_repository = providers.Factory(ChatBotRepository, session= session)
    
    #----- SERVICES -----
    user_service = providers.Factory(UserService, repository = user_repository)
    client_service = providers.Factory(ClientService, repository = client_repository)
    team_service = providers.Factory(TeamService, repository = team_repository)
    role_service = providers.Factory(RoleService, repository = role_repository)
    refresh_token_service = providers.Factory(RefreshTokenService, repository = refresh_token_repository)
    business_profile_service = providers.Factory(BusinessProfileService, repository = business_profile_repository)
    tag_service = providers.Factory(TagService, repository = tag_repository)
    attribute_service = providers.Factory(AttributeService, repository = attribute_repository)
    contact_service = providers.Factory(ContactService, repository = contact_repository)
    message_service = providers.Factory(MessageService, repository = message_repository)
    template_service = providers.Factory(TemplateService, repository = template_repository)
    conversation_service = providers.Factory(ConversationService, repository = conversation_repository)
    assignment_service = providers.Factory(AssignmentService, repository = assignment_repository)
    broadcast_service = providers.Factory(BroadcastService, repository = broadcast_repository)
    note_service = providers.Factory(NoteService, repository = note_repository)
    chat_bot_service = providers.Factory(ChatBotService, repository = chat_bot_repository)
    chat_bot_context_service = providers.Singleton(ChatbotContextService, redis_service = async_redis_service)
    system_log_service = providers.Singleton(SystemLogService, log_publisher = system_logs_publisher)

    http_client = providers.Singleton(
        EnhancedHTTPClient,
        client=http_client,
        log_service=system_log_service  
    )
    #----- API -----
    business_profile_api = providers.Singleton(BusinessProfileApi, client = http_client)
    whatsapp_template_api = providers.Singleton(WhatsAppTemplateApi, client = http_client)
    whatsapp_media_api = providers.Singleton(WhatsAppMediaApi, client = http_client)
    whatsapp_message_api = providers.Singleton(WhatsAppMessageApi, client = http_client)
    
    #-------------- USE CASES --------------
    
    #----- Socket ------
    socket_message_gateway = providers.Singleton(
        SocketMessageGateway,
        sio=sio,
        redis=async_redis_service,
        business_profile_service=business_profile_service
    )   
    
    #----- USER USE CASES -----
    user_create_user = providers.Factory(CreateUser, user_service = user_service, team_service = team_service, role_service = role_service)
    user_create_team = providers.Factory(CreateTeam, team_service = team_service, user_service = user_service)
    user_delete_user_by_id = providers.Factory(DeleteUserById, user_service = user_service, redis_service = async_redis_service)
    user_edit_user = providers.Factory(EditUser, user_service = user_service, role_service = role_service, team_service = team_service, redis_service = async_redis_service)
    user_get_teams = providers.Factory(GetTeams, team_service = team_service, user_service = user_service)
    user_get_user_info = providers.Factory(GetUserInfo, user_service = user_service, redis_service = async_redis_service)
    user_get_user_by_client_id = providers.Factory(GetUsersByClientId, user_service = user_service, client_service = client_service)
    user_delete_team_by_team_name = providers.Factory(DeleteTeam, team_service = team_service, user_service = user_service)
    user_team_edit_team = providers.Factory(EditTeam, team_service = team_service, user_service = user_service)
    
    #----- AUTH USE CASES -----
    auth_user_login = providers.Factory(UserLogin, user_service = user_service, refresh_token_service = refresh_token_service, client_service = client_service, business_profile_service = business_profile_service)
    auth_user_logout = providers.Factory(UserLogout, refresh_token_service = refresh_token_service)
    auth_token_refresh = providers.Factory(TokenRefresh, refresh_token_service = refresh_token_service, user_service = user_service, business_profile_service = business_profile_service, redis_service = async_redis_service)
    auth_get_roles = providers.Factory(GetRoles, role_service = role_service, redis_service = async_redis_service)
    auth_force_logout_by_admin = providers.Factory(ForceLogoutByAdmin, user_service = user_service , refresh_token_service = refresh_token_service)
    auth_force_password_reset_by_admin = providers.Factory(ForcePasswordResetByAdmin, user_service = user_service)
    
    #----- BUSINESS PROFILE USE CASES -----
    business_profile_get_business_profile = providers.Factory(GetBusinessProfile, business_profile_api = business_profile_api, user_service = user_service, business_profile_service = business_profile_service)
    business_profile_update_business_profile = providers.Factory(UpdateBusinessProfile, business_profile_api = business_profile_api, user_service = user_service, business_profile_service = business_profile_service)
    business_profile_create_upload_session = providers.Factory(CreateUploadSession, business_profile_api = business_profile_api, user_service = user_service, business_profile_service = business_profile_service)
    business_profile_upload_file_data = providers.Factory(UploadFileData, business_profile_api = business_profile_api, user_service = user_service, business_profile_service = business_profile_service)
    business_profile_update_profile_picture = providers.Factory(UpdateProfilePicture, business_profile_api = business_profile_api, user_service = user_service, business_profile_service = business_profile_service)
    
    #----- TAG USE CASES -----
    tag_create_tag = providers.Factory(CreateTag, tag_service = tag_service, user_service = user_service, contact_service = contact_service)
    tag_delete_tag = providers.Factory(DeleteTag, tag_service = tag_service, user_service = user_service)
    tag_get_tags = providers.Factory(GetTags, tag_service = tag_service, user_service = user_service)
    tag_update_tag = providers.Factory(UpdateTag, tag_service = tag_service, user_service = user_service)
    tag_get_tag_by_contact = providers.Factory(GetTagByContact, tag_service = tag_service)
    
    #----- WHATSAPP TEMPLATE USE CASES -----
    whatsapp_template_get_templates = providers.Factory(GetTemplates, user_service = user_service,template_mongo_crud = mongo_crud_template)
    whatsapp_template_create_template = providers.Factory(CreateTemplate, whatsapp_template_api = whatsapp_template_api, user_service = user_service, business_profile_service = business_profile_service , mongo_crud = mongo_crud_template, template_service = template_service)
    whatsapp_template_delete_template = providers.Factory(DeleteTemplate, whatsapp_template_api = whatsapp_template_api, user_service = user_service, business_profile_service = business_profile_service, template_service = template_service, mongo_crud = mongo_crud_template)
    
    #----- WHATSAPP MEDIA USE CASES -----
    whatsapp_media_download_media = providers.Factory(DownloadMedia, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service)
    whatsapp_media_retrieve_media_url = providers.Factory(RetrieveMediaUrl, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service)
    whatsapp_media_upload_media = providers.Factory(UploadMedia, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service, s3_bucket_service = s3_bucket_service, aws_region = config.AWS_REGION, aws_s3_bucket_name = config.S3_BUCKET_NAME)
    whatsapp_media_delete_media = providers.Factory(DeleteMedia, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service)
    whatsapp_media_create_upload_session = providers.Factory(CreateSession, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service)
    whatsapp_media_upload_file_data = providers.Factory(UploadFileSession, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service)
    
    
    #----- MESSAGE USE CASES -----
    get_conversation_messages = providers.Factory(GetConversationMessages, conversation_service = conversation_service,user_service = user_service, mongo_crud = mongo_crud_message)
    whatsapp_message_text_message = providers.Factory(TextMessage, whatsapp_message_api=whatsapp_message_api, user_service=user_service, business_profile_service=business_profile_service, message_service=message_service, conversation_service=conversation_service,contact_service=contact_service,redis_service=async_redis_service,mongo_crud=mongo_crud_message)  
    whatsapp_message_template_message = providers.Factory(TemplateMessage, whatsapp_message_api=whatsapp_message_api, user_service=user_service, business_profile_service=business_profile_service, template_service=template_service, conversation_service=conversation_service,contact_service=contact_service,assignment_service=assignment_service,redis_service=async_redis_service,mongo_crud_message=mongo_crud_message, mongo_crud_template=mongo_crud_template, message_service=message_service)
    whatsapp_message_media_message = providers.Factory(MediaMessage, whatsapp_message_api = whatsapp_message_api, whatsapp_media_api = whatsapp_media_api, user_service = user_service, business_profile_service = business_profile_service, message_service = message_service, conversation_service = conversation_service, contact_service = contact_service, assignment_service = assignment_service, s3_bucket_service = s3_bucket_service, aws_region = config.AWS_REGION, aws_s3_bucket_name = config.S3_BUCKET_NAME, redis_service = async_redis_service ,mongo_crud = mongo_crud_message)
    whatsapp_message_reply_with_reaction = providers.Factory(ReplyWithReactionMessage, whatsapp_message_api = whatsapp_message_api, user_service = user_service, business_profile_service = business_profile_service, contact_service = contact_service, conversation_service = conversation_service,message_service = message_service, mongo_crud = mongo_crud_message, redis_service = async_redis_service)
    whatsapp_message_location_message = providers.Factory(LocationMessage, whatsapp_message_api = whatsapp_message_api, user_service = user_service, business_profile_service = business_profile_service, redis_service = async_redis_service, contact_service = contact_service, message_service = message_service, mongo_crud = mongo_crud_message, conversation_service = conversation_service)
    
    #----- Team Inbox USE CASES -----
    get_conversations = providers.Factory(GetUserConversations, conversation_service = conversation_service, user_service = user_service, contact_service = contact_service, message_service = message_service, redis = async_redis_service)
    create_new_conversation = providers.Factory(CreateNewConversation, conversation_service = conversation_service, contact_service = contact_service, client_service = client_service, team_service = team_service, user_service = user_service, message_service = message_service, whatsapp_message_api = whatsapp_message_api, assignment_service = assignment_service, business_profile_service = business_profile_service, mongo_crud = mongo_crud_message, mongo_template = mongo_crud_template, redis_service = async_redis_service)
    update_conversation_status = providers.Factory(UpdateConversationStatus, conversation_service = conversation_service, socket_gateway = socket_message_gateway)
    assigned_user_to_conversation = providers.Factory(AssignedUserToConversation, conversation_service = conversation_service, user_service = user_service, message_crud = mongo_crud_message, message_service = message_service, assignment_service = assignment_service, socket_gateway = socket_message_gateway)

    #----- Notes -----
    note_create_note = providers.Factory(CreateNote, note_service = note_service, user_service = user_service, contact_service = contact_service)
    note_get_notes_by_contact_id = providers.Factory(GetNoteByContact, note_service = note_service)
    note_update_note = providers.Factory(UpdateNote, note_service = note_service, user_service = user_service)
    note_delete_note = providers.Factory(DeleteNote, note_service = note_service, user_service = user_service, contact_service = contact_service)
    
    #----- Attributes -----
    attribute_create_attribute = providers.Factory(CreateAttribute, attribute_service = attribute_service, user_service = user_service, contact_service = contact_service)
    attribute_delete_attribute = providers.Factory(DeleteAttribute, attribute_service = attribute_service, user_service = user_service)
    attribute_get_attributes = providers.Factory(GetAttributes, attribute_service = attribute_service, user_service = user_service)
    attribute_update_attribute = providers.Factory(UpdateAttribute, attribute_service = attribute_service, user_service = user_service)
    attribute_get_attributes_by_contact = providers.Factory(GetAttributesByContact, attribute_service = attribute_service)
    attribute_delete_attribute_by_contact = providers.Factory(DeleteAttributeByContact, attribute_service = attribute_service, user_service = user_service)
    attribute_update_attribute_by_contact = providers.Factory(UpdateAttributeByContact, attribute_service = attribute_service, user_service = user_service)
    #----- Contacts -----
    contact_create_contact = providers.Factory(CreateContact, contact_service = contact_service, user_service = user_service, attribute_service = attribute_service)
    contact_delete_contact = providers.Factory(DeleteContact, user_service = user_service, contact_service = contact_service)
    contact_get_contacts = providers.Factory(GetContacts, contact_service = contact_service, user_service = user_service)
    contact_update_contact = providers.Factory(UpdateContact, contact_service = contact_service, user_service = user_service, attribute_service = attribute_service, tag_service = tag_service)
    
    #----- BroadCast -----
    broadcast_get_broadcasts = providers.Factory(GetBroadcasts, broadcast_service = broadcast_service, business_profile_service = business_profile_service)
    broadcast_schedule_broadcast = providers.Factory(BroadcastScheduler, broadcast_service = broadcast_service, user_service = user_service,contact_service = contact_service,bussiness_service = business_profile_service, redis = async_redis_service, message_publisher = message_broadcast_publisher, mongo_crud_template = mongo_crud_template) 
    broadcast_cancel_broadcast = providers.Factory(CancelBroadcast, broadcast_service = broadcast_service, redis_service = async_redis_service)
    broadcast_broadcast_config = providers.Singleton(BroadcastConfig,redis_service = async_redis_service, broadcast_scheduler = broadcast_schedule_broadcast)
    
    #----- Operations -----
    save_message_document = providers.Factory(SaveMessage, message_service = message_service,message_repo = mongo_crud_message, redis_service = async_redis_service)

   
    #----- RealTime -----
    template_hook = providers.Singleton(TemplateHook, template_service = template_service, client_service = client_service, business_profile_service = business_profile_service, mongo_crud = mongo_crud_template, wa_template_api = whatsapp_template_api)
    message_hook = providers.Singleton(
        MessageHook, 
        message_service = message_service,
        conversation_service = conversation_service, 
        save_message = save_message_document, 
        contact_service = contact_service, 
        client_service = client_service, 
        assignment_service = assignment_service,
        team_service = team_service, 
        business_profile_service = business_profile_service ,
        message_publisher = message_publisher, 
        chatbot_context_service = chat_bot_context_service, 
        chatbot_flow_publisher = chat_bot_flow_publisher, 
        media_api = whatsapp_media_api,
        redis_service = async_redis_service,
        mongo_message = mongo_crud_message,
        mongo_flow = mongo_crud_chat_bot,
        socket_message = socket_message_gateway, 
        s3_service = s3_bucket_service,
        message_hook_received_publisher = message_hook_received_publisher, 
        aws_s3_bucket = config.S3_BUCKET_NAME, 
        aws_region = config.AWS_REGION
        )
    webhook_dispatcher = providers.Factory(WebhookDispatcher, message_hook = message_hook, template_hook = template_hook)
    
    #----- ChatBot -----
    chat_bot_create_chat_bot = providers.Factory(CreateChatBot, chat_bot_service = chat_bot_service, business_service = business_profile_service)
    chat_bot_delete_chat_bot = providers.Factory(DeleteChatBot, chat_bot_service = chat_bot_service, user_service = user_service,mongo_crud_chat_bot = mongo_crud_chat_bot, s3_bucket_service = s3_bucket_service)
    chat_bot_add_flow_node = providers.Factory(AddFlowNode, chat_bot_service = chat_bot_service, business_service = business_profile_service,whatsapp_media_api = whatsapp_media_api,s3_bucket_service = s3_bucket_service, aws_region = config.AWS_REGION, aws_s3_bucket_name = config.S3_BUCKET_NAME, mongo_crud_chat_bot = mongo_crud_chat_bot)
    chat_bot_get_chat_bots = providers.Factory(GetChatBots, chat_bot_service = chat_bot_service,user_service = user_service)
    chat_bot_get_flow_nodes = providers.Factory(GetChatBotFlow, chat_bot_service = chat_bot_service,mongo_crud_chat_bot_flow = mongo_crud_chat_bot)
    chat_bot_trigger_chat_bot = providers.Factory(TriggerChatBot, chat_bot_service = chat_bot_service,conversation_service = conversation_service,trigger_publisher = chat_bot_trigger_publisher, business_service = business_profile_service,contact_service = contact_service)
    #----- error and logger -----
    error_handler = providers.Singleton(ErrorHandler, log_service = system_log_service)    

