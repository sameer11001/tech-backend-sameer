from abc import ABC, abstractmethod

from fastapi import UploadFile


class StorageService(ABC):

    @abstractmethod
    def save_file(self, file_path: str, file_data: UploadFile) -> str:
        pass

    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        pass