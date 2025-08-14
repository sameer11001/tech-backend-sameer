from sqlmodel import Session
from app.core.repository.BaseRepository import BaseRepository
from app.whatsapp.team_inbox.models.Assignment import Assignment


class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, session: Session):
        super().__init__(model=Assignment, session=session)
        
    