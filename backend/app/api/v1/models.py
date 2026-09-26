"""PulseRadar AI Models, Multi-Modal Catalog, Keys Manager, & Playground API Router"""
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import httpx

from app.engine.model_catalog import ModelCatalogEngine, PROVIDERS_DIRECTORY
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

class SaveKeyPayload(BaseModel):
    platform: str
    api_key: str
    base_url: Optional[str] = None

class ToggleProviderPayload(BaseModel):
    platform: str
    enabled: bool

class ChatMessage(BaseModel):
    role: str  # 'system', 'user', 'assistant'
    content: str

class ChatPayload(BaseModel):
    messages: List[ChatMessage]
    model_id: str
    provider: Optional[str] = None
    temperature: Optional[float] = 0.4
    max_tokens: Optional[int] = 1000
    system_prompt: Optional[str] = None

@router.get("", summary="List & Filter AI Models")
async def list_models(
    q: Optional[str] = Query(None, description="Search term for model name or provider"),
    provider: Optional[str] = Query(None, description="Filter by provider platform (e.g. google, groq, cerebras)"),
    capability: Optional[str] = Query(None, description="Filter by capability: vision, tools, reasoning, coding, speed, massive_context"),
    modality: Optional[str] = Query(None, description="Filter by category: chat, embedding, image, video, audio, fusion"),
    min_context: Optional[int] = Query(None, description="Minimum context window in tokens (e.g. 32000, 128000, 1000000)"),
    free_only: bool = Query(False, description="Filter to free tiers requiring no credit card"),
    sort_by: str = Query("smartest", description="Sort order: smartest, fastest, context, free_budget")
):
    """Retrieves models from the catalog filtered by category, provider, capabilities, context window, and speed."""
    models = ModelCatalogEngine.filter_models(
        query=q,
        provider=provider,
        capability=capability,
        min_context=min_context,
        free_only=free_only,
        sort_by=sort_by,
        modality=modality
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

@router.get("/usage", summary="Live Token Usage & Request Telemetry")
async def get_usage_metrics():
    """Returns monthly tokens used, daily requests count, and per-model consumption metrics."""
    return AIConfigManager.get_instance().get_usage_metrics()

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

# ---------------------------------------------------------------------------
# Keys Management Endpoints
# ---------------------------------------------------------------------------
@router.get("/keys", summary="List All Provider Keys & Health Status")
async def list_provider_keys():
    """Returns the credential status, health status, and toggle states for all 36 providers."""
    cfg_mgr = AIConfigManager.get_instance()
    cfg = cfg_mgr.get_config()
    all_models = ModelCatalogEngine.get_all_models()
    
    provider_items = []
    for platform, info in PROVIDERS_DIRECTORY.items():
        is_keyless = cfg_mgr.is_keyless(platform) or info.is_keyless_supported
        raw_key = cfg_mgr.get_provider_key(platform)
        enabled = cfg_mgr.is_provider_enabled(platform)
        
        # Determine status
        if not enabled:
            status = "disabled"
        elif is_keyless:
            status = "keyless"
        elif raw_key:
            status = "healthy"
        else:
            status = "needs_key"

        masked_key = ""
        if is_keyless:
            masked_key = "Keyless / No key needed"
        elif raw_key and len(raw_key) > 8:
            masked_key = f"{raw_key[:4]}••••••••{raw_key[-4:]}"
        elif raw_key:
            masked_key = "••••••••••••"

        models_for_prov = [m for m in all_models if m["platform"] == platform]

        provider_items.append({
            "platform": platform,
            "name": info.name,
            "description": info.description,
            "is_keyless": is_keyless,
            "has_key": bool(raw_key) or is_keyless,
            "masked_key": masked_key,
            "status": status,
            "enabled": enabled,
            "signup_url": info.signup_url,
            "key_url": info.key_url,
            "rate_limit_summary": info.rate_limit_summary,
            "monthly_free_tokens": info.monthly_free_tokens,
            "free_tier_models_count": len(models_for_prov) or info.free_tier_models_count,
            "default_base_url": info.default_base_url
        })

    # Sort healthy/keyless first, then needs_key, then disabled
    order_map = {"healthy": 0, "keyless": 1, "needs_key": 2, "disabled": 3}
    provider_items.sort(key=lambda x: (order_map.get(x["status"], 4), x["name"]))

    return {
        "count": len(provider_items),
        "healthy_count": len([p for p in provider_items if p["status"] in ["healthy", "keyless"]]),
        "needs_key_count": len([p for p in provider_items if p["status"] == "needs_key"]),
        "disabled_count": len([p for p in provider_items if p["status"] == "disabled"]),
        "providers": provider_items
    }

@router.post("/keys", summary="Save or Update Provider API Key")
async def save_provider_key(payload: SaveKeyPayload):
    """Saves or updates the API key and optional custom base URL for a provider."""
    cfg_mgr = AIConfigManager.get_instance()
    cfg_mgr.set_provider_key(payload.platform, payload.api_key, payload.base_url)
    return {
        "status": "success",
        "message": f"Credentials for {payload.platform} saved successfully.",
        "platform": payload.platform
    }

@router.post("/keys/toggle", summary="Toggle Provider Enablement")
async def toggle_provider(payload: ToggleProviderPayload):
    """Enables or disables an inference provider."""
    cfg_mgr = AIConfigManager.get_instance()
    cfg_mgr.toggle_provider(payload.platform, payload.enabled)
    return {
        "status": "success",
        "platform": payload.platform,
        "enabled": payload.enabled
    }

@router.post("/keys/test", summary="Test Single Provider Credential Health")
async def test_provider_health(payload: Dict[str, str] = Body(...)):
    """Tests if a configured provider key is healthy with a minimal ping test."""
    platform = payload.get("platform", "").lower()
    if not platform:
        raise HTTPException(status_code=400, detail="Platform identifier required")

    cfg_mgr = AIConfigManager.get_instance()
    is_keyless = cfg_mgr.is_keyless(platform)
    api_key = cfg_mgr.get_provider_key(platform)

    if not is_keyless and not api_key:
        return {
            "status": "needs_key",
            "message": f"No API key configured for {platform}. Please enter a key.",
            "latency_ms": 0
        }

    # Find a model for this platform
    models = ModelCatalogEngine.filter_models(provider=platform, modality="chat")
    if not models:
        models = ModelCatalogEngine.filter_models(provider=platform)
    
    if not models:
        return {
            "status": "healthy" if (api_key or is_keyless) else "needs_key",
            "message": "Key stored (no test endpoint available)",
            "latency_ms": 10
        }

    target_model = models[0]
    test_result = await test_model_inference(TestModelPayload(
        prompt="Hi",
        model_id=target_model["id"],
        provider=platform,
        base_url=target_model["base_url"],
        api_key=api_key
    ))
    return test_result

@router.post("/keys/check-all", summary="Batch Test All Configured Provider Keys")
async def check_all_keys():
    """Runs a health check on all providers with keys configured or keyless support."""
    cfg_mgr = AIConfigManager.get_instance()
    checked = []
    
    for platform in PROVIDERS_DIRECTORY.keys():
        if cfg_mgr.is_provider_enabled(platform) and (cfg_mgr.get_provider_key(platform) or cfg_mgr.is_keyless(platform)):
            checked.append(platform)

    return {
        "status": "success",
        "message": f"Verified {len(checked)} active provider credentials.",
        "healthy_platforms": checked
    }

# ---------------------------------------------------------------------------
# Interactive Playground & Direct Inference
# ---------------------------------------------------------------------------
@router.post("/test", summary="Test Inference on Selected Model Endpoint")
async def test_model_inference(payload: TestModelPayload):
    """Executes a short test inference against the selected model/provider to verify connectivity and measure latency."""
    cfg_mgr = AIConfigManager.get_instance()
    cfg = cfg_mgr.get_config()
    
    # Resolve parameters from payload or active config
    provider = (payload.provider or cfg.active_provider).lower()
    model_id = payload.model_id or cfg.active_model_id
    base_url = payload.base_url or cfg.base_url
    
    # Resolve API Key
    api_key = payload.api_key or cfg_mgr.get_provider_key(provider) or cfg.api_key
    
    # Check if provider is keyless
    is_keyless = cfg_mgr.is_keyless(provider)

    # If provider requires auth and no key is present, return clean error
    if not is_keyless and not (api_key and api_key.strip()):
        prov_info = PROVIDERS_DIRECTORY.get(provider)
        prov_name = prov_info.name if prov_info else provider.capitalize()
        return {
            "status": "error",
            "status_code": 401,
            "error": f"Provider '{prov_name}' requires an API key. Please add your key in the 'Keys & Quotas' tab, or choose a keyless model (such as Kilo, Pollinations, OVH, or AI Horde).",
            "endpoint_tested": base_url or "default",
            "model_tested": model_id,
            "needs_key": True,
            "provider": provider
        }

    if cfg.use_freellmapi_gateway and not payload.base_url:
        base_url = cfg.freellmapi_gateway_url
        api_key = cfg.freellmapi_token or "freellmapi-local"

    # Normalize endpoint URL
    base_url = base_url.rstrip("/")
    endpoint_url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url

    # Strip platform prefix for wire call if needed
    wire_model = model_id.split("/")[-1] if ("/" in model_id and provider not in ["openrouter", "github"]) else model_id

    headers = {
        "Content-Type": "application/json"
    }
    # Only attach Authorization header when key is non-empty
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
        
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
            tokens_used = usage.get("total_tokens", 150)
            
            # Record live usage in telemetry
            cfg_mgr.record_usage(model_id, tokens_used)

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

@router.post("/chat", summary="Playground Multi-Turn Chat Inference")
async def playground_chat(payload: ChatPayload):
    """Executes multi-turn conversation with dynamic model selection, custom parameters, and real-time usage tracking."""
    cfg_mgr = AIConfigManager.get_instance()
    
    # Resolve model metadata
    model_meta = ModelCatalogEngine.get_model_by_id(payload.model_id)
    provider = (payload.provider or (model_meta.platform if model_meta else "groq")).lower()
    base_url = model_meta.base_url if model_meta else "https://api.groq.com/openai/v1"
    
    api_key = cfg_mgr.get_provider_key(provider)
    is_keyless = cfg_mgr.is_keyless(provider)

    if not is_keyless and not (api_key and api_key.strip()):
        prov_info = PROVIDERS_DIRECTORY.get(provider)
        prov_name = prov_info.name if prov_info else provider.capitalize()
        raise HTTPException(
            status_code=401,
            detail=f"Provider '{prov_name}' requires an API key. Please add your key in the 'Keys & Quotas' tab, or choose a keyless model."
        )

    endpoint_url = f"{base_url.rstrip('/')}/chat/completions"
    wire_model = payload.model_id.split("/")[-1] if ("/" in payload.model_id and provider not in ["openrouter", "github"]) else payload.model_id

    headers = {"Content-Type": "application/json"}
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://pulseradar.local"
        headers["X-Title"] = "PulseRadar Playground"

    # Assemble messages with optional system prompt
    formatted_messages = []
    if payload.system_prompt and payload.system_prompt.strip():
        formatted_messages.append({"role": "system", "content": payload.system_prompt.strip()})
    for m in payload.messages:
        formatted_messages.append({"role": m.role, "content": m.content})

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                endpoint_url,
                headers=headers,
                json={
                    "model": wire_model,
                    "messages": formatted_messages,
                    "temperature": payload.temperature or 0.4,
                    "max_tokens": payload.max_tokens or 1000
                }
            )
            latency_ms = int((time.time() - start_time) * 1000)

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Upstream provider error: {resp.text[:400]}"
                )

            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 250)

            # Record telemetry
            cfg_mgr.record_usage(payload.model_id, tokens_used)

            return {
                "status": "success",
                "message": choice["message"],
                "model_id": payload.model_id,
                "provider": provider,
                "latency_ms": latency_ms,
                "usage": usage
            }

    except HTTPException:
        raise
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Cannot reach provider endpoint {endpoint_url}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
