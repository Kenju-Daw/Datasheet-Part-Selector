"""
Configuration management for Datasheet Part Selector
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./datasheet_selector.db"
    
    # Gemini API
    gemini_api_key: str = ""
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    datasheets_dir: Path = base_dir / "datasheets"
    
    # Distributor APIs (optional)
    digikey_client_id: str = ""
    digikey_client_secret: str = ""
    mouser_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
