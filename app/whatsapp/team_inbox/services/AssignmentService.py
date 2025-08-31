from app.core.services.BaseService import BaseService
from app.whatsapp.team_inbox.models.Assignment import Assignment
from app.whatsapp.team_inbox.repositories.AssignmentRepository import AssignmentRepository


class AssignmentService(BaseService[Assignment]):
    def __init__(self, repository: AssignmentRepository):
        super().__init__(repository)
        self.repository = repository