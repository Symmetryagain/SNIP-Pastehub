# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- User ---
class UserResponse(BaseModel):
    id: str
    username: str
    api_token: str
    
    model_config = ConfigDict(from_attributes=True)

# --- Post ---
class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    parent_id: Optional[str] = None
    tags: List[str] = []

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

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