# app/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from app.db.database import Base
from sqlalchemy.orm import relationship

def generate_uuid():
    return uuid.uuid4().hex

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    api_token = Column(String, unique=True, index=True, nullable=False) # 预留给 CLI
    created_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True) # 允许为空（墓碑模式时清空内容）
    
    # 外键关联
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    # 溯源：指向被 Fork 的帖子。如果为空则为原创。
    parent_id = Column(String, ForeignKey("posts.id"), nullable=True)
    
    # 状态枚举：active 正常, deleted 墓碑模式
    status = Column(String, default="active", nullable=False) 
    
    created_via = Column(String, default="web", nullable=False) # web, api, cli
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 建立与 User 表的关联
    author = relationship("User", backref="posts")