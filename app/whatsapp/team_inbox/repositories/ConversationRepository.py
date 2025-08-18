from typing import Optional
from uuid import UUID
from sqlalchemy import desc, func
from sqlmodel import Session, or_ , select
from app.annotations.models.Contact import Contact
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.user_management.user.models.Team import Team
from app.user_management.user.models.UserTeam import UserTeam
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.ConversationTeamLink import ConversationTeamLink
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: Session):
        super().__init__(model=Conversation, session=session)
        
    async def find_by_contact_and_client_number(
        self, contact_phone_number: str, client_phone_number: str
    ) -> Optional[Conversation]:
        try:
            query = (
                select(Conversation)
                .join(Contact, Conversation.contact_id == Contact.id)
                .join(BusinessProfile, Conversation.client_id == BusinessProfile.client_id)
                .where(Contact.phone_number == contact_phone_number)
                .where(BusinessProfile.phone_number == client_phone_number)
            )            
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    async def find_by_contact_and_client_id(
        self,
        contact_phone_number: str,
        client_id: UUID
    ) -> Optional[Conversation]:
        try:
            query = (
                select(Conversation)
                .join(Contact, Conversation.contact_id == Contact.id)
                .where(
                    Contact.phone_number == contact_phone_number,
                    Contact.client_id == client_id
                )
            )            
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise  DataBaseException(e)
    
    async def get_user_conversations(
        self, 
        user_id: UUID, 
        page: int = 1, 
        limit: int = 10,
        search_term: Optional[str] = None
    ) -> dict:
        offset = (page - 1) * limit
    
        try:
            subquery_latest_msg = (
                select(
                    MessageMeta.conversation_id,
                    func.max(MessageMeta.created_at).label("latest_msg_time")
                )
                .group_by(MessageMeta.conversation_id)
                .subquery()
            )
    
            query = (
                select(Conversation)
                .join(ConversationTeamLink, Conversation.id == ConversationTeamLink.conversation_id)
                .join(UserTeam, UserTeam.team_id == ConversationTeamLink.team_id)
                .join(Contact, Conversation.contact_id == Contact.id)  
                .outerjoin(subquery_latest_msg, Conversation.id == subquery_latest_msg.c.conversation_id)
                .where(UserTeam.user_id == user_id)
                .options(selectinload(Conversation.conversation_link))
                .options(selectinload(Conversation.assignment))
                .order_by(desc(subquery_latest_msg.c.latest_msg_time))  
            )

            if search_term and search_term.strip():
                search_conditions = self._build_search_conditions(search_term.strip())
                query = query.where(search_conditions)
    
            result = await self.session.exec(query.offset(offset).limit(limit))
            conversations = result.all()
    
            count_query = (
                select(func.count(func.distinct(Conversation.id)))
                .join(ConversationTeamLink, Conversation.id == ConversationTeamLink.conversation_id)
                .join(UserTeam, UserTeam.team_id == ConversationTeamLink.team_id)
                .join(Contact, Conversation.contact_id == Contact.id)
                .where(UserTeam.user_id == user_id)
            )

            if search_term and search_term.strip():
                search_conditions = self._build_search_conditions(search_term.strip())
                count_query = count_query.where(search_conditions)
    
            total_items = (await self.session.exec(count_query)).one()
            total_pages = (total_items + limit - 1) // limit
    
            return {
                "data": conversations,
                "meta": {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                    "next_page": page + 1 if page < total_pages else None,
                    "prev_page": page - 1 if page > 1 else None,
                },
            }
    
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    def _build_search_conditions(self, search_term: str):

        clean_search = search_term.lower().strip()
        
        phone_search = ''.join(c for c in clean_search if c.isdigit())
        
        search_conditions = []
        
        if clean_search:
            search_conditions.append(
                func.lower(Contact.name).like(f"{clean_search}")
            )
            
            search_conditions.append(
                func.lower(Contact.name).like(f"{clean_search}%")
            )
            
            search_conditions.append(
                func.lower(Contact.name).like(f"%{clean_search}%")
            )
            
            words = clean_search.split()
            if len(words) > 1:
                for word in words:
                    if len(word) > 2:
                        search_conditions.append(
                            func.lower(Contact.name).like(f"%{word}%")
                        )
        
        if phone_search:
            search_conditions.append(
                Contact.phone_number.like(f"%{phone_search}%")
            )
            
            search_conditions.append(
                func.concat(Contact.country_code, Contact.phone_number).like(f"%{phone_search}%")
            )
            
            if len(phone_search) >= 4:
                search_conditions.append(
                    Contact.phone_number.like(f"%{phone_search[-4:]}")
                )
            if len(phone_search) >= 6:
                search_conditions.append(
                    Contact.phone_number.like(f"%{phone_search[-6:]}")
                )
            if len(phone_search) >= 8:
                search_conditions.append(
                    Contact.phone_number.like(f"%{phone_search[-8:]}")
                )
        
        if clean_search and any(c.isdigit() for c in clean_search) and any(c.isalpha() for c in clean_search):
            alpha_part = ''.join(c for c in clean_search if c.isalpha())
            numeric_part = ''.join(c for c in clean_search if c.isdigit())
            
            if alpha_part:
                search_conditions.append(
                    func.lower(Contact.name).like(f"%{alpha_part}%")
                )
            if numeric_part:
                search_conditions.append(
                    Contact.phone_number.like(f"%{numeric_part}%")
                )
        
        return or_(*search_conditions) if search_conditions else True