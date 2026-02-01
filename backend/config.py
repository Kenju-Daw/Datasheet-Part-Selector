"""
Configuration management for Datasheet Part Selector
"""
import json
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional


# User settings file location
USER_SETTINGS_FILE = Path(__file__).parent / "user_settings.json"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./datasheet_selector.db"
    
    # Gemini API (from .env - can be overridden by user settings)
    gemini_api_key: str = ""
    
    # OpenRouter API (from .env - can be overridden by user settings)
    openrouter_api_key: str = ""
    
    # Active LLM provider
    active_llm_provider: Literal["google", "openrouter"] = "google"
    
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


def load_user_settings() -> dict:
    """Load user settings from JSON file"""
    if USER_SETTINGS_FILE.exists():
        try:
            with open(USER_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def get_effective_api_key(provider: Optional[str] = None) -> tuple[str, str, Optional[str]]:
    """
    Get the effective API key based on user settings and provider.
    Returns (api_key, provider, model_id) tuple.
    """
    user_settings = load_user_settings()
    base_settings = get_settings()
    
    # Determine active provider
    active_provider = provider or user_settings.get("active_provider", base_settings.active_llm_provider)
    
    # Get selected model (if any)
    selected_model = user_settings.get("selected_model")
    
    if active_provider == "openrouter":
        # Prefer user settings, fall back to .env
        key = user_settings.get("openrouter_api_key") or base_settings.openrouter_api_key
        return (key, "openrouter", selected_model)
    else:
        # Google/Gemini - prefer user settings, fall back to .env
        key = user_settings.get("gemini_api_key") or base_settings.gemini_api_key
        return (key, "google", selected_model)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
