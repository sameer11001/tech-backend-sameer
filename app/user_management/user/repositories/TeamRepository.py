from math import ceil
from typing import List, Optional
from sqlmodel import select, delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.user_management.user.models.Team import Team
from app.user_management.user.models.UserTeam import UserTeam
from sqlmodel.ext.asyncio.session import AsyncSession

class TeamRepository(BaseRepository[Team]):

    def __init__(self, session : AsyncSession):
        super().__init__(model=Team, session=session)

    async def get_by_name(self, team_name: str) -> Optional[Team]:
        async with self.session as db_session:
            try:
                statement = select(Team).where(Team.name == team_name)
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_client_id(self, client_id: str) -> List[Team]:
        async with self.session as db_session:
            try:
                statement = select(Team).where(Team.client_id == client_id)
                result = await db_session.exec(statement)
                return result.all()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_teams_with_users_by_client_id(
        self, client_id: str, query: str = None, page: int = 1, limit: int = 10
    ) -> dict:
        async with self.session as db_session:
            try:
                conditions = [Team.client_id == client_id]
                if query:
                    conditions.append(Team.name.ilike(f"%{query}%"))

                total_count_result = await db_session.exec(
                    select(func.count(Team.id)).where(*conditions)
                )
                total_count = total_count_result.first() or 0

                teams_result = await db_session.exec(
                    select(Team)
                    .where(*conditions)
                    .offset((page - 1) * limit)
                    .limit(limit)
                    .options(selectinload(Team.users))
                )
                teams = teams_result.all()

                return {
                    "teams": teams,
                    "total_count": total_count,
                    "page": page,
                    "limit": limit,
                    "total_pages": ceil(total_count / limit) if limit else 1
                }

            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def updateTeamUsers(self, team_id: str, new_users: List[UserTeam]):
        async with self.session as db_session:
            try:
                await db_session.exec(delete(UserTeam).where(UserTeam.team_id == team_id))
                if new_users:
                    db_session.add_all(new_users)
                await db_session.commit()
            except SQLAlchemyError as e:
                raise DataBaseException(f"Failed to update team users: {e}")

    async def get_default_team_by_client_id(self, client_id: str) -> Optional[Team]:
        async with self.session as db_session:
            try:
                statement = select(Team).where(
                    Team.client_id == client_id,
                    Team.is_default.is_(True)
                )
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
