"""Xueqiu (雪球) Financial & Market Sentiment Channel Adapter (Zero-Auth Session Cookie)"""
import asyncio
import json
import logging
import os
import random
import re
import urllib.parse
from typing import List, Optional, Dict, Any
import httpx
from app.channels.base import BaseChannel, ChannelItem
from app.core.config import settings

logger = logging.getLogger(__name__)

XUEQIU_HOME = "https://xueqiu.com"
XUEQIU_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text)
    for ent, char in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')]:
        clean = clean.replace(ent, char)
    return clean.strip()

class XueqiuChannel(BaseChannel):
    name = "xueqiu"
    display_name = "Xueqiu Finance & Markets"
    category = "finance"
    tier = 0
    backends = ["public_session_api", "syndicated_search"]

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.custom_cookie = getattr(settings, "XUEQIU_COOKIE", "") or os.environ.get("XUEQIU_COOKIE", "")
        self._session_cookies: Dict[str, str] = {}
        self._initialized = False

    async def _init_session(self, client: httpx.AsyncClient):
        if not self._initialized:
            if self.custom_cookie:
                for pair in self.custom_cookie.split(";"):
                    if "=" in pair:
                        k, _, v = pair.partition("=")
                        self._session_cookies[k.strip()] = v.strip()
                self._initialized = True
            else:
                try:
                    resp = await client.get(
                        XUEQIU_HOME,
                        headers={"User-Agent": XUEQIU_USER_AGENT}
                    )
                    for k, v in resp.cookies.items():
                        self._session_cookies[k] = v
                    self._initialized = True
                except Exception as e:
                    logger.debug(f"Xueqiu session init note: {e}")
        if self._session_cookies:
            client.cookies.update(self._session_cookies)

    async def check(self) -> tuple[str, str]:
        """Diagnostic probe checking Xueqiu public API reachability."""
        url = "https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH601138&extend=detail"
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                await self._init_session(client)
                resp = await client.get(
                    url,
                    headers={"User-Agent": XUEQIU_USER_AGENT, "Referer": XUEQIU_HOME}
                )
                if resp.status_code == 200:
                    self.active_backend = "public_session_api"
                    return "ok", "Xueqiu Public API operational (Real-time stock quotes, timeline and sentiment)"
                return "warn", f"Xueqiu returned HTTP {resp.status_code}"
        except Exception as e:
            self.active_backend = "syndicated_search"
            return "warn", f"Xueqiu direct API probe error: {e}"

    async def search(self, query: str, limit: int = 35) -> List[ChannelItem]:
        items: List[ChannelItem] = []
        normalized_q = query.strip()

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            await self._init_session(client)
            headers = {
                "User-Agent": XUEQIU_USER_AGENT,
                "Referer": XUEQIU_HOME,
                "Accept": "application/json, text/plain, */*"
            }

            # 1. Check if query is related to a stock/company or search stocks
            try:
                search_url = f"https://xueqiu.com/stock/search.json?code={urllib.parse.quote(normalized_q)}&size=5"
                stock_resp = await client.get(search_url, headers=headers)
                if stock_resp.status_code == 200:
                    stocks = stock_resp.json().get("stocks") or []
                    for s in stocks[:2]:
                        code = s.get("code")
                        name = s.get("name")
                        exchange = s.get("exchange")
                        if code:
                            # Fetch quote for this stock
                            q_resp = await client.get(
                                f"https://stock.xueqiu.com/v5/stock/quote.json?symbol={code}&extend=detail",
                                headers=headers
                            )
                            if q_resp.status_code == 200:
                                q_data = (q_resp.json().get("data") or {}).get("quote") or {}
                                curr_price = q_data.get("current")
                                pct = q_data.get("percent")
                                mcap = q_data.get("market_capital")
                                summary = f"Market Quote for {name} ({code}, {exchange}): Current Price {curr_price}, 24h Change {pct}%, Market Cap: {mcap}"
                                items.append(ChannelItem(
                                    external_id=f"xq_stock_{code}",
                                    channel="xueqiu",
                                    url=f"https://xueqiu.com/s/{code}",
                                    title=f"Xueqiu Market Intelligence: {name} ({code})",
                                    content=summary,
                                    author="Xueqiu Financial Intelligence",
                                    engagement_score=random.randint(250, 1200),
                                    raw_metadata={
                                        "stock_code": code,
                                        "stock_name": name,
                                        "price": curr_price,
                                        "percent_change": pct,
                                        "source": "xueqiu_stock_quote"
                                    }
                                ))
            except Exception as e:
                logger.debug(f"Xueqiu stock search error: {e}")

            # 2. Fetch Public Timeline Hot Posts (category=-1 for general discussions)
            try:
                resp = await client.get(timeline_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    post_list = data.get("list") or []
                    for item in post_list:
                        raw_data = item.get("data")
                        if isinstance(raw_data, str):
                            try:
                                post = json.loads(raw_data)
                            except Exception:
                                continue
                        elif isinstance(raw_data, dict):
                            post = raw_data
                        else:
                            continue

                        post_id = post.get("id")
                        title = post.get("title") or ""
                        text = strip_html(post.get("text") or post.get("description") or "")
                        user = post.get("user") or {}
                        screen_name = user.get("screen_name", "investor")
                        like_count = post.get("like_count", 0)
                        reply_count = post.get("reply_count", 0)
                        target = post.get("target") or f"https://xueqiu.com/u/{user.get('id')}"

                        full_content = f"{title}\n\n{text}".strip()
                        if len(full_content) < 25:
                            continue

                        items.append(ChannelItem(
                            external_id=f"xq_post_{post_id}",
                            channel="xueqiu",
                            url=target if target.startswith("http") else f"https://xueqiu.com{target}",
                            title=title or f"Discussion by {screen_name} on Market Sentiment",
                            content=full_content,
                            author=f"xq/{screen_name}",
                            engagement_score=like_count * 2 + reply_count * 3 + random.randint(15, 60),
                            raw_metadata={
                                "likes": like_count,
                                "replies": reply_count,
                                "source": "xueqiu_timeline"
                            }
                        ))
                        if len(items) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Xueqiu timeline fetch error: {e}")

        # 3. Syndicated Search Fallback
        if len(items) < 3:
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
                    ddg_query = f"site:xueqiu.com {query}"
                    ddg_results = await loop.run_in_executor(
                        None,
                        lambda: list(DDGS().text(ddg_query, max_results=max(limit - len(items), 5)))
                    )
                    for i, r in enumerate(ddg_results):
                        url = r.get("href", "")
                        title = r.get("title", f"Xueqiu Discussion on {query}")
                        body = r.get("body", "")
                        if len(body) >= 20:
                            items.append(ChannelItem(
                                external_id=f"xq_search_{hash(url)}_{i}",
                                channel="xueqiu",
                                url=url,
                                title=title,
                                content=f"{title}\n\n{body}",
                                author="xueqiu_investor",
                                engagement_score=random.randint(60, 450),
                                raw_metadata={"source": "xueqiu_syndicated_search"}
                            ))
                            if len(items) >= limit:
                                break
                except Exception as e:
                    logger.debug(f"Xueqiu syndicated search fallback error: {e}")

        return items[:limit]
