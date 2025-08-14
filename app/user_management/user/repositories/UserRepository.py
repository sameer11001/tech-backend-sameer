from typing import Dict, List, Optional, Union
from sqlalchemy import func, or_
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.user_management.user.models.User import User
from app.core.repository.BaseRepository import BaseRepository
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(model=User, session=session)

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            statement = select(self.model).where(self.model.email == email)
            result = await self.session.exec(statement)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    async def get_users_by_client_id(
        self, client_id: str, query: str, page: int, limit: int
    ) -> Dict[str, Union[List[User], int]]:
        try:
            base_query = select(self.model).where(self.model.client_id == client_id).order_by(
                self.model.created_at.desc()
            )
            if query:
                base_query = base_query.where(
                    or_(
                        self.model.email.ilike(f"%{query}%"),
                        self.model.first_name.ilike(f"%{query}%"),
                        self.model.last_name.ilike(f"%{query}%") 
                    )
                )
            
            if query:
                total_count = await self.session.exec(
                    select(func.count(self.model.id)).where(
                        self.model.client_id == client_id,
                        or_(
                            self.model.email.ilike(f"%{query}%"),
                            self.model.first_name.ilike(f"%{query}%"),
                            self.model.last_name.ilike(f"%{query}%") 
                        )
                    )
                )
            else:    
                total_count = await self.session.exec(
                    select(func.count(self.model.id)).where(self.model.client_id == client_id)
                )
            
            users = await self.session.exec(
                base_query.offset((page - 1) * limit).limit(limit)
            )
            
            return {"users": users.all(), "total_count": total_count.first()}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    async def get_users_by_client_id_count(self, client_id: str) -> int:
        try:
            query = select(func.count(self.model.id)).where(
                self.model.client_id == client_id
            )
            result = await self.session.exec(query)
            return result.all()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    async def search_user(
        self, query_str: str, client_id: str, page: int, limit: int
    ) -> Dict[str, Union[List[User], int]]:
        try:
            count_query = select(func.count(self.model.id)).where(
                self.model.client_id == client_id,
                or_(
                    self.model.email.contains(query_str),
                    self.model.first_name.contains(query_str),
                    self.model.last_name.contains(query_str),
                ),
            )
            count_result = await self.session.exec(count_query)
            total_count = count_result.first()

            query = (
                select(self.model)
                .where(
                    self.model.client_id == client_id,
                    or_(
                        self.model.email.contains(query_str),
                        self.model.first_name.contains(query_str),
                        self.model.last_name.contains(query_str),
                    ),
                )
                .offset((page - 1) * limit)
                .limit(limit)
            )
            result = await self.session.exec(query)
            users = result.all()

            return {"users": users, "total_count": total_count}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))  
    async def get_by_id_and_team_id(self, user_id: str, team_id: str) -> Optional[User]:
        try:
            result = await self.session.exec(select(self.model).where(self.model.id == user_id, self.model.team_id == team_id))
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))