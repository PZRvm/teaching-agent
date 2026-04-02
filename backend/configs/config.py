from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # LLM 配置（默认硅基流动）
    openai_api_key: str
    openai_base_url: str = "https://api.siliconflow.cn/v1"
    openai_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./database.db"

    # 向量数据库配置
    chroma_persist_dir: str = "./chroma_db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
