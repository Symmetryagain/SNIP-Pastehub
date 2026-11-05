# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- User ---
class MeResponse(BaseModel):
    id: str
    username: str
    is_admin: bool
    auth_method: Literal["session", "api_key"]  # 本次请求用的是密码会话（JWT）还是 API Key

# --- API Key ---
class RotateApiTokenRequest(BaseModel):
    password: str  # 轮换 Key 需要再次输入密码

class ApiTokenResponse(BaseModel):
    api_token: str  # 明文只在这里出现一次

# --- Post ---
class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    parent_id: Optional[str] = None
    tags: List[str] = []

class PostCreate(PostBase):
    # 来源标记：网页端默认 web，命令行工具传 cli
    created_via: Literal["web", "cli", "api"] = "web"

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class AuthorInfo(BaseModel):
    username: str
    model_config = ConfigDict(from_attributes=True)

class PostResponse(PostBase):
    id: str
    author_id: str
    author: AuthorInfo
    status: str
    created_via: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
