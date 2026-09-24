"""Firecrawl API Client for Deep Markdown & Structured JSON Scraping"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class FirecrawlClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.FIRECRAWL_API_KEY or "").strip()
        self.base_url = settings.FIRECRAWL_BASE_URL.rstrip("/")
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrapes a single URL and converts it into clean, LLM-ready Markdown."""
        if not self.is_configured:
            return None

        endpoint = f"{self.base_url}/v1/scrape"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    data = res_json.get("data", {})
                    markdown = data.get("markdown", "")
                    metadata = data.get("metadata", {})
                    return {
                        "success": True,
                        "markdown": markdown,
                        "title": metadata.get("title", ""),
                        "description": metadata.get("description", ""),
                        "source_url": metadata.get("sourceURL", url),
                        "status_code": metadata.get("statusCode", 200)
                    }
                else:
                    logger.warning(f"Firecrawl scrape failed for {url}: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Firecrawl scrape exception for {url}: {e}")

        return None

    async def scrape_batch(self, urls: List[str], max_concurrency: int = 3) -> Dict[str, Dict[str, Any]]:
        """Scrapes multiple URLs with concurrency throttling to respect rate limits."""
        if not self.is_configured or not urls:
            return {}

        results: Dict[str, Dict[str, Any]] = {}
        semaphore = asyncio.Semaphore(max_concurrency)

        async def worker(u: str):
            async with semaphore:
                res = await self.scrape_url(u)
                if res and res.get("success"):
                    results[u] = res

        tasks = [worker(u) for u in urls[:10]]
        await asyncio.gather(*tasks, return_exceptions=True)
        return results
