from typing import List, Type, Dict, Any
from app.core.exceptions.GlobalException import GlobalException

def generate_responses(
    exceptions: List[Type[GlobalException]],
    default_exception: bool = False
) -> Dict[int, Dict[str, Any]]:
    responses = {}
            
    for exception_cls in exceptions:
        if not hasattr(exception_cls, "exception_response"):
            raise TypeError(
                f"{exception_cls.__name__} must implement exception_response() class method"
            )
        exception_response = exception_cls.exception_response()
        for status_code, response_schema in exception_response.items():
            if status_code in responses:
                existing_examples = responses[status_code]["content"]["application/json"]["examples"]
                new_example = response_schema["content"]["application/json"]["examples"]
                existing_examples.update(new_example)
            else:
                responses[status_code] = response_schema
    return responses