from app.annotations.repositories.AttributeRepository import AttributeRepository
from app.annotations.repositories.ContactRepository import ContactRepository
from app.annotations.repositories.NoteRepository import NoteRepository
from app.annotations.services.AttributeService import AttributeService
from app.annotations.services.ContactService import ContactService
from app.annotations.services.NoteService import NoteService
from app.annotations.v1.use_case.CreateAttribute import CreateAttribute
from app.annotations.v1.use_case.CreateContact import CreateContact
from app.annotations.v1.use_case.CreateNote import CreateNote
from app.annotations.v1.use_case.DeleteAttribute import DeleteAttribute
from app.annotations.v1.use_case.DeleteAttributeByContact import DeleteAttributeByContact
from app.annotations.v1.use_case.DeleteContact import DeleteContact
from app.annotations.v1.use_case.DeleteNote import DeleteNote
from app.annotations.v1.use_case.GetAttributes import GetAttributes
from app.annotations.v1.use_case.GetAttributesByContact import GetAttributesByContact
from app.annotations.v1.use_case.GetContacts import GetContacts
from app.annotations.v1.use_case.GetNoteByContact import GetNoteByContact
from app.annotations.v1.use_case.GetTagByContact import GetTagByContact
from app.annotations.v1.use_case.UpdateAttribute import UpdateAttribute
from app.annotations.repositories.TagRepository import TagRepository
from app.annotations.services.TagService import TagService
from app.annotations.v1.use_case.CreateTag import CreateTag
from app.annotations.v1.use_case.DeleteTag import DeleteTag
from app.annotations.v1.use_case.GetTags import GetTags
from app.annotations.v1.use_case.UpdateAttributeByContact import UpdateAttributeByContact
from app.annotations.v1.use_case.UpdateContacts import UpdateContact
from app.annotations.v1.use_case.UpdateNote import UpdateNote
from app.annotations.v1.use_case.UpdateTag import UpdateTag
from app.chat_bot.models.ChatBot import ChatBot
from app.chat_bot.repositories.ChatBotRepositories import ChatBotRepository
from app.chat_bot.services.ChatBotService import ChatBotService
from app.chat_bot.v1.use_case.CreateChatBot import CreateChatBot
from app.core.broker.MessageBroadcastPublisher import MessageBroadcastPublisher
from app.core.broker.RabbitMQBroker import RabbitMQBroker,RabbitMQSettings
from app.core.broker.WhatsappMessagePublisher import  WhatsappMessagePublisher
from app.core.exceptions.ErrorHandler import raise_for_status

