# app/db/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from app.db.database import Base
from sqlalchemy.orm import relationship

def generate_uuid():
    return uuid.uuid4().hex

# 解决 utcnow 弃用警告的向下兼容函数 (兼容 Python 3.10 到 3.12+)
# 获取当前的 UTC 时间并剥离时区信息，确保写入 SQLite 的格式与老数据保持绝对一致
def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    api_token = Column(String, unique=True, index=True, nullable=False) # 预留给 CLI
    created_at = Column(DateTime, default=get_utc_now)

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
    
    # 使用更新后的时间获取函数
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # 【新增】存储帖子标签，使用 SQLAlchemy 内置的 JSON 类型
    tags = Column(JSON, default=list, nullable=False)
    
    # 建立与 User 表的关联
    author = relationship("User", backref="posts")