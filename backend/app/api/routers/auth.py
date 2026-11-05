# app/api/routers/auth.py
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.security import (
    verify_password, create_access_token, generate_api_token, hash_api_token,
)
from app.schemas import Token, MeResponse, RotateApiTokenRequest, ApiTokenResponse
from app.api.deps import get_auth, get_session_user, is_admin

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    return {
        "access_token": create_access_token(user.id, user.username),
        "token_type": "bearer"
    }


@router.get("/me", response_model=MeResponse)
def read_me(auth: Tuple[User, str] = Depends(get_auth)):
    # 注意：不返回 API Key。Key 只在生成/轮换时展示一次
    user, method = auth
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": is_admin(user),
        "auth_method": method,
    }


@router.post("/token/rotate", response_model=ApiTokenResponse)
def rotate_api_token(
    body: RotateApiTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_session_user),
):
    # 生成新 Key 并立即作废旧 Key。要求：密码会话 + 再次输入密码，
    # 这样即使会话 JWT 泄露，也无法凭它换到永久有效的 Key
    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="密码错误")

    new_token = generate_api_token()
    current_user.api_token_hash = hash_api_token(new_token)
    db.commit()
    return {"api_token": new_token}