from app.core.repository.MongoRepository import MongoCRUD
from app.core.services.S3Service import S3Service
from app.core.storage.redis import AsyncRedisService
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.real_time.webhook.services.MessageHook import MessageHook
from app.real_time.webhook.services.TemplateHook import TemplateHook
from app.real_time.webhook.services.WebhookDispatcher import WebhookDispatcher
from app.user_management.user.repositories.UserRepository import UserRepository
from app.user_management.user.v1.use_case.DeleteTeam import DeleteTeam
from app.user_management.user.v1.use_case.EditTeam import EditTeam
from app.whatsapp.broadcast.repositories.BroadCastRepository import BroadcastRepository
from app.whatsapp.broadcast.services.BroadCastService import BroadcastService
from app.whatsapp.broadcast.use_case.BroadcastConfig import BroadcastConfig
from app.whatsapp.broadcast.use_case.BroadcastScheduler import BroadcastScheduler
from app.whatsapp.broadcast.use_case.CancelBroadcast import CancelBroadcast
from app.whatsapp.broadcast.use_case.GetBroadcasts import GetBroadcasts
from app.whatsapp.business_profile.external_services.BusinessProfileApi import BusinessProfileApi
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.business_profile.v1.use_case.UploadFileData import UploadFileData
from app.whatsapp.business_profile.v1.use_case.CreateUploadSession import CreateUploadSession
from app.whatsapp.business_profile.v1.use_case.GetBusinessProfile import GetBusinessProfile
from app.whatsapp.business_profile.v1.use_case.UpdateBusinessProfile import UpdateBusinessProfile
from app.whatsapp.business_profile.v1.use_case.UpdateProfilePicture import UpdateProfilePicture
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi
from app.whatsapp.media.v1.usecase.CreaeSession import CreateSession
from app.whatsapp.media.v1.usecase.DeleteMedia import DeleteMedia
from app.whatsapp.media.v1.usecase.DownloadMedia import DownloadMedia
from app.whatsapp.media.v1.usecase.RetrieveMediaUrl import RetrieveMediaUrl
from app.whatsapp.media.v1.usecase.UploadMedia import UploadMedia
from app.whatsapp.media.v1.usecase.UploadSession import UploadFileSession
from app.whatsapp.team_inbox.external_services.WhatsAppMessageApi import WhatsAppMessageApi
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.operations.SaveMessage import SaveMessage
from app.whatsapp.team_inbox.repositories.AssignmentRepository import AssignmentRepository
from app.whatsapp.team_inbox.repositories.ConversationRepository import ConversationRepository
from app.whatsapp.team_inbox.repositories.MessageRepository import MessageRepository
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService
from app.whatsapp.team_inbox.v1.use_case.AssignedUserToConversation import AssignedUserToConversation
from app.whatsapp.team_inbox.v1.use_case.GetConversationMessages import GetConversationMessages
from app.whatsapp.team_inbox.v1.use_case.GetUserConversations import GetUserConversations
from app.whatsapp.team_inbox.v1.use_case.CreateNewConversation import CreateNewConversation
from app.whatsapp.team_inbox.v1.use_case.LocationMessage import LocationMessage
from app.whatsapp.team_inbox.v1.use_case.MediaMessage import MediaMessage
from app.whatsapp.team_inbox.v1.use_case.ReplyWithReactionMessage import ReplyWithReactionMessage
from app.whatsapp.team_inbox.v1.use_case.TemplateMessage import TemplateMessage
from app.whatsapp.team_inbox.v1.use_case.TextMessage import TextMessage
from app.whatsapp.team_inbox.v1.use_case.UpdateConversationStatus import UpdateConversationStatus
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.repositories.TemplateRepositories import TemplateRepository
from app.whatsapp.template.services.TemplateService import TemplateService
from app.whatsapp.template.v1.usecase.CreateTemplate import CreateTemplate
from app.whatsapp.template.v1.usecase.DeleteTemplate import DeleteTemplate
from dependency_injector import containers, providers

