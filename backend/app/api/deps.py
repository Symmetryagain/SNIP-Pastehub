# app/api/deps.py
from typing import Optional, Tuple
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import hash_api_token

# 核心修改：告诉 Swagger UI，去哪里（tokenUrl）用账号密码换取 Token
# 这里的 "/api/auth/login" 必须和 main.py 中挂载的路由路径完全一致
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ADMIN_USERNAME = "admin"

AUTH_SESSION = "session"   # 密码登录得到的 JWT（网页端 / snip login）
AUTH_API_KEY = "api_key"   # 无状态 API Key，每次请求携带


def is_admin(user: User) -> bool:
    return user.username == ADMIN_USERNAME


def _authenticate(token: str, db: Session) -> Tuple[Optional[User], Optional[str]]:
    # 路线 A：尝试作为 JWT 会话解析
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        pass
    else:
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        return user, (AUTH_SESSION if user else None)

    # 路线 B：作为 API Key 解析（数据库只存哈希）
    user = db.query(User).filter(User.api_token_hash == hash_api_token(token)).first()
    return user, (AUTH_API_KEY if user else None)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_auth(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Tuple[User, str]:
    """返回 (用户, 认证方式)。"""
    user, method = _authenticate(token, db)
    if user is None:
        raise _unauthorized()
    return user, method


def get_current_user(auth: Tuple[User, str] = Depends(get_auth)) -> User:
    # 业务接口：密码会话和 API Key 均可
    return auth[0]


def get_session_user(auth: Tuple[User, str] = Depends(get_auth)) -> User:
    # Key 管理接口：只接受密码会话，API Key 不能用来管理 Key
    user, method = auth
    if method != AUTH_SESSION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 不能用于管理 Key，请先用账号密码登录（snip login）",
        )
    return user
