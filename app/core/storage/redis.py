from datetime import datetime
import json
import msgpack
from typing import Any, Dict, List, Optional, Set, Union
import redis
import redis.asyncio as aioredis
from uuid import UUID as NativeUUID
from asyncpg.pgproto.pgproto import UUID as PgUUID

from app.utils.DateTimeHelper import DateTimeHelper

class RedisService:
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: Optional[str] = None,
        namespace: str = "",
        default_ttl: int = 30 * 24 * 60 * 60,
        use_msgpack: bool = True,
    ):
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.use_msgpack = use_msgpack
        self._DATETIME_KEY = "__datetime__"
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=not use_msgpack,
        )

    _DATETIME_EXT = 1
    _UUID_EXT = 2 
    
    def _encode_custom(self, obj):
        if isinstance(obj, datetime):
            dt = DateTimeHelper.ensure_utc(obj)
            return msgpack.ExtType(self._DATETIME_EXT, dt.isoformat().encode())
        if isinstance(obj, (NativeUUID, PgUUID)):
            return msgpack.ExtType(self._UUID_EXT, str(obj).encode())
        raise TypeError
    
    def _decode_custom(self, code, data):
        if code == self._DATETIME_EXT:
            return DateTimeHelper.ensure_utc(datetime.fromisoformat(data.decode()))
        if code == self._UUID_EXT:
            return data.decode()  
        return msgpack.ExtType(code, data)

    def _key(self, key: str) -> str:
        ns = f"{self.namespace}:" if self.namespace and not self.namespace.endswith(":") else self.namespace
        return f"{ns}{key}"

    def _serialize(self, value: Any) -> bytes:
        return msgpack.packb(value, use_bin_type=True, default=self._encode_custom)

    def _deserialize(self, raw: Union[bytes, str, None]) -> Any:
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            try:
                return msgpack.unpackb(raw, raw=False, ext_hook=self._decode_custom)
            except Exception:
                try:
                    return raw.decode()
                except Exception:
                    return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return raw
        return raw

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a key with an optional TTL.
        :param key: Redis key
        :param value: Value to store (any serializable object)
        :param ttl: Time-to-live in seconds (defaults to default_ttl)
        :param nx: Only set if key does not exist
        :param xx: Only set if key exists
        :return: True if set was successful
        """
        full_key = self._key(key)
        ex = ttl if ttl is not None else self.default_ttl
        data = self._serialize(value)
        return self._client.set(full_key, data, ex=ex, nx=nx, xx=xx)

    
    def get(self, key: str) -> Any:
        """Retrieve and deserialize a key."""
        raw = self._client.get(self._key(key))
        return self._deserialize(raw)

    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys, returns number of keys deleted."""
        full = [self._key(k) for k in keys]
        return self._client.delete(*full)

    
    def exists(self, *keys: str) -> int:
        """Check existence of keys, returns count of existing keys."""
        full = [self._key(k) for k in keys]
        return self._client.exists(*full)

    
    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on a key."""
        return self._client.expire(self._key(key), ttl)

    
    def ttl(self, key: str) -> int:
        """Get TTL of a key (seconds)."""
        return self._client.ttl(self._key(key))

    
    def hset(self, key: str, mapping: Dict[str, Any]) -> int:
        """Set multiple hash fields."""
        data = {field: self._serialize(val) for field, val in mapping.items()}
        return self._client.hset(self._key(key), mapping=data)

    
    def hget(self, key: str, field: str) -> Any:
        """Get a single hash field."""
        raw = self._client.hget(self._key(key), field)
        return self._deserialize(raw)

    
    def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all fields and values of a hash."""
        raw = self._client.hgetall(self._key(key))
        return {f: self._deserialize(v) for f, v in raw.items()}

    
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to head of list."""
        vals = [self._serialize(v) for v in values]
        return self._client.lpush(self._key(key), *vals)

    
    def rpush(self, key: str, *values: Any) -> int:
        """Push values to tail of list."""
        vals = [self._serialize(v) for v in values]
        return self._client.rpush(self._key(key), *vals)

    
    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get a range of list elements."""
        raw = self._client.lrange(self._key(key), start, end)
        return [self._deserialize(v) for v in raw]

    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a key by amount."""
        return self._client.incrby(self._key(key), amount)

    
    def pipeline(self) -> redis.client.Pipeline:
        """Create a pipeline for batch commands."""
        return self._client.pipeline()

    
    def flush_db(self) -> bool:
        """Flush the entire database."""
        return self._client.flushdb()

    
    def keys(self, pattern: str) -> List[str]:
        """List keys matching pattern."""
        return self._client.keys(self._key(pattern))


from datetime import datetime
import json
import msgpack
from typing import Any, Dict, List, Optional, Set, Union
import redis
import redis.asyncio as aioredis
from uuid import UUID as NativeUUID
from asyncpg.pgproto.pgproto import UUID as PgUUID

from app.utils.DateTimeHelper import DateTimeHelper

class AsyncRedisService:
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: Optional[str] = None,
        namespace: str = "",
        default_ttl: int = 30 * 24 * 60 * 60,
        use_msgpack: bool = True,
    ):
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.use_msgpack = use_msgpack
        self._DATETIME_KEY = "__datetime__"         
        self._client = aioredis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=not use_msgpack,
        )

    _DATETIME_EXT = 1
    _UUID_EXT = 2 
    
    def _encode_custom(self, obj):
        if isinstance(obj, datetime):
            dt = DateTimeHelper.ensure_utc(obj)
            return msgpack.ExtType(self._DATETIME_EXT, dt.isoformat().encode())
        if isinstance(obj, (NativeUUID, PgUUID)):
            return msgpack.ExtType(self._UUID_EXT, str(obj).encode())
        raise TypeError
    
    def _decode_custom(self, code, data):
        if code == self._DATETIME_EXT:
            return DateTimeHelper.ensure_utc(datetime.fromisoformat(data.decode()))
        if code == self._UUID_EXT:
            return data.decode()  
        return msgpack.ExtType(code, data)

    def _key(self, key: str) -> str:
        ns = f"{self.namespace}:" if self.namespace and not self.namespace.endswith(":") else self.namespace
        return f"{ns}{key}"

    def _serialize(self, value: Any, use_json: bool = False) -> Union[bytes, str]:
        if use_json:
            return json.dumps(value, default=str)  
        else:
            return msgpack.packb(value, use_bin_type=True, default=self._encode_custom)

    def _deserialize(self, raw: Union[bytes, str, None], use_json: bool = False) -> Any:
        if raw is None:
            return None
            
        if use_json:
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return raw
            elif isinstance(raw, (bytes, bytearray)):
                try:
                    decoded = raw.decode('utf-8')
                    return json.loads(decoded)
                except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                    return raw.decode('utf-8', errors='ignore')
            return raw
        else:
            if isinstance(raw, (bytes, bytearray)):
                try:
                    return msgpack.unpackb(raw, raw=False, ext_hook=self._decode_custom)
                except Exception:
                    try:
                        return raw.decode()
                    except Exception:
                        return raw
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except Exception:
                    return raw
            return raw

    def _smart_deserialize(self, raw: Union[bytes, str, None]) -> Any:
        if raw is None:
            return None
            
        if isinstance(raw, (bytes, bytearray)):
            try:
                decoded_str = raw.decode('utf-8')
                if decoded_str.isdigit() or (decoded_str.startswith('-') and decoded_str[1:].isdigit()):
                    return int(decoded_str)
            except (UnicodeDecodeError, ValueError):
                pass
        
        try:
            return self._deserialize(raw, use_json=False)
        except Exception:
            try:
                return self._deserialize(raw, use_json=True)
            except Exception:
                if isinstance(raw, (bytes, bytearray)):
                    return raw.decode('utf-8', errors='ignore')
                return raw

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
        use_json: bool = False,
    ) -> bool:
        """
        Set a key with optional JSON serialization.
        
        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            use_json: Use JSON serialization instead of MessagePack
        """
        full_key = self._key(key)
        ex = ttl if ttl is not None else self.default_ttl
        data = self._serialize(value, use_json=use_json)
        return await self._client.set(full_key, data, ex=ex, nx=nx, xx=xx)

    async def get(self, key: str, use_json: bool = False) -> Any:
        raw = await self._client.get(self._key(key))
        return self._deserialize(raw, use_json=use_json)

    async def get_smart(self, key: str) -> Any:
        raw = await self._client.get(self._key(key))
        return self._smart_deserialize(raw)

    async def delete(self, *keys: str) -> int:
        full = [self._key(k) for k in keys]
        return await self._client.delete(*full)

    async def exists(self, *keys: str) -> int:
        full = [self._key(k) for k in keys]
        return await self._client.exists(*full)

    async def expire(self, key: str, ttl: int) -> bool:
        return await self._client.expire(self._key(key), ttl)

    async def ttl(self, key: str) -> int:
        return await self._client.ttl(self._key(key))

    async def hset(self, key: str, mapping: Dict[str, Any], use_json: bool = False) -> int:
        if use_json:
            data = {field: self._serialize(val, use_json=True) for field, val in mapping.items()}
        else:
            data = {field: self._serialize(val, use_json=False) for field, val in mapping.items()}
        return await self._client.hset(self._key(key), mapping=data)

    async def hget(self, key: str, field: str, use_json: bool = False) -> Any:
        raw = await self._client.hget(self._key(key), field)
        return self._deserialize(raw, use_json=use_json)

    async def hgetall(self, key: str, use_json: bool = False) -> Dict[str, Any]:
        raw = await self._client.hgetall(self._key(key))
        cleaned: dict[str, Any] = {}
        for k, v in raw.items():
            skey = k.decode() if isinstance(k, (bytes, bytearray)) else k
            cleaned[skey] = self._deserialize(v, use_json=use_json)
        return cleaned

    async def hgetall_smart(self, key: str) -> Dict[str, Any]:
        raw = await self._client.hgetall(self._key(key))
        cleaned: dict[str, Any] = {}
        for k, v in raw.items():
            skey = k.decode() if isinstance(k, (bytes, bytearray)) else k
            cleaned[skey] = self._smart_deserialize(v)
        return cleaned

    async def lpush(self, key: str, *values: Any, use_json: bool = False) -> int:
        if use_json:
            vals = [self._serialize(v, use_json=True) for v in values]
        else:
            vals = [self._serialize(v, use_json=False) for v in values]
        return await self._client.lpush(self._key(key), *vals)

    async def rpush(self, key: str, *values: Any, use_json: bool = False) -> int:
        if use_json:
            vals = [self._serialize(v, use_json=True) for v in values]
        else:
            vals = [self._serialize(v, use_json=False) for v in values]
        return await self._client.rpush(self._key(key), *vals)

    async def lrange(self, key: str, start: int, end: int, use_json: bool = False) -> List[Any]:
        raw = await self._client.lrange(self._key(key), start, end)
        return [self._deserialize(v, use_json=use_json) for v in raw]

    async def incr(self, key: str, amount: int = 1) -> int:
        return await self._client.incrby(self._key(key), amount)

    async def pipeline(self) -> aioredis.client.Pipeline:
        return self._client.pipeline()

    async def flush_db(self) -> bool:
        return await self._client.flushdb()

    async def keys(self, pattern: str) -> List[str]:
        return await self._client.keys(self._key(pattern))

    async def close(self):
        await self._client.close()
        
    async def get_redis(self):
        return self._client

    async def sadd(self, key: str, *values: Any, use_json: bool = False) -> int:
        if use_json:
            vals = [self._serialize(v, use_json=True) for v in values]
        else:
            vals = [self._serialize(v, use_json=False) for v in values]
        return await self._client.sadd(self._key(key), *vals)

    async def srem(self, key: str, *values: Any, use_json: bool = False) -> int:
        if use_json:
            vals = [self._serialize(v, use_json=True) for v in values]
        else:
            vals = [self._serialize(v, use_json=False) for v in values]
        return await self._client.srem(self._key(key), *vals)

    async def smembers(self, key: str, use_json: bool = False) -> Set[Any]:
        raw = await self._client.smembers(self._key(key))
        return {self._deserialize(v, use_json=use_json) for v in raw}
    
    async def sismember(self, key: str, value: Any, use_json: bool = False) -> bool:
        if isinstance(value, str) and not use_json:
            return await self._client.sismember(key, value)
        else:
            serialized_value = self._serialize(value, use_json=use_json)
            return await self._client.sismember(key, serialized_value)    
        
    async def scard(self, key: str) -> int:
        return await self._client.scard(self._key(key))
    
    async def xadd(self, key: str, fields: Dict[str, Any], id: str = '*', maxlen: Optional[int] = None, approximate: bool = True, use_json: bool = False) -> str:
        if not isinstance(fields, dict) or not fields:
            raise ValueError("Fields must be a non-empty dictionary for xadd.")
        
        serialized_fields = {}
        for k, v in fields.items():
            key_str = str(k)
            serialized_fields[key_str] = self._serialize(v, use_json=use_json)
            
        return await self._client.xadd(
            name=self._key(key),
            fields=serialized_fields,
            id=id,
            maxlen=maxlen,
            approximate=approximate
        )

    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        result = await self._client.hincrby(self._key(key), field, amount)
        return result

    async def hset_unread_consistent(self, key: str, mapping: Dict[str, Any]) -> int:

        processed_mapping = {}
        
        for field, value in mapping.items():
            if field == 'unread_count' and isinstance(value, (int, float)):
                processed_mapping[field] = int(value)
            else:
                processed_mapping[field] = self._serialize(value, use_json=True)
        
        return await self._client.hset(self._key(key), mapping=processed_mapping)

    async def hgetall_unread_consistent(self, key: str) -> Dict[str, Any]:
        return await self.hgetall_smart(key)