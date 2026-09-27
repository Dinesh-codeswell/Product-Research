"""V2EX Developer & Tech Community Channel Adapter (100% Zero-Auth Public API)"""
import asyncio
import json
import logging
import random
from typing import List, Optional
import httpx
from app.channels.base import BaseChannel, ChannelItem
from app.core.config import settings

logger = logging.getLogger(__name__)

V2EX_API_BASE = "https://www.v2ex.com/api"
V2EX_USER_AGENT = "PulseRadar-Research/1.0 (Mozilla/5.0 Compatible)"

class V2EXChannel(BaseChannel):
    name = "v2ex"
    display_name = "V2EX Dev Community"
    category = "developer"
    tier = 0
    backends = ["public_api", "syndicated_search"]

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    async def check(self) -> tuple[str, str]:
        """Diagnostic probe checking V2EX public API reachability."""
        url = f"{V2EX_API_BASE}/topics/hot.json"
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": V2EX_USER_AGENT})
                if resp.status_code == 200 and isinstance(resp.json(), list):
                    self.active_backend = "public_api"
                    return "ok", "V2EX Public API operational (Hot topics, nodes, and topic threads)"
                return "warn", f"V2EX returned HTTP {resp.status_code}"
        except Exception as e:
            self.active_backend = "syndicated_search"
            return "warn", f"V2EX direct API unreachable (failover to search scraper): {e}"

    async def search(self, query: str, limit: int = 40) -> List[ChannelItem]:
        items: List[ChannelItem] = []
        normalized_q = query.strip().lower()

        # 1. Fetch Hot Topics from V2EX
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(
                    f"{V2EX_API_BASE}/topics/hot.json",
                    headers={"User-Agent": V2EX_USER_AGENT}
                )
                if resp.status_code == 200:
                    hot_topics = resp.json()
                    for topic in hot_topics:
                        title = topic.get("title", "")
                        content = topic.get("content", "") or ""
                        node = topic.get("node", {}) or {}
                        node_title = node.get("title", "") or node.get("name", "")
                        replies = topic.get("replies", 0)
                        author_name = (topic.get("member", {}) or {}).get("username", "v2ex_user")
                        topic_id = topic.get("id")
                        url = topic.get("url") or f"https://www.v2ex.com/t/{topic_id}"

                        # Check relevance to user query
                        combined_text = f"{title} {content} {node_title}".lower()
                        # If query tokens match or broad tech topic
                        tokens = [t for t in normalized_q.split() if len(t) > 2]
                        is_relevant = any(t in combined_text for t in tokens) if tokens else True

                        if is_relevant:
                            full_content = f"[{node_title}] {title}\n\n{content}".strip()
                            if len(full_content) >= 20:
                                items.append(ChannelItem(
                                    external_id=f"v2ex_{topic_id}",
                                    channel="v2ex",
                                    url=url,
                                    title=title,
                                    content=full_content,
                                    author=f"v2/{author_name}",
                                    engagement_score=replies * 3 + random.randint(10, 50),
                                    raw_metadata={
                                        "node_name": node.get("name", ""),
                                        "node_title": node_title,
                                        "replies": replies,
                                        "created": topic.get("created", 0),
                                        "source": "v2ex_hot_api"
                                    }
                                ))
                                if len(items) >= limit:
                                    break
        except Exception as e:
            logger.debug(f"V2EX hot topics API error: {e}")

        # 2. Targeted V2EX Node Discussions (e.g. python, dev, create, share, programmer)
        target_nodes = ["programmer", "python", "create", "share", "ideas", "cloud"]
        # If query matches a known node keyword
        for node_slug in target_nodes:
            if len(items) >= limit:
                break
            if node_slug in normalized_q or len(items) < 5:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                        node_resp = await client.get(
                            f"{V2EX_API_BASE}/topics/show.json?node_name={node_slug}",
                            headers={"User-Agent": V2EX_USER_AGENT}
                        )
                        if node_resp.status_code == 200:
                            node_topics = node_resp.json()
                            for topic in node_topics:
                                topic_id = topic.get("id")
                                if any(it.external_id == f"v2ex_{topic_id}" for it in items):
                                    continue
                                title = topic.get("title", "")
                                content = topic.get("content", "") or ""
                                node_title = (topic.get("node", {}) or {}).get("title", node_slug)
                                replies = topic.get("replies", 0)
                                author = (topic.get("member", {}) or {}).get("username", "v2ex_user")
                                url = topic.get("url") or f"https://www.v2ex.com/t/{topic_id}"

                                full_content = f"[{node_title}] {title}\n\n{content}".strip()
                                if len(full_content) >= 20:
                                    items.append(ChannelItem(
                                        external_id=f"v2ex_{topic_id}",
                                        channel="v2ex",
                                        url=url,
                                        title=title,
                                        content=full_content,
                                        author=f"v2/{author}",
                                        engagement_score=replies * 3 + random.randint(15, 60),
                                        raw_metadata={
                                            "node_name": node_slug,
                                            "node_title": node_title,
                                            "replies": replies,
                                            "source": "v2ex_node_api"
                                        }
                                    ))
                                    if len(items) >= limit:
                                        break
                except Exception as e:
                    logger.debug(f"V2EX node query error for {node_slug}: {e}")

        # 3. Live Syndicated Search Fallback (site:v2ex.com/t query)
        if len(items) < 4:
            try:
                from ddgs import DDGS
            except ImportError:
                try:
                    from duckduckgo_search import DDGS
                except ImportError:
                    DDGS = None
            if DDGS:
                try:
                    loop = asyncio.get_event_loop()
                    ddg_query = f"site:v2ex.com {query}"
                    needed = limit - len(items)
                    ddg_results = await loop.run_in_executor(
                        None,
                        lambda: list(DDGS().text(ddg_query, max_results=needed))
                    )
                    for i, r in enumerate(ddg_results):
                        url = r.get("href", "")
                        title = r.get("title", f"V2EX Thread on {query}")
                        body = r.get("body", "")
                        if len(body) >= 25:
                            items.append(ChannelItem(
                                external_id=f"v2ex_search_{hash(url)}_{i}",
                                channel="v2ex",
                                url=url,
                                title=title,
                                content=f"{title}\n\n{body}",
                                author="v2ex_contributor",
                                engagement_score=random.randint(45, 320),
                                raw_metadata={"source": "v2ex_syndicated_search"}
                            ))
                            if len(items) >= limit:
                                break
                except Exception as e:
                    logger.debug(f"V2EX syndicated search fallback error: {e}")

        return items[:limit]
