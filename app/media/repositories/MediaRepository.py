from sqlmodel import Session
from app.media.models.ModelMedia import ModelMedia
from app.core.repository.BaseRepository import BaseRepository

class MediaRepository(BaseRepository[ModelMedia]):
    def __init__(self, session: Session):
        self.session = session
        super().__init__(ModelMedia, session)
    