from app.user_management.auth.repositories.RefreshTokenRepository import RefreshTokenRepository
from app.user_management.auth.repositories.RoleRepository import RoleRepository
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.user_management.auth.services.RoleService import RoleService
from app.user_management.auth.v1.use_case.FrocePasswordResetByAdmin import ForcePasswordResetByAdmin
from app.user_management.auth.v1.use_case.ForceLogoutByAdmin import ForceLogoutByAdmin
from app.user_management.auth.v1.use_case.GetRoles import GetRoles
from app.user_management.auth.v1.use_case.TokenRefresh import TokenRefresh
from app.user_management.auth.v1.use_case.UserLogin import UserLogin
from app.user_management.auth.v1.use_case.UserLogout import UserLogout
from app.core.config.settings import Settings
from app.core.storage.postgres import PostgresDatabase, get_session
from app.user_management.user.repositories.ClientRepository import ClientRepository
from app.user_management.user.repositories.TeamRepository import TeamRepository
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService
from app.user_management.user.v1.use_case.CreateTeam import CreateTeam
from app.user_management.user.v1.use_case.CreateUser import CreateUser
from app.user_management.user.v1.use_case.DeleteUserById import DeleteUserById
from app.user_management.user.v1.use_case.EditUser import EditUser
from app.user_management.user.v1.use_case.GetTeams import GetTeams
from app.user_management.user.v1.use_case.GetUserInfo import GetUserInfo
from app.user_management.user.v1.use_case.GetUsersByClientId import GetUsersByClientId
from app.whatsapp. business_profile.v1.repository.BusinessProfileRepository import BusinessProfileRepository
from app.whatsapp.template.external_services.WhatsAppTemplateApi import WhatsAppTemplateApi
from app.whatsapp.template.v1.usecase.GetTemplates import GetTemplates
from botocore.config import Config as BotoConfig
from boto3.s3.transfer import TransferConfig
from socketio import AsyncServer,AsyncRedisManager
import boto3
import httpx

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
            'app.core.config.appstartup',
            'app.core.exceptions.ErrorHandler',
            'app.core.controllers.BaseController',
            'app.annotations.v1.controllers.NoteController',
            'app.chat_bot.v1.controllers.ChatBotController',
        ]
    )

    
    #----- CONFIG -----
    config = providers.Configuration()
    config.from_pydantic(Settings())
    
    redis_manager = providers.Singleton(
        AsyncRedisManager,
        url = config.CACHE_URL
    )
    
    #----- socket -----
    sio: AsyncServer= providers.Singleton(
        AsyncServer,
        async_mode="asgi",
        client_manager=redis_manager,
        cors_allowed_origins=["http://localhost:4200","http://localhost:59943"],
        transports=['websocket'],
        logger=True,
        engineio_logger=True,
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
    session = providers.Resource(get_session, db_instance=psql)

    http_client = providers.Singleton(httpx.AsyncClient, event_hooks={'response': [raise_for_status]}, timeout=120)
    
    mongo_crud_message = providers.Singleton(MongoCRUD, model = Message) 
    mongo_crud_template = providers.Singleton(MongoCRUD, model = Template) 
    mongo_crud_chat_bot = providers.Singleton(MongoCRUD, model=ChatBot)
    
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
    
    #----- REPOSITORIES -----
    user_repository = providers.Factory(UserRepository, session = session)
    team_repository = providers.Factory(TeamRepository, session = session)
    client_repository = providers.Factory(ClientRepository, session = session)
    refresh_token_repository = providers.Factory(RefreshTokenRepository, session = session)
    role_repository = providers.Factory(RoleRepository, session = session)
    business_profile_repository = providers.Factory(BusinessProfileRepository, session = session)
    tag_repository = providers.Factory(TagRepository, session = session)
    attribute_repository = providers.Factory(AttributeRepository, session = session)
    contact_repository = providers.Factory(ContactRepository, session = session)
    message_repository = providers.Factory(MessageRepository, session = session)
    template_repository = providers.Factory(TemplateRepository, session = session)
    conversation_repository = providers.Factory(ConversationRepository, session = session)
    assignment_repository = providers.Factory(AssignmentRepository, session = session)
    broadcast_repository = providers.Factory(BroadcastRepository, session = session)
    note_repository = providers.Factory(NoteRepository, session = session)
    chat_bot_repository = providers.Factory(ChatBotRepository, session = session)
    
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
    message_hook = providers.Singleton(MessageHook, message_service = message_service,conversation_service = conversation_service, save_message = save_message_document, contact_service = contact_service, client_service = client_service, assignment_service = assignment_service,team_service = team_service, business_profile_service = business_profile_service ,message_publisher = message_publisher, media_api = whatsapp_media_api,redis_service = async_redis_service,mongo_message = mongo_crud_message,socket_message = socket_message_gateway, s3_service = s3_bucket_service, aws_s3_bucket = config.S3_BUCKET_NAME, aws_region = config.AWS_REGION)
    webhook_dispatcher = providers.Factory(WebhookDispatcher, message_hook = message_hook, template_hook = template_hook)
    
    #----- ChatBot -----
    chat_bot_create_chat_bot = providers.Factory(CreateChatBot, chat_bot_service = chat_bot_service, user_service = user_service)
    