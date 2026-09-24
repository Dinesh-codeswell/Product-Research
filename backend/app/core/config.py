"""PulseRadar Core Configuration with Multi-Platform Credentials"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PulseRadar"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulseradar.db"
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # "openai", "anthropic", "ollama", "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Platform Credentials (Optional for enhanced rate limits & authenticated search)
    TWITTER_AUTH_TOKEN: str = ""
    TWITTER_CT0: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    
    FACEBOOK_C_USER: str = ""
    FACEBOOK_XS: str = ""
    
    GITHUB_TOKEN: str = ""
    
    # Firecrawl API for Deep Web Markdown Scraping & LLM Bundle Generation
    FIRECRAWL_API_KEY: str = ""
    FIRECRAWL_BASE_URL: str = "https://api.firecrawl.dev"
    
    # Ingestion Scope & Limits
    MAX_ITEMS_PER_CHANNEL: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30
    REDDIT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PulseRadar/1.0"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
