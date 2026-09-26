"""AI Strategic Planner & Multi-Modal Pipeline Integration Engine

Bridges PulseRadar's AI Model Catalog and active provider configurations into:
1. Product Research: Intent decomposition, multi-channel tactical keyword planning, and browser targeting.
2. Browser Agent Control: Community routing, keyword queries, and signal extraction.
3. SEO & GEO Pipeline: AI search engine citation optimization (ChatGPT, Perplexity, Gemini) and SERP meta generation.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional
import httpx

from app.core.ai_config import AIConfigManager
from app.engine.model_catalog import ModelCatalogEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIResearchPlanner:
    def __init__(self):
        self.cfg_mgr = AIConfigManager.get_instance()

    async def _dispatch_llm_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[Dict[str, Any]]:
        """Dispatches an inference request to the currently active configured model and extracts JSON."""
        cfg = self.cfg_mgr.get_config()
        provider = (cfg.active_provider or "groq").lower()
        model_id = cfg.active_model_id

        # Resolve wire model and endpoint
        wire_model = ModelCatalogEngine.resolve_wire_model(model_id, provider)
        base_url = cfg.base_url.rstrip("/") if cfg.base_url else "https://api.openai.com/v1"
        api_key = cfg.api_key or getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            api_key = self.cfg_mgr.get_provider_key(provider)

        is_keyless = self.cfg_mgr.is_keyless(provider)
        if not is_keyless and not (api_key and api_key.strip()):
            logger.info(f"AI Planner: Provider '{provider}' has no active API key. Using rule-based fallback.")
            return None

        endpoint_url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url

        headers = {"Content-Type": "application/json"}
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://pulseradar.local"
            headers["X-Title"] = "PulseRadar AI Planner"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": wire_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1200
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(endpoint_url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"AI Planner upstream error ({resp.status_code}): {resp.text[:200]}")
                    return None
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return None
                raw_content = choices[0].get("message", {}).get("content", "")
                
                # Extract JSON block
                clean_json_str = raw_content
                if "```json" in clean_json_str:
                    clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json_str:
                    clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()
                else:
                    match = re.search(r"(\{.*\})", clean_json_str, re.DOTALL)
                    if match:
                        clean_json_str = match.group(1)

                return json.loads(clean_json_str)
        except Exception as e:
            logger.warning(f"AI Planner dispatch failed ({e}). Reverting to rule-based planner.")
            return None

    async def plan_research_query(self, query: str, channels: List[str]) -> Dict[str, Any]:
        """Analyzes search query intent and creates high-yield channel-specific keywords and subreddits."""
        system_prompt = (
            "You are PulseRadar's Principal Product Discovery & Search Intelligence Agent. "
            "Your job is to deconstruct research queries into high-signal developer keywords and targeted communities. "
            "Always respond with ONLY valid JSON with this exact schema:\n"
            "{\n"
            '  "intent_summary": "string describing core user friction",\n'
            '  "primary_friction_hypotheses": ["hypothesis 1", "hypothesis 2"],\n'
            '  "target_entities": ["tool/competitor 1", "tool/competitor 2"],\n'
            '  "channel_queries": {\n'
            '    "reddit": ["keyword query 1", "keyword query 2"],\n'
            '    "hackernews": ["keyword query 1", "keyword query 2"],\n'
            '    "github": ["keyword query 1", "keyword query 2"],\n'
            '    "twitter": ["keyword query 1", "keyword query 2"],\n'
            '    "youtube": ["keyword query 1", "keyword query 2"],\n'
            '    "google": ["keyword query 1", "keyword query 2"]\n'
            '  },\n'
            '  "recommended_subreddits": ["sub1", "sub2", "sub3"]\n'
            "}"
        )

        user_prompt = (
            f"Target Query: '{query}'\n"
            f"Active Channels to Scrape: {', '.join(channels)}\n\n"
            "Generate short, high-signal search queries (2-4 words) that developers actually use when complaining or discussing alternatives. "
            "Do NOT output long interrogative sentences. Output keyword phrases like 'prisma slow drizzle', 'stripe billing churn', 'auth0 migration cost'."
        )

        plan = await self._dispatch_llm_json(system_prompt, user_prompt, temperature=0.3)
        if plan and isinstance(plan, dict) and "channel_queries" in plan:
            logger.info(f"AI Planner successfully generated search plan for '{query}' using active model.")
            return plan

        # Graceful rule-based fallback
        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        words = clean_q.split()
        short_q = " ".join(words[:4]) if len(words) > 4 else clean_q

        return {
            "intent_summary": f"Discovery research on {query}",
            "primary_friction_hypotheses": [
                f"Configuration complexity in {query}",
                f"Performance bottlenecks and vendor lock-in for {query}"
            ],
            "target_entities": words[:3],
            "channel_queries": {
                ch: [short_q, f"{short_q} alternative", f"{short_q} issues"] for ch in channels
            },
            "recommended_subreddits": ["webdev", "programming", "reactjs", "node", "devops"]
        }

    async def generate_seo_strategic_audit(self, url: str, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Uses the active AI model to generate high-value Generative Engine Optimization (GEO) & SERP insights."""
        system_prompt = (
            "You are PulseRadar's Generative Engine Optimization (GEO) and AI Search Strategist. "
            "You optimize sites for citation by ChatGPT Search, Perplexity AI, Google Gemini, and Claude. "
            "Always respond with ONLY valid JSON with this exact schema:\n"
            "{\n"
            '  "brand_summary": "1-2 sentence core offering summary",\n'
            '  "ai_citation_readiness_verdict": "High | Medium | Low with concise rationale",\n'
            '  "recommended_title_tag": "High-CTR, entity-rich title tag under 60 chars",\n'
            '  "recommended_meta_description": "Compelling SERP description with key benefit under 155 chars",\n'
            '  "high_value_keyword_opportunities": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"],\n'
            '  "ai_search_quotability_actions": [\n'
            '    "Action item 1 to get cited by Perplexity/ChatGPT",\n'
            '    "Action item 2 to structure data for LLM extraction"\n'
            '  ],\n'
            '  "schema_recommendations": ["Organization schema with sameAs", "FAQPage schema with direct answers"]\n'
            "}"
        )

        title = crawl_data.get("title", {}).get("text", "")
        meta_desc = crawl_data.get("meta_description", {}).get("text", "")
        sample_text = (crawl_data.get("visible_text", "") or "")[:1500]

        user_prompt = (
            f"Target URL: {url}\n"
            f"Current Title: {title}\n"
            f"Current Meta Description: {meta_desc}\n"
            f"Extracted Page Content Sample:\n{sample_text}\n\n"
            "Analyze and provide actionable, high-impact optimizations for AI search engines and traditional SERPs."
        )

        audit = await self._dispatch_llm_json(system_prompt, user_prompt, temperature=0.2)
        if audit and isinstance(audit, dict) and "recommended_title_tag" in audit:
            return audit

        # Rule-based fallback
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        return {
            "brand_summary": f"Official web platform for {domain}.",
            "ai_citation_readiness_verdict": "Medium: Add more structured numerical claims and direct Q&A answers for AI models.",
            "recommended_title_tag": f"{domain.capitalize()} — Fast, Reliable & Scalable Platform",
            "recommended_meta_description": f"Explore {domain} for modern developer workflows, zero-friction integration, and predictable performance.",
            "high_value_keyword_opportunities": [f"{domain} review", f"{domain} pricing", f"{domain} alternatives", f"{domain} vs competitors"],
            "ai_search_quotability_actions": [
                "Include a 2-3 sentence definition paragraph at the very top of the page for instant citation by ChatGPT and Perplexity.",
                "Add concrete benchmark figures, latency numbers, and percentage improvements."
            ],
            "schema_recommendations": ["Organization schema with founder & social links", "FAQPage with high-intent customer queries"]
        }
