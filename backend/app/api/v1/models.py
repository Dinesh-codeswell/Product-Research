"""PulseRadar AI Models & FreeLLMAPI Integration API Router"""
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
import httpx

from app.engine.model_catalog import ModelCatalogEngine
from app.core.ai_config import AIConfigManager, AIModelConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["AI Models & Free Tier"])

class UpdateConfigPayload(BaseModel):
    active_model_id: Optional[str] = None
    active_provider: Optional[str] = None
    active_model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    routing_strategy: Optional[str] = None
    temperature: Optional[float] = None
    use_freellmapi_gateway: Optional[bool] = None
    freellmapi_gateway_url: Optional[str] = None
    freellmapi_token: Optional[str] = None

class TestModelPayload(BaseModel):
    prompt: str = "Explain what product friction is in two sentences."
    model_id: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None

@router.get("", summary="List & Filter AI Models")
async def list_models(
    q: Optional[str] = Query(None, description="Search term for model name or provider"),
    provider: Optional[str] = Query(None, description="Filter by provider platform (e.g. google, groq, cerebras)"),
    capability: Optional[str] = Query(None, description="Filter by capability: vision, tools, reasoning, coding, speed, massive_context"),
    min_context: Optional[int] = Query(None, description="Minimum context window in tokens (e.g. 32000, 128000, 1000000)"),
    free_only: bool = Query(False, description="Filter to free tiers requiring no credit card"),
    sort_by: str = Query("smartest", description="Sort order: smartest, fastest, context, free_budget")
):
    """Retrieves models from the catalog filtered by provider, capabilities, context window, and speed."""
    models = ModelCatalogEngine.filter_models(
        query=q,
        provider=provider,
        capability=capability,
        min_context=min_context,
        free_only=free_only,
        sort_by=sort_by
    )
    return {
        "count": len(models),
        "models": models
    }

@router.get("/providers", summary="34 Free LLM Providers Knowledge Base")
async def get_providers():
    """Returns knowledge base of all 34 free LLM providers with free-tier quotas and setup guides."""
    providers = ModelCatalogEngine.get_providers()
    return {
        "count": len(providers),
        "providers": providers
    }

@router.get("/stats", summary="Catalog Aggregate Statistics")
async def get_stats():
    """Returns aggregate stats on free inference tokens, endpoint count, and provider distribution."""
    return ModelCatalogEngine.get_statistics()

@router.get("/config", summary="Get Current AI Engine Settings")
async def get_active_config():
    """Returns the current active synthesis model and provider settings (with masked credentials)."""
    return AIConfigManager.get_instance().get_public_config()

@router.post("/config", summary="Update AI Engine Settings")
async def update_active_config(payload: UpdateConfigPayload):
    """Updates active model, provider, API key, or FreeLLMAPI gateway settings."""
    update_dict = {k: v for k, v in payload.model_dump().items() if v is not None}
    
    # Auto-resolve provider display name and base URL if model_id provided
    if "active_model_id" in update_dict and not update_dict.get("base_url"):
        model_meta = ModelCatalogEngine.get_model_by_id(update_dict["active_model_id"])
        if model_meta:
            update_dict["active_provider"] = model_meta.platform
            update_dict["active_model_name"] = model_meta.display_name
            if not update_dict.get("use_freellmapi_gateway"):
                update_dict["base_url"] = model_meta.base_url

    AIConfigManager.get_instance().update_config(update_dict)
    return {
        "status": "success",
        "message": "AI configuration updated successfully",
        "config": AIConfigManager.get_instance().get_public_config()
    }

@router.post("/test", summary="Test Inference on Selected Model Endpoint")
async def test_model_inference(payload: TestModelPayload):
    """Executes a short test inference against the selected model/provider to verify connectivity and measure latency."""
    cfg = AIConfigManager.get_instance().get_config()
    
    # Resolve parameters from payload or active config
    provider = payload.provider or cfg.active_provider
    model_id = payload.model_id or cfg.active_model_id
    base_url = payload.base_url or cfg.base_url
    api_key = payload.api_key or cfg.api_key
    
    if cfg.use_freellmapi_gateway and not payload.base_url:
        base_url = cfg.freellmapi_gateway_url
        api_key = cfg.freellmapi_token or "freellmapi-local"

    # Normalize endpoint URL
    base_url = base_url.rstrip("/")
    endpoint_url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url

    # Strip platform prefix for wire call if needed
    wire_model = model_id.split("/")[-1] if ("/" in model_id and provider not in ["openrouter", "github"]) else model_id

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://pulseradar.local"
        headers["X-Title"] = "PulseRadar Connection Test"

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                endpoint_url,
                headers=headers,
                json={
                    "model": wire_model,
                    "messages": [{"role": "user", "content": payload.prompt}],
                    "max_tokens": 150,
                    "temperature": 0.2
                }
            )
            latency_ms = int((time.time() - start_time) * 1000)

            if resp.status_code != 200:
                return {
                    "status": "error",
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms,
                    "error": resp.text[:500],
                    "endpoint_tested": endpoint_url,
                    "model_tested": wire_model
                }

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return {
                "status": "success",
                "status_code": 200,
                "latency_ms": latency_ms,
                "response": content,
                "usage": usage,
                "served_model": data.get("model", wire_model),
                "endpoint_tested": endpoint_url
            }

    except httpx.ConnectError:
        return {
            "status": "error",
            "latency_ms": int((time.time() - start_time) * 1000),
            "error": f"Failed to connect to {endpoint_url}. Is the service running?",
            "endpoint_tested": endpoint_url,
            "model_tested": wire_model
        }
    except Exception as e:
        return {
            "status": "error",
            "latency_ms": int((time.time() - start_time) * 1000),
            "error": str(e),
            "endpoint_tested": endpoint_url,
            "model_tested": wire_model
        }
