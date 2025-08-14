import os
from pathlib import Path
from fastapi import UploadFile
from app.core.services.StorageService import StorageService

class LocalStorageService(StorageService):
    def __init__(self, base_path: str = "tempfiles"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_id: str, file_data: UploadFile) -> str:
        full_path = self.base_path / file_id
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_data.file.read())
        return str(full_path)

    def get_file_url(self, file_id: str) -> str:
        full_path = self.base_path / file_id
        return str(full_path.resolve())

    def delete_file(self, file_id: str) -> bool:
        full_path = self.base_path / file_id
        if full_path.exists():
            full_path.unlink()
            return True
        return False