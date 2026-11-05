# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.security import verify_password, create_access_token
from app.schemas import Token, MeResponse
from app.api.deps import get_current_user, is_admin

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
def read_me(current_user: User = Depends(get_current_user)):
    # 返回当前用户信息及其长期 API Token（CLI 登录后用它代替会过期的 JWT）
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": is_admin(current_user),
        "api_token": current_user.api_token,
    }
