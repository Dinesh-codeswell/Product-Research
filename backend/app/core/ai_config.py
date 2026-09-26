"""Persistent AI Configuration and Active Model Selection Manager"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai_model_config.json")

class AIModelConfig(BaseModel):
    active_model_id: str = "groq/llama-3.3-70b-versatile"
    active_provider: str = "groq"
    active_model_name: str = "Llama 3.3 70B Versatile"
    base_url: str = "https://api.groq.com/openai/v1"
    api_key: str = ""
    routing_strategy: str = "balanced"  # balanced, fastest, smartest, free_quota, custom
    temperature: float = 0.3
    max_tokens: int = 4096
    use_freellmapi_gateway: bool = False
    freellmapi_gateway_url: str = "http://localhost:3001/v1"
    freellmapi_token: str = ""
    custom_headers: Dict[str, str] = {}

class AIConfigManager:
    _instance: Optional["AIConfigManager"] = None
    _config: AIModelConfig

    def __init__(self):
        self._config = self._load_config()

    @classmethod
    def get_instance(cls) -> "AIConfigManager":
        if cls._instance is None:
            cls._instance = AIConfigManager()
        return cls._instance

    def _load_config(self) -> AIModelConfig:
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AIModelConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load AI config from {CONFIG_FILE_PATH}: {e}. Using defaults.")

        # Default fallback: check if OpenAI key is set in env, else default to Groq free
        openai_key = getattr(settings, "OPENAI_API_KEY", "")
        if openai_key and not openai_key.startswith("mock-"):
            return AIModelConfig(
                active_model_id="openai/gpt-4o-mini",
                active_provider="openai",
                active_model_name="GPT-4o Mini",
                base_url="https://api.openai.com/v1",
                api_key=openai_key
            )

        return AIModelConfig()

    def get_config(self) -> AIModelConfig:
        return self._config

    def get_public_config(self) -> Dict[str, Any]:
        """Returns configuration with masked API keys for secure frontend consumption."""
        cfg = self._config.model_dump()
        raw_key = cfg.get("api_key", "")
        if raw_key and len(raw_key) > 8:
            cfg["masked_api_key"] = f"{raw_key[:4]}...{raw_key[-4:]}"
        elif raw_key:
            cfg["masked_api_key"] = "****"
        else:
            cfg["masked_api_key"] = ""
        
        raw_fla = cfg.get("freellmapi_token", "")
        if raw_fla and len(raw_fla) > 8:
            cfg["masked_freellmapi_token"] = f"{raw_fla[:4]}...{raw_fla[-4:]}"
        else:
            cfg["masked_freellmapi_token"] = ""
            
        cfg["has_api_key"] = bool(raw_key)
        cfg["has_freellmapi_token"] = bool(raw_fla)
        cfg.pop("api_key", None)
        cfg.pop("freellmapi_token", None)
        return cfg

    def update_config(self, new_data: Dict[str, Any]) -> AIModelConfig:
        current_dict = self._config.model_dump()
        
        # If empty api_key is submitted, preserve existing non-empty key
        if "api_key" in new_data and not new_data["api_key"] and current_dict.get("api_key"):
            new_data.pop("api_key")
            
        if "freellmapi_token" in new_data and not new_data["freellmapi_token"] and current_dict.get("freellmapi_token"):
            new_data.pop("freellmapi_token")

        current_dict.update(new_data)
        updated = AIModelConfig(**current_dict)
        self._config = updated

        # Persist to disk
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(updated.model_dump(), f, indent=2)
            logger.info(f"Updated AI configuration saved to {CONFIG_FILE_PATH} (Active Model: {updated.active_model_id})")
        except Exception as e:
            logger.error(f"Error persisting AI config: {e}")

        return self._config
