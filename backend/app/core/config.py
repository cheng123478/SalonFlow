"""全局配置：从环境变量 / .env 读取，集中管理。"""
import logging
import secrets

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "SalonFlow"
    debug: bool = True
    secret_key: str = ""
    access_token_expire_minutes: int = 10080

    # 上传文件目录（相对 backend 运行目录）
    upload_dir: str = "uploads"

    # Agent：会话记忆（每会话保留的最近消息条数）
    history_limit: int = 20

    # 长期记忆：召回条数 / 去重相似度阈值
    memory_top_k: int = 3
    memory_similarity_threshold: float = 0.9

    # SQL 日志（默认关闭，避免每次只读查询的 BEGIN/ROLLBACK 刷屏；调试时置 true）
    sql_echo: bool = False

    # MySQL
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_user: str = "root"
    mysql_password: str = "salonflow123"
    mysql_database: str = "salonflow"

    # DeepSeek（阶段 3+）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Qdrant（阶段 5+）
    qdrant_url: str = "http://127.0.0.1:6333"

    # Embedding：云 bge-m3 API（阶段 5+）
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "BAAI/bge-m3"

    @model_validator(mode="after")
    def _ensure_secret_key(self):
        if not self.secret_key or "please-change-me" in self.secret_key:
            self.secret_key = secrets.token_hex(32)
            logger.warning(
                "未配置安全的 SECRET_KEY，已临时生成随机密钥（重启后登录态失效）。"
                "生产环境请通过环境变量设置固定的 SECRET_KEY。"
            )
        return self

    @property
    def database_url(self) -> str:
        """异步 MySQL 连接串（密码若含特殊字符需自行 URL 编码）。"""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


settings = Settings()
