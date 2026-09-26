"""Unit Tests for PulseRadar AI Model Catalog, Modalities, Keys Manager, and Telemetry"""
import pytest
from app.engine.model_catalog import ModelCatalogEngine, PROVIDERS_DIRECTORY, CATALOG_MODELS
from app.core.ai_config import AIConfigManager
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_providers_directory_completeness():
    assert len(PROVIDERS_DIRECTORY) >= 34
    for key, p in PROVIDERS_DIRECTORY.items():
        assert p.name
        assert p.platform
        assert p.monthly_free_tokens
        assert p.rate_limit_summary
        assert p.key_setup_guide

def test_model_catalog_filters():
    # 1. Reasoning filter
    reasoning_models = ModelCatalogEngine.filter_models(capability="reasoning")
    assert len(reasoning_models) > 0
    assert all(m["is_reasoning"] for m in reasoning_models)

    # 2. Context window filter (1M+)
    million_ctx = ModelCatalogEngine.filter_models(min_context=1_000_000)
    assert len(million_ctx) > 0
    assert all(m["context_window"] >= 1_000_000 for m in million_ctx)

    # 3. Provider filter (Groq)
    groq_models = ModelCatalogEngine.filter_models(provider="groq")
    assert len(groq_models) > 0
    assert all(m["platform"] == "groq" for m in groq_models)

    # 4. Search query
    gemini_models = ModelCatalogEngine.filter_models(query="gemini")
    assert len(gemini_models) > 0
    assert any("gemini" in m["display_name"].lower() for m in gemini_models)

    # 5. Modality filtering
    chat_models = ModelCatalogEngine.filter_models(modality="chat")
    assert len(chat_models) >= 40
    assert all(m.get("modality", "chat") == "chat" for m in chat_models)

    embedding_models = ModelCatalogEngine.filter_models(modality="embedding")
    assert len(embedding_models) >= 5
    assert all(m.get("modality") == "embedding" for m in embedding_models)

    image_models = ModelCatalogEngine.filter_models(modality="image")
    assert len(image_models) >= 4
    assert all(m.get("modality") == "image" for m in image_models)

    audio_models = ModelCatalogEngine.filter_models(modality="audio")
    assert len(audio_models) >= 3
    assert all(m.get("modality") == "audio" for m in audio_models)

    fusion_models = ModelCatalogEngine.filter_models(modality="fusion")
    assert len(fusion_models) >= 1
    assert all(m.get("modality") == "fusion" for m in fusion_models)

def test_ai_config_manager():
    mgr = AIConfigManager.get_instance()
    cfg = mgr.get_config()
    assert cfg.active_model_id
    
    public_cfg = mgr.get_public_config()
    assert "api_key" not in public_cfg
    assert "has_api_key" in public_cfg

    # Key resolution
    assert mgr.is_keyless("kilo")
    assert mgr.is_keyless("pollinations")
    assert mgr.is_keyless("ovh")
    assert not mgr.is_keyless("google")

    # Usage tracking
    initial_metrics = mgr.get_usage_metrics()
    mgr.record_usage("groq/llama-3.3-70b-versatile", 250)
    updated_metrics = mgr.get_usage_metrics()
    assert updated_metrics["tokens_this_month"] >= initial_metrics["tokens_this_month"] + 250
    assert updated_metrics["requests_today"] >= 1

def test_api_routes():
    # 1. Test /models endpoint with modality filter
    res = client.get("/api/v1/models?modality=chat")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 40

    # 2. Test /models/usage endpoint
    res_usage = client.get("/api/v1/models/usage")
    assert res_usage.status_code == 200
    usage_data = res_usage.json()
    assert "tokens_this_month" in usage_data
    assert "requests_today" in usage_data

    # 3. Test /models/keys endpoint
    res_keys = client.get("/api/v1/models/keys")
    assert res_keys.status_code == 200
    keys_data = res_keys.json()
    assert keys_data["count"] >= 34
    assert "healthy_count" in keys_data
    assert "needs_key_count" in keys_data

    # 4. Test missing key error handling (no illegal header exception!)
    res_test = client.post("/api/v1/models/test", json={
        "prompt": "Test hello",
        "provider": "groq",
        "model_id": "groq/llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": ""
    })
    assert res_test.status_code == 200
    test_json = res_test.json()
    # It must return a graceful error status with 401 or needs_key, NOT crash with Illegal header
    assert test_json["status"] in ["error", "needs_key"]
    if test_json.get("status_code") == 401:
        assert "requires an API key" in test_json.get("error", "")
