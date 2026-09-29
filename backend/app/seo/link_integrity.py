"""Link Integrity Auditor — Broken Internal & External Link Detection
(notfair `broken-link-checker` pattern)

Checks sampled internal/external links from the crawl result with bounded
concurrency, HEAD-first with GET fallback (many hosts 405 HEAD requests).
Produces a link-graph health score and site-health issues feed.
"""
import asyncio
import logging
from typing import Dict, Any, List, Set
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PulseRadarSEO/1.0 (link integrity audit)"


class LinkIntegrityAuditor:
    def __init__(self, timeout: float = 8.0, max_concurrency: int = 12):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)

    # ------------------------------------------------------------------
    async def _probe(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """HEAD-first probe with GET fallback. Returns a link record."""
        async with self.semaphore:
            for attempt, method in enumerate(("HEAD", "GET")):
                try:
                    resp = await client.request(method, url)
                    if resp.status_code == 405 and method == "HEAD":
                        continue  # fall through to GET
                    return {
                        "url": url,
                        "status_code": resp.status_code,
                        "ok": resp.status_code < 400,
                        "redirected": bool(resp.history),
                        "final_url": str(resp.url) if resp.history else url,
                    }
                except Exception as e:
                    if attempt == 1:  # after GET fallback also failed
                        return {
                            "url": url,
                            "status_code": 0,
                            "ok": False,
                            "redirected": False,
                            "final_url": url,
                            "error": type(e).__name__,
                        }
                    continue
        return {"url": url, "status_code": 0, "ok": False, "redirected": False, "final_url": url, "error": "unreachable"}

    # ------------------------------------------------------------------
    async def audit(
        self,
        crawl_data: Dict[str, Any],
        max_internal: int = 12,
        max_external: int = 6,
    ) -> Dict[str, Any]:
        """Probes sampled links from the crawl result."""
        links = crawl_data.get("links", {}) or {}
        internal: List[str] = (links.get("internal_sample") or [])[:max_internal]
        external: List[str] = (links.get("external_sample") or [])[:max_external]

        # Dedupe, keep http(s) only
        def clean(urls: List[str]) -> List[str]:
            seen: Set[str] = set()
            out = []
            for u in urls:
                if u.startswith(("http://", "https://")) and u not in seen:
                    seen.add(u)
                    out.append(u)
            return out

        internal, external = clean(internal), clean(external)
        targets = [(u, "internal") for u in internal] + [(u, "external") for u in external]

        results: List[Dict[str, Any]] = []
        if targets:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                probe_tasks = [self._probe(client, u) for u, _ in targets]
                probe_results = await asyncio.gather(*probe_tasks)
                for (url, kind), probe in zip(targets, probe_results):
                    probe["type"] = kind
                    results.append(probe)

        broken = [r for r in results if not r.get("ok")]
        redirects = [r for r in results if r.get("redirected")]
        checked = len(results)
        broken_rate = (len(broken) / checked) if checked else 0.0

        # Score: start 100, -15 per broken, -3 per redirect chain
        score = max(0, min(100, 100 - len(broken) * 15 - len(redirects) * 3))

        issues: List[Dict[str, str]] = []
        for b in broken:
            issues.append({
                "severity": "HIGH" if b.get("type") == "internal" else "MEDIUM",
                "field": "Broken Link",
                "message": f"{b.get('type', 'link').title()} link returns HTTP {b.get('status_code') or 'error'}: {b['url'][:120]}",
            })
        for r in redirects[:5]:
            issues.append({
                "severity": "LOW",
                "field": "Redirect Chain",
                "message": f"Link redirects to {r.get('final_url', '')[:120]} — update the source href",
            })

        return {
            "success": True,
            "checked": checked,
            "internal_checked": len(internal),
            "external_checked": len(external),
            "broken_count": len(broken),
            "redirect_count": len(redirects),
            "broken_rate": round(broken_rate, 3),
            "link_health_score": score,
            "broken_links": [
                {"url": b["url"], "status_code": b.get("status_code"), "type": b.get("type")}
                for b in broken[:15]
            ],
            "redirect_links": [
                {"url": r["url"], "final_url": r.get("final_url"), "type": r.get("type")}
                for r in redirects[:10]
            ],
            "issues": issues,
            "note": f"Sampled {checked} links (bounded probe: HEAD-first with GET fallback).",
        }
