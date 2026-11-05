# app/core/security.py
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # username 仅供前端展示/控制按钮显隐，后端权限判断始终以数据库中的用户为准
    to_encode = {"exp": expire, "sub": str(subject), "username": username}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
