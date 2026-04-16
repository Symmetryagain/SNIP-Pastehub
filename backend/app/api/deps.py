# app/api/deps.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.config import settings

# 核心修改：告诉 Swagger UI，去哪里（tokenUrl）用账号密码换取 Token
# 这里的 "/api/auth/login" 必须和 main.py 中挂载的路由路径完全一致
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), # 这里直接拿到解析后的 token 字符串
    db: Session = Depends(get_db)
) -> User:
    user = None
    
    try:
        # 路线 A：尝试作为网页端 JWT 解析
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
    except jwt.PyJWTError:
        # 路线 B：JWT 解析失败，尝试作为 CLI API Token 解析
        user = db.query(User).filter(User.api_token == token).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user