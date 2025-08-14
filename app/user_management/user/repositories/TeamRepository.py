from math import ceil
from typing import List
from sqlmodel import Session, delete, func, select
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.user_management.user.models.Team import Team
from app.user_management.user.models.UserTeam import UserTeam
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

class TeamRepository(BaseRepository[Team]):
    def __init__(self, session: Session):
        super().__init__(model=Team, session=session)

    async def get_by_name(self, team_name: str) -> Team:
        try:
            statement = select(Team).where(Team.name == team_name)
            result = await self.session.exec(statement)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))      
    async def get_by_client_id(self, client_id: str) -> List[Team]:
        try:
            statement = select(Team).where(Team.client_id == client_id)
            result = await self.session.exec(statement).all()
            return result
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
                
    async def get_teams_with_users_by_client_id(
        self, client_id: str, query: str = None, page: int = 1, limit: int = 10
    ) -> dict:
        try:
            conditions = [Team.client_id == client_id]
            if query:
                conditions.append(Team.name.ilike(f"%{query}%"))
    
            total_count_result = await self.session.exec(
                select(func.count(Team.id)).where(*conditions)
            )
            total_count = total_count_result.first()
    
            teams_result = await self.session.exec(
                select(Team)
                .where(*conditions)
                .offset((page - 1) * limit)
                .limit(limit)
                .options(selectinload(Team.users))  # preload users if needed
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
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    async def updateTeamUsers(self, team_id: str, new_users: list[UserTeam]):
        try:
            await self.session.exec(
                delete(UserTeam).where(UserTeam.team_id == team_id)
            )
            if new_users:
                self.session.add_all(new_users)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(f"Failed to update team users: {e}")
    
    async def get_default_team_by_client_id(self, client_id: str):
        
        try:
            statement = select(Team).where(
                Team.client_id == client_id,
                Team.is_default.is_(True)
            )            
            result = await self.session.exec(statement)

            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))