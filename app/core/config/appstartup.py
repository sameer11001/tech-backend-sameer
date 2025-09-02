from app.chat_bot.models.ChatBot import FlowNode
from app.core.logs.loggers import Logger
from app.whatsapp.broadcast.use_case.BroadcastConfig import BroadcastConfig
from app.whatsapp.template.models.Template import Template
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from app.core.config import settings
from app.core.storage.MongoDB import MongoDB
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.core.config.container import Container
from app.user_management.user.models.Client import Client
from app.user_management.auth.models.Role import Role
from app.user_management.user.models.User import User
from app.user_management.user.models.Team import Team
from app.utils.enums.RoleEnum import RoleEnum
from app.utils.encryption import get_hash
from app.whatsapp.team_inbox.models.Message import Message
from app.core.config.settings import settings
from app.events.app_events_route import rabbitmq_router

ROLES = [
    "ADMINISTRATOR",
    "AUTOMATION_MANAGER",
    "BROADCAST_MANAGER",
    "DEVELOPER",
    "DASHBOARD_VIEWER",
    "TEMPLATE_MANAGER",
    "BILLING_MANAGER",
    "OPERATOR",
    "Contact_MANAGER"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = MongoDB(settings.MONGO_URI, settings.MONGO_DB)
    await mongo.init_db([Message, Template,FlowNode,Logger])    
    container = Container()
    broadcast_config : BroadcastConfig = container.broadcast_broadcast_config()

    db_instance = container.psql()
    try:
        await db_instance.init_db()                  
        async with db_instance._session_factory() as db:
            # Create roles
            async def get_or_create_role(role_name: str) -> Role:
                result = await db.exec(
                    select(Role).filter_by(role_name=RoleEnum(role_name))
                )
                role = result.scalar_one_or_none()
                if not role:
                    role = Role(
                        role_name=RoleEnum(role_name),
                        description=f"{role_name} role",
                    )
                    db.add(role)
                    await db.flush()
                return role
            # Initialize roles
            for role_name in ROLES:
                await get_or_create_role(role_name)
            # Create or get client
            result = await db.exec(select(Client))
            client = result.scalar_one_or_none()
            if not client:
                client = Client(client_id=100)
                db.add(client)
                await db.flush()
            # Create or get team
            result = await db.exec(select(Team).filter_by(name="Example Team"))
            team = result.scalar_one_or_none()
            if not team:
                team = Team(
                    name="Example Team",
                    description="A demo team for all 7 users",
                    client_id=client.id,
                    is_default=True,
                )
                db.add(team)
                await db.flush()
            # Create or get business profile
            result = await db.exec(
                select(BusinessProfile).filter_by(business_id="904055570973681")
            )
            business_profile = result.scalar_one_or_none()
            if not business_profile:
                business_profile = BusinessProfile(
                    business_id="904055570973681",
                    app_id="670614906139142",
                    phone_number="+15551546858",
                    phone_number_id="558569350676631",
                    whatsapp_business_account_id="1691192741820643",
                    access_token="EAAJh67NC8gYBO237KkRZCbYanv1YAIYLxJOX8h8jufguMqY1JgVpa9ZAJE9eoFHLtZBLduFZCpv9SQWym5Va4ZBzebFAbXHjVyuYNjFM1cdekWZAsnj4cN9Sk8hZB1KzmaGjZCMOiTtyQs9G571p0ZC1PBmAQH6TAq4PiEhQgzLk8jWoHndqMhqqZBcAjZCLZAekE1OSZCEXXZAnLHD5KgGltwek4XSz3SU4SiAWntTRWGHBT5r37IInoZD",
                    client_id=client.id,
                )
                db.add(business_profile)
                await db.flush()
            # Create users
            result = await db.exec(select(User))
            users = result.scalars().all()
            emails_in_use = {u.email for u in users}
            for i, role_name in enumerate(ROLES, start=1):
                user_email = f"user{i}@example.com"
                if user_email in emails_in_use:
                    continue
                result = await db.exec(
                    select(Role).filter_by(role_name=RoleEnum(role_name))
                )
                user_role = result.scalar_one()
                new_user = User(
                    first_name=f"First{i}",
                    last_name=f"Last{i}",
                    email=user_email,
                    phone_number=f"+96279112204{i}",
                    password=get_hash(f"Password{i}"),
                    is_base_admin=(role_name == "ADMINISTRATOR"),
                    online_status=True,
                    client_id=client.id,
                )
                new_user.roles.append(user_role)
                new_user.teams.append(team)
                db.add(new_user)
            # Commit all changes
            await db.commit()
            await broadcast_config.start_listener()
            await rabbitmq_router.startup()
            yield
    finally:
        # Cleanup
        await db_instance._engine.dispose()
        mongo.client.close()   
        await rabbitmq_router.shutdown()
        await broadcast_config.stop_listener()