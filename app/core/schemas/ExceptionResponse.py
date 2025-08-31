from typing import Dict, Any, Type, ClassVar
from app.core.exceptions.GlobalException import GlobalException


class ExceptionResponse:
    @staticmethod
    def generate(exception_class: Type[GlobalException]) -> Dict[int, Dict[str, Any]]:
        default_instance = exception_class()
        return {
            default_instance.status_code: {
                "description": default_instance.message,
                "content": {
                    "application/json": {
                        "examples": {
                            default_instance.error_code.name: {
                                "summary": default_instance.message,
                                "value": {
                                    "status": "error",
                                    "error": {
                                        "status_code": default_instance.status_code,
                                        "error_code": default_instance.error_code,
                                        "message": default_instance.message,
                                        "timestamp": "2025-03-06T12:00:00Z",
                                        "path": "/example/path",
                                    },
                                },
                            }
                        }
                    }
                },
            }
        }
