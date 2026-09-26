"""Persistent AI Configuration, Provider Credentials, and Telemetry Manager"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai_model_config.json")

# Known keyless platforms requiring zero authentication
KEYLESS_PLATFORMS = {"kilo", "pollinations", "aihorde", "ovh", "custom"}

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
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    
    # Provider credential store & toggles
    provider_keys: Dict[str, str] = Field(default_factory=dict)
    provider_enabled: Dict[str, bool] = Field(default_factory=dict)
    provider_base_urls: Dict[str, str] = Field(default_factory=dict)

    # Usage & analytics telemetry
    monthly_tokens_used: int = 0
    daily_requests_count: int = 0
    per_model_usage: Dict[str, int] = Field(default_factory=dict)
    last_usage_reset_date: str = ""

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
                api_key=openai_key,
                provider_keys={"openai": openai_key}
            )

        return AIModelConfig()

    def get_config(self) -> AIModelConfig:
        return self._config

    def get_provider_key(self, platform: str) -> str:
        """Resolves the best available API key for a given provider platform."""
        platform_lower = platform.lower()
        if platform_lower in KEYLESS_PLATFORMS:
            return ""

        # 1. Check explicit provider_keys store
        if platform_lower in self._config.provider_keys and self._config.provider_keys[platform_lower].strip():
            return self._config.provider_keys[platform_lower].strip()

        # 2. Check active config api_key if provider matches
        if self._config.active_provider.lower() == platform_lower and self._config.api_key.strip():
            return self._config.api_key.strip()

        # 3. Check environment variables
        env_map = {
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "cerebras": "CEREBRAS_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "github": "GITHUB_TOKEN",
            "mistral": "MISTRAL_API_KEY",
            "cohere": "COHERE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "nvidia": "NVIDIA_API_KEY",
            "cloudflare": "CLOUDFLARE_API_TOKEN",
            "sambanova": "SAMBANOVA_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY"
        }
        env_var = env_map.get(platform_lower)
        if env_var and os.environ.get(env_var):
            val = os.environ.get(env_var, "").strip()
            if val and not val.startswith("mock-"):
                return val

        return ""

    def is_provider_enabled(self, platform: str) -> bool:
        """Determines whether a provider is enabled (default is True unless toggled off)."""
        return self._config.provider_enabled.get(platform.lower(), True)

    def is_keyless(self, platform: str) -> bool:
        return platform.lower() in KEYLESS_PLATFORMS

    def set_provider_key(self, platform: str, key: str, base_url: Optional[str] = None):
        """Sets or updates the credential for a specific provider platform."""
        plat = platform.lower()
        keys = dict(self._config.provider_keys)
        if key:
            keys[plat] = key.strip()
        else:
            keys.pop(plat, None)
        
        updates: Dict[str, Any] = {"provider_keys": keys}
        if base_url:
            base_urls = dict(self._config.provider_base_urls)
            base_urls[plat] = base_url.strip()
            updates["provider_base_urls"] = base_urls

        # If current active provider, also update active api_key
        if self._config.active_provider.lower() == plat:
            updates["api_key"] = key.strip() if key else ""

        self.update_config(updates)

    def toggle_provider(self, platform: str, enabled: bool):
        """Enables or disables a provider platform."""
        plat = platform.lower()
        provider_enabled = dict(self._config.provider_enabled)
        provider_enabled[plat] = enabled
        self.update_config({"provider_enabled": provider_enabled})

    def record_usage(self, model_id: str, tokens: int = 150):
        """Records token and request usage for live dashboard telemetry."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_reqs = self._config.daily_requests_count
        monthly_tokens = self._config.monthly_tokens_used

        # Reset daily counter if day changed
        if self._config.last_usage_reset_date != today_str:
            daily_reqs = 0

        daily_reqs += 1
        monthly_tokens += max(1, tokens)

        per_model = dict(self._config.per_model_usage)
        per_model[model_id] = per_model.get(model_id, 0) + max(1, tokens)

        self.update_config({
            "daily_requests_count": daily_reqs,
            "monthly_tokens_used": monthly_tokens,
            "per_model_usage": per_model,
            "last_usage_reset_date": today_str
        })

    def get_usage_metrics(self) -> Dict[str, Any]:
        """Returns monthly and daily usage telemetry formatted for the UI."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_reqs = self._config.daily_requests_count
        if self._config.last_usage_reset_date != today_str:
            daily_reqs = 0

        return {
            "tokens_this_month": self._config.monthly_tokens_used,
            "requests_today": daily_reqs,
            "per_model_usage": self._config.per_model_usage,
            "headline": f"{self._config.monthly_tokens_used:,} tok this month · {daily_reqs} req today"
        }

    def get_public_config(self) -> Dict[str, Any]:
        """Returns configuration with masked API keys for secure frontend consumption."""
        cfg = self._config.model_dump()
        raw_key = self.get_provider_key(self._config.active_provider) or cfg.get("api_key", "")
        
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
            
        cfg["has_api_key"] = bool(raw_key) or self.is_keyless(self._config.active_provider)
        cfg["has_freellmapi_token"] = bool(raw_fla)
        cfg.pop("api_key", None)
        cfg.pop("freellmapi_token", None)
        cfg.pop("provider_keys", None)  # Hide raw credentials
        return cfg

    def update_config(self, new_data: Dict[str, Any]) -> AIModelConfig:
        current_dict = self._config.model_dump()
        
        # If empty api_key is submitted, preserve existing non-empty key unless explicitly cleared
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
