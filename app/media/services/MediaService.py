from app.core.services.BaseService import BaseService
from app.media.models.ModelMedia import ModelMedia
from app.media.repositories.MediaRepository import MediaRepository


class MediaServices(BaseService[ModelMedia]):
    def __init__(self, repository: MediaRepository):
        super().__init__(repository)
        self.repository = repository
    
    