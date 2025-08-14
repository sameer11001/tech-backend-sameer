import json
import functools
import inspect
from typing import Callable, Any, Union, List
from app.core.storage.redis import redis_client

def delete_cache(keys: Union[str, List[str]] = None):

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:

            result = await func(*args, **kwargs)
            
            if keys:
                key_fields = [keys] if isinstance(keys, str) else keys
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                try:
                    key_parts = [
                        f"{field}={json.dumps(bound_args.arguments[field], sort_keys=True)}"
                        for field in sorted(key_fields)
                    ]
                except KeyError as e:
                    raise ValueError(f"Missing key argument: {e.args[0]}")
                cache_key = f"cache:{func.__name__}:" + ":".join(key_parts)
            else:
                cache_key = (
                    f"cache:{func.__name__}:"
                    f"{json.dumps(args, sort_keys=True)}:"
                    f"{json.dumps(kwargs, sort_keys=True)}"
                )
            
            await redis_client.delete(cache_key)
            return result
        return wrapper
    return decorator