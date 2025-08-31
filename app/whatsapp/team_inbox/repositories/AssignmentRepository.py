from app.core.repository.BaseRepository import BaseRepository
from app.whatsapp.team_inbox.models.Assignment import Assignment
from sqlmodel.ext.asyncio.session import AsyncSession


class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, session: AsyncSession):
        self.session = session
        super().__init__(model=Assignment, session=session)
        
    