"""Application settings and configuration"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    model_config = SettingsConfigDict(env_prefix='DATABASE')

    host: str = Field('localhost', alias='HOST')
    port: int = Field(5432, alias='PORT')
    database: str = Field('gozcu', alias='NAME')
    user: str = Field('postgres', alias='USER')
    password: str = Field('postgres', alias='PASSWORD')
    pool_size: int = Field(10, alias='POOL_SIZE')


class RedisSettings(BaseSettings):
    """Redis configuration settings"""
    model_config = SettingsConfigDict(env_prefix='REDIS_')

    host: str = Field(default='localhost', description='Redis host')
    port: int = Field(default=6379, description='Redis port')
    stream_key: str = Field(default='camera_events', description='Redis stream key')
    consumer_group: str = Field(default='processor_group', description='Consumer group name')
    consumer_name: str = Field(default='processor_1', description='Consumer name')


class ProcessingSettings(BaseSettings):
    """Processing configuration settings"""
    model_config = SettingsConfigDict(env_prefix='PROCESSING_')

    batch_size: int = Field(default=100, description='Batch size for processing')
    batch_timeout_seconds: float = Field(default=5.0, description='Batch timeout in seconds')
    max_retries: int = Field(default=3, description='Maximum retry attempts')


class LogSettings(BaseSettings):
    """Logging configuration settings"""
    model_config = SettingsConfigDict(env_prefix='LOG_')

    log_level: str = Field(default='INFO', description='Logging level')


class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    log: LogSettings = Field(default_factory=LogSettings)


@lru_cache
def get_settings() -> Settings:
    """Get settings instance (singleton pattern)"""
    return Settings()


# Export singleton instance
settings = get_settings()
