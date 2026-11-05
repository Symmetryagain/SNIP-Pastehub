# app/core/config.py
import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# 数据目录（Docker 中挂载为 ./snip_data）
DATA_DIR = "./data"
SECRET_KEY_FILE = os.path.join(DATA_DIR, ".secret_key")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "Snip Share"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DATA_DIR}/snip_data.db"

    # 不再提供写死的默认值：优先读环境变量 / .env，
    # 否则自动生成随机密钥并持久化到数据卷（见 _resolve_secret_key）
    SECRET_KEY: Optional[str] = None

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7


def _resolve_secret_key(configured: Optional[str]) -> str:
    if configured:
        if len(configured) < 32:
            raise RuntimeError("SECRET_KEY 太短，至少需要 32 个字符")
        return configured

    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        # O_EXCL 保证只有一个进程能创建成功，权限仅属主可读写
        fd = os.open(SECRET_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(64))

    with open(SECRET_KEY_FILE) as f:
        key = f.read().strip()
    if len(key) < 32:
        raise RuntimeError(f"{SECRET_KEY_FILE} 内容无效，请删除后重启以重新生成")
    return key


settings = Settings()
settings.SECRET_KEY = _resolve_secret_key(settings.SECRET_KEY)
