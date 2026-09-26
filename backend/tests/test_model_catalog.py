"""Unit Tests for PulseRadar AI Model Catalog and FreeLLMAPI Integration"""
import pytest
from app.engine.model_catalog import ModelCatalogEngine, PROVIDERS_DIRECTORY, CATALOG_MODELS
from app.core.ai_config import AIConfigManager

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

def test_ai_config_manager():
    mgr = AIConfigManager.get_instance()
    cfg = mgr.get_config()
    assert cfg.active_model_id
    
    public_cfg = mgr.get_public_config()
    assert "api_key" not in public_cfg
    assert "has_api_key" in public_cfg
