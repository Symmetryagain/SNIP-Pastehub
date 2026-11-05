# app/core/security.py
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- API Key ---
# 与大模型服务的 API Key 同一模式：明文只在生成时展示一次，数据库只存 SHA-256 哈希。
# Key 本身有 128 bit 随机熵，因此无需加盐或慢哈希。
API_TOKEN_PREFIX = "tok_"
API_TOKEN_HASH_PREFIX = "sha256$"

def generate_api_token() -> str:
    return API_TOKEN_PREFIX + secrets.token_hex(16)

def hash_api_token(token: str) -> str:
    return API_TOKEN_HASH_PREFIX + hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(subject: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # username 仅供前端展示/控制按钮显隐，后端权限判断始终以数据库中的用户为准
    to_encode = {"exp": expire, "sub": str(subject), "username": username}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
