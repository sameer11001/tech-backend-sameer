from typing import Dict, List, Optional, Union
from sqlalchemy import func, or_
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.user_management.user.models.User import User
from app.core.repository.BaseRepository import BaseRepository
from sqlmodel import  select
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.enums.SortBy import SortByCreatedAt

class UserRepository(BaseRepository[User]):
    def __init__(self, session : AsyncSession):
        
        self.session = session
        
        super().__init__(model=User, session=session)

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.session as db_session:
            try:
                statement = select(self.model).where(self.model.email == email)
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
            
    async def get_users_by_client_id(
        self, client_id: str, query: str, page: int, limit: int, sort_by: Optional[SortByCreatedAt]
    ) -> Dict[str, Union[List[User], int]]:
        async with self.session as db_session:
            try:
                base_query = select(self.model).where(self.model.client_id == client_id)
                
                if sort_by == SortByCreatedAt.ASC:
                    base_query = base_query.order_by(self.model.created_at)
                elif sort_by == SortByCreatedAt.DESC:
                    base_query = base_query.order_by(self.model.created_at.desc())
                    
                if query:
                    base_query = base_query.where(
                        or_(
                            self.model.email.ilike(f"%{query}%"),
                            self.model.first_name.ilike(f"%{query}%"),
                            self.model.last_name.ilike(f"%{query}%")
                        )
                    )

                if query:
                    total_count = await db_session.exec(
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
                    total_count = await db_session.exec(
                        select(func.count(self.model.id)).where(self.model.client_id == client_id)
                    )

                users = await db_session.exec(
                    base_query.offset((page - 1) * limit).limit(limit)
                )

                return {"users": users.all(), "total_count": total_count.first()}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_users_by_client_id_count(self, client_id: str) -> int:
        async with self.session as db_session:
            try:
                query = select(func.count(self.model.id)).where(self.model.client_id == client_id)
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def search_user(
        self, query_str: str, client_id: str, page: int, limit: int
    ) -> Dict[str, Union[List[User], int]]:
        async with self.session as db_session:
            try:
                count_query = select(func.count(self.model.id)).where(
                    self.model.client_id == client_id,
                    or_(
                        self.model.email.contains(query_str),
                        self.model.first_name.contains(query_str),
                        self.model.last_name.contains(query_str),
                    ),
                )
                count_result = await db_session.exec(count_query)
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
                result = await db_session.exec(query)
                users = result.all()

                return {"users": users, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_id_and_team_id(self, user_id: str, team_id: str) -> Optional[User]:
        async with self.session as db_session:
            try:
                result = await db_session.exec(
                    select(self.model).where(self.model.id == user_id, self.model.team_id == team_id)
                )
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))