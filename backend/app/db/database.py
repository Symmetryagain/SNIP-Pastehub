# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# SQLite 需要 check_same_thread=False 允许跨线程共享连接（FastAPI 异步路由需要）
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 获取数据库会话的依赖函数 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()