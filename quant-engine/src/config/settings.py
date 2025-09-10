"""全局配置管理模块"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # 应用基础配置
    app_name: str = Field(default="quant-engine", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")

    # 服务配置
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=8002, description="服务监听端口")

    # MySQL数据库配置
    mysql_host: str = Field(default="localhost", description="MySQL主机地址")
    mysql_port: int = Field(default=3306, description="MySQL端口")
    mysql_user: str = Field(default="qtrade", description="MySQL用户名")
    mysql_password: str = Field(default="qtrade123", description="MySQL密码")
    mysql_database: str = Field(default="qtrade", description="MySQL数据库名")
    mysql_charset: str = Field(default="utf8mb4", description="MySQL字符集")

    # Redis配置
    redis_host: str = Field(default="localhost", description="Redis主机地址")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_password: str | None = Field(default=None, description="Redis密码")
    redis_db: int = Field(default=0, description="Redis数据库索引")

    # data-collector服务配置
    data_collector_base_url: str = Field(
        default="http://localhost:8080", description="data-collector服务基础URL"
    )
    data_collector_timeout: int = Field(default=30, description="请求超时时间（秒）")

    # Tushare配置
    tushare_token: str = Field(default="", description="Tushare API Token")
    tushare_timeout: int = Field(default=30, description="Tushare请求超时时间（秒）")
    tushare_retry_count: int = Field(default=3, description="Tushare请求重试次数")
    tushare_retry_delay: float = Field(default=1.0, description="Tushare请求重试延迟（秒）")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str | None = Field(default=None, description="日志文件路径")

    # 缓存配置
    cache_ttl: int = Field(default=3600, description="缓存过期时间（秒）")

    # NLP模型配置
    finbert_model_name: str = Field(
        default="ProsusAI/finbert", description="FinBERT模型名称"
    )
    model_cache_dir: str | None = Field(default="./models", description="模型缓存目录")

    @property
    def mysql_url(self) -> str:
        """获取MySQL连接URL"""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# 全局配置实例
settings = Settings()
