"""
配置管理模块
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """系统配置"""
    
    # OpenAI配置
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # 监控系统配置
    monitor_grpc_host: str = Field("localhost", env="MONITOR_GRPC_HOST")
    monitor_grpc_port: int = Field(50051, env="MONITOR_GRPC_PORT")
    
    # 向量数据库配置
    chroma_persist_directory: str = Field("./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    chroma_collection_name: str = Field("linux_monitoring_kb", env="CHROMA_COLLECTION_NAME")
    
    # Redis配置
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # 告警配置
    alert_webhook_url: Optional[str] = Field(None, env="ALERT_WEBHOOK_URL")
    alert_email_smtp_host: str = Field("smtp.gmail.com", env="ALERT_EMAIL_SMTP_HOST")
    alert_email_smtp_port: int = Field(587, env="ALERT_EMAIL_SMTP_PORT")
    alert_email_user: Optional[str] = Field(None, env="ALERT_EMAIL_USER")
    alert_email_password: Optional[str] = Field(None, env="ALERT_EMAIL_PASSWORD")
    
    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # 分析配置
    cpu_threshold_warning: float = Field(80.0, env="CPU_THRESHOLD_WARNING")
    cpu_threshold_critical: float = Field(95.0, env="CPU_THRESHOLD_CRITICAL")
    memory_threshold_warning: float = Field(85.0, env="MEMORY_THRESHOLD_WARNING")
    memory_threshold_critical: float = Field(95.0, env="MEMORY_THRESHOLD_CRITICAL")
    load_threshold_warning: float = Field(4.0, env="LOAD_THRESHOLD_WARNING")
    load_threshold_critical: float = Field(8.0, env="LOAD_THRESHOLD_CRITICAL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
settings = Settings()
