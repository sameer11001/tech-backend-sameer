from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hash(value: str) -> str:    
    return pwd_context.hash(value)


def verify_hash(value: str, hashed: str) -> bool:
    return pwd_context.verify(value, hashed)
