# app/db/migrate.py
# 启动时执行的轻量数据迁移（幂等，可重复运行）
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import hash_api_token, API_TOKEN_HASH_PREFIX


def hash_plaintext_api_tokens(db: Session) -> int:
    """把旧版本明文存储的 API Key 原地替换为哈希。

    用户手里的 Key 不变，只是数据库里不再保存明文。返回迁移的用户数。
    """
    users = db.query(User).all()
    migrated = 0
    for user in users:
        if not user.api_token_hash.startswith(API_TOKEN_HASH_PREFIX):
            user.api_token_hash = hash_api_token(user.api_token_hash)
            migrated += 1
    if migrated:
        db.commit()
    return migrated
