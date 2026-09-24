"""Research Controller & Multi-Channel Streaming Endpoints"""
import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.models.entities import ResearchSession, RawFeedback, InsightCluster, EvidenceQuote, GeneratedSpec
from app.models.schemas import (
    StartResearchRequest,
    ResearchSessionResponse,
    GenerateSpecRequest,
    GeneratedSpecResponse
)
from app.channels.reddit import RedditChannel
from app.channels.youtube import YouTubeChannel
from app.channels.hackernews import HackerNewsChannel
from app.channels.github import GitHubChannel
from app.channels.twitter import TwitterChannel
from app.channels.facebook import FacebookChannel

from app.engine.cleaner import TextCleaner
from app.engine.embedder import EmbeddingEngine
from app.engine.clusterer import SemanticClusterer
from app.engine.synthesizer import SynthesisEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["Research"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])

# In-memory SSE queues and event history buffer per session
session_event_queues: Dict[str, List[asyncio.Queue]] = {}
session_event_history: Dict[str, List[str]] = {}

def publish_event(session_id: str, stage: str, percent: int, message: str, data: dict = None):
    payload = json.dumps({"stage": stage, "percent": percent, "message": message, "data": data or {}})
    if session_id not in session_event_history:
        session_event_history[session_id] = []
    session_event_history[session_id].append(payload)
    if len(session_event_history[session_id]) > 250:
        session_event_history[session_id].pop(0)

    queues = session_event_queues.get(session_id, [])
    for q in queues:
        try:
            q.put_nowait(payload)
        except Exception:
            pass

async def scrape_channel(channel_name: str, query: str, limit: int, subreddits: List[str] = None):
    try:
        if channel_name == "reddit":
            ch = RedditChannel()
            return await ch.search(query=query, limit=limit, subreddits=subreddits)
        elif channel_name == "youtube":
            ch = YouTubeChannel()
            return await ch.search(query=query, limit=limit)
        elif channel_name == "hackernews":
            ch = HackerNewsChannel()
            return await ch.search(query=query, limit=limit)
        elif channel_name == "github":
            ch = GitHubChannel()
            return await ch.search(query=query, limit=limit)
        elif channel_name == "twitter":
            ch = TwitterChannel()
            return await ch.search(query=query, limit=limit)
        elif channel_name == "facebook":
            ch = FacebookChannel()
            return await ch.search(query=query, limit=limit)
        elif channel_name in ["google", "web", "duckduckgo"]:
            from app.channels.google import GoogleChannel
            ch = GoogleChannel()
            return await ch.search(query=query, limit=limit)
    except Exception as e:
        logger.error(f"Error scraping channel {channel_name}: {e}")
    return []

async def run_research_pipeline(
    session_id: str,
    query: str,
    channels: List[str],
    subreddits: List[str],
    max_items: int,
    execution_mode: str = "focus",
    browser_approved: bool = False
):
    """Background task orchestrating parallel scraping (or live browser agent), cleaning, clustering, and synthesis."""
    logger.info(f"Starting research pipeline for session {session_id} (Query: '{query}', Mode: {execution_mode}, Channels: {channels}, MaxItems: {max_items})")
    
    cleaner = TextCleaner()
    embedder = EmbeddingEngine()
    clusterer = SemanticClusterer()
    synthesizer = SynthesisEngine()
    
    async with AsyncSessionLocal() as db:
        stmt = select(ResearchSession).where(ResearchSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            return
        
        session.status = "RUNNING"
        await db.commit()

        try:
            if execution_mode == "browser" and browser_approved:
                publish_event(session_id, "browser_agent_start", 10, f"Spawning Live Browser Agent across {len(channels)} channels...", {
                    "mode": "browser",
                    "channels": channels,
                    "action": "SPAWN_AGENT",
                    "channel": "system",
                    "title": "Autonomous Browser Agent Starting"
                })
                from app.browser_agent.agent import LiveBrowserAgent
                browser_agent = LiveBrowserAgent()
                all_raw_items = await browser_agent.run_live_browser_sweep(
                    session_id=session_id,
                    query=query,
                    channels=channels,
                    max_items=max_items,
                    event_publisher=publish_event
                )

                # Resilient Fallback: If browser engine yielded 0 items, run parallel multi-channel scrapers
                if not all_raw_items:
                    logger.warning(f"Browser agent yielded 0 items. Triggering resilient multi-channel scraper fallback for session {session_id}.")
                    publish_event(session_id, "browser_fallback", 25, f"Engaging parallel multi-channel direct syndication across {len(channels)} channels...", {
                        "action": "FALLBACK_SCRAPE",
                        "channel": "system",
                        "title": "Parallel Resilient Ingestion",
                        "description": "Engaging direct syndication scrapers across all channels"
                    })
                    per_channel_limit = max(15, max_items // max(1, len(channels)))
                    tasks = [scrape_channel(ch, query, per_channel_limit, subreddits) for ch in channels]
                    results = await asyncio.gather(*tasks)
                    for ch_items in results:
                        all_raw_items.extend(ch_items)
            else:
                publish_event(session_id, "start", 10, f"Dispatching parallel workers across {len(channels)} channels...")

                # 1. Parallel Multi-Channel Ingestion (Focus Mode)
                per_channel_limit = max(15, max_items // len(channels))
                tasks = [scrape_channel(ch, query, per_channel_limit, subreddits) for ch in channels]
                results = await asyncio.gather(*tasks)

                all_raw_items = []
                for ch_items in results:
                    all_raw_items.extend(ch_items)

            publish_event(session_id, "scraped", 55, f"Harvested {len(all_raw_items)} signals across {len(channels)} channels.")

            # 2. Cleaning & Deduplication
            publish_event(session_id, "cleaning", 70, f"Deduplicating and stripping noise across {len(all_raw_items)} items...")
            cleaned_items = cleaner.deduplicate_and_clean(all_raw_items)

            # Persist raw feedbacks
            for it in cleaned_items:
                fb = RawFeedback(
                    session_id=session_id,
                    channel=it.channel,
                    external_id=it.external_id,
                    url=it.url,
                    title=it.title,
                    content=it.content,
                    author=it.author,
                    engagement_score=it.engagement_score,
                    raw_metadata=it.raw_metadata
                )
                db.add(fb)
            session.total_items_scraped = len(cleaned_items)
            await db.commit()

            # 3. Embeddings & Semantic Clustering
            publish_event(session_id, "clustering", 85, f"Generating vector embeddings and semantic clusters across {len(cleaned_items)} items...")
            texts = [it.content for it in cleaned_items]
            embeddings = embedder.generate_embeddings(texts)
            clusters_data = clusterer.cluster_items(cleaned_items, embeddings)

            # Persist clusters & quotes
            for c_data in clusters_data:
                cluster_obj = InsightCluster(
                    session_id=session_id,
                    title=c_data["title"],
                    category=c_data["category"],
                    description=c_data["description"],
                    severity_score=c_data["severity_score"],
                    item_count=c_data["item_count"],
                    keyword_tags=c_data["keyword_tags"]
                )
                db.add(cluster_obj)
                await db.flush()

                for q in c_data["quotes"]:
                    quote_obj = EvidenceQuote(
                        cluster_id=cluster_obj.id,
                        quote_text=q["quote_text"],
                        permalink=q["permalink"],
                        source_author=q["source_author"],
                        source_channel=q["source_channel"],
                        engagement_score=q["engagement_score"]
                    )
                    db.add(quote_obj)

            # 4. Executive Synthesis
            publish_event(session_id, "synthesizing", 92, "Synthesizing strategic executive summary and user mental models...")
            summary = await synthesizer.generate_executive_summary(query, clusters_data, len(cleaned_items))
            session.executive_summary = summary
            session.status = "COMPLETED"
            await db.commit()

            publish_event(session_id, "completed", 100, f"Discovery complete! Discovered {len(clusters_data)} clusters from {len(cleaned_items)} signals.", {
                "session_id": session_id,
                "clusters_count": len(clusters_data),
                "total_items": len(cleaned_items)
            })

        except Exception as e:
            logger.error(f"Error executing research pipeline: {e}", exc_info=True)
            session.status = "FAILED"
            session.executive_summary = f"Pipeline error: {type(e).__name__}: {str(e)}"
            await db.commit()
            publish_event(session_id, "failed", 100, f"Research pipeline error: {str(e)}")

@router.post("/start", response_model=Dict[str, str])
async def start_research(payload: StartResearchRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Launches a new multi-channel research session in the background."""
    mode = payload.execution_mode if payload.execution_mode in ["focus", "browser"] else "focus"
    is_approved = bool(payload.browser_approved) if mode == "browser" else False

    new_session = ResearchSession(
        query=payload.query,
        channels_used=payload.channels,
        status="QUEUED",
        execution_mode=mode
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    session_event_queues[new_session.id] = []

    background_tasks.add_task(
        run_research_pipeline,
        session_id=new_session.id,
        query=payload.query,
        channels=payload.channels,
        subreddits=payload.subreddits or [],
        max_items=payload.max_items,
        execution_mode=mode,
        browser_approved=is_approved
    )

    return {"session_id": new_session.id, "status": "QUEUED"}

@router.get("/{session_id}", response_model=ResearchSessionResponse)
async def get_research_session(session_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ResearchSession)
        .options(
            selectinload(ResearchSession.clusters).selectinload(InsightCluster.quotes),
            selectinload(ResearchSession.feedbacks)
        )
        .where(ResearchSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session

@router.get("/{session_id}/events")
async def stream_events(session_id: str):
    if session_id not in session_event_queues:
        session_event_queues[session_id] = []

    queue = asyncio.Queue()

    # Replay past events first so late-connecting clients receive full history
    past_events = session_event_history.get(session_id, [])
    for past_msg in past_events:
        queue.put_nowait(past_msg)

    session_event_queues[session_id].append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {msg}\n\n"
                    data = json.loads(msg)
                    if data.get("stage") in ["completed", "failed"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping prevents proxy timeout
                    yield ": ping\n\n"
        finally:
            if session_id in session_event_queues and queue in session_event_queues[session_id]:
                session_event_queues[session_id].remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/{session_id}/generate-prd", response_model=GeneratedSpecResponse)
async def generate_prd_endpoint(session_id: str, payload: GenerateSpecRequest, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.clusters).selectinload(InsightCluster.quotes))
        .where(ResearchSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    clusters_dicts = []
    for c in session.clusters:
        clusters_dicts.append({
            "title": c.title,
            "category": c.category,
            "description": c.description,
            "quotes": [{"quote_text": q.quote_text, "permalink": q.permalink, "source_author": q.source_author} for q in c.quotes]
        })

    synthesizer = SynthesisEngine()
    prd_markdown = await synthesizer.generate_prd(session.query, clusters_dicts, payload.custom_instructions)

    spec = GeneratedSpec(
        session_id=session_id,
        spec_type=payload.spec_type,
        markdown_content=prd_markdown
    )
    db.add(spec)
    await db.commit()
    await db.refresh(spec)

    return spec

@router.get("/{session_id}/export/{format}")
async def export_report(session_id: str, format: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ResearchSession)
        .options(
            selectinload(ResearchSession.clusters).selectinload(InsightCluster.quotes),
            selectinload(ResearchSession.feedbacks),
            selectinload(ResearchSession.specs)
        )
        .where(ResearchSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if format == "json":
        data = {
            "id": session.id,
            "query": session.query,
            "total_items": session.total_items_scraped,
            "channels": session.channels_used,
            "summary": session.executive_summary,
            "clusters": [
                {
                    "title": c.title,
                    "category": c.category,
                    "severity": c.severity_score,
                    "item_count": c.item_count,
                    "quotes": [q.quote_text for q in c.quotes]
                }
                for c in session.clusters
            ],
            "feedbacks": [
                {
                    "id": fb.id,
                    "channel": fb.channel,
                    "url": fb.url,
                    "title": fb.title,
                    "author": fb.author,
                    "content": fb.content,
                    "full_markdown": (fb.raw_metadata or {}).get("full_markdown"),
                    "firecrawl_extracted": bool((fb.raw_metadata or {}).get("firecrawl")),
                    "engagement": fb.engagement_score
                }
                for fb in (session.feedbacks or [])
            ]
        }
        return Response(content=json.dumps(data, indent=2), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=pulseradar_{session_id}.json"})

    if format in ["ai-bundle", "llm-bundle"]:
        # Comprehensive AI Agent Context Bundle
        bundle_lines = [
            f"# AI RESEARCH CONTEXT DOSSIER: {session.query}",
            "",
            "> **AI SYSTEM DIRECTIVE**: This file contains customer discovery intelligence, synthesized pain points,",
            "> ground-truth evidence quotes, and full article transcripts scraped via PulseRadar and Firecrawl.",
            "> Ingest this context directly into your reasoning model to draft PRDs, design features, or write code.",
            "",
            f"- **Research Query:** `{session.query}`",
            f"- **Harvested Signals:** {session.total_items_scraped} verified items across {', '.join(session.channels_used)}",
            f"- **Execution Timestamp:** {session.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## 1. Executive Summary & Problem Framing",
            session.executive_summary or "No executive summary available.",
            "",
            "---",
            "",
            "## 2. Synthesized Thematic Clusters & Customer Friction",
            ""
        ]
        for c in session.clusters:
            bundle_lines.append(f"### [{c.category}] {c.title}")
            bundle_lines.append(f"**Severity Score:** {c.severity_score} / 1.0 • **Signal Count:** {c.item_count}")
            bundle_lines.append(f"**Analysis:** {c.description}")
            bundle_lines.append("")
            bundle_lines.append("**Verbatim Evidence Quotes:**")
            for q in c.quotes:
                bundle_lines.append(f"- \"{q.quote_text}\" — [{q.source_author or 'Contributor'}]({q.permalink}) ({q.source_channel.title()})")
            bundle_lines.append("")

        bundle_lines.append("---")
        bundle_lines.append("")
        bundle_lines.append("## 3. Deep Source Transcripts & Scraped Articles (Firecrawl / Web)")
        bundle_lines.append("")

        for i, fb in enumerate(session.feedbacks or []):
            full_md = (fb.raw_metadata or {}).get("full_markdown") or fb.content
            is_fc = (fb.raw_metadata or {}).get("firecrawl", False)
            badge = " [Firecrawl Deep Scraped]" if is_fc else ""
            bundle_lines.append(f"### Document {i+1}: {fb.title or 'Untitled Discussion'}{badge}")
            bundle_lines.append(f"- **Channel:** `{fb.channel}`")
            bundle_lines.append(f"- **Author:** {fb.author or 'anonymous'}")
            bundle_lines.append(f"- **URL:** {fb.url}")
            bundle_lines.append(f"- **Engagement Score:** {fb.engagement_score}")
            bundle_lines.append("")
            bundle_lines.append("```markdown")
            bundle_lines.append(full_md)
            bundle_lines.append("```")
            bundle_lines.append("")

        return Response(
            content="\n".join(bundle_lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=pulseradar_ai_agent_bundle_{session_id}.md"}
        )

    lines = [
        f"# PulseRadar Research Dossier: {session.query}",
        f"*Generated on {session.created_at.strftime('%Y-%m-%d %H:%M UTC')}*",
        f"*Total Analyzed Signals: {session.total_items_scraped} across {', '.join(session.channels_used)}*",
        "",
        "## Executive Summary",
        session.executive_summary or "No summary available.",
        "",
        "## Key Thematic Clusters",
        ""
    ]
    for c in session.clusters:
        lines.append(f"### [{c.category}] {c.title}")
        lines.append(c.description)
        lines.append("")
        lines.append("**Evidence Quotes:**")
        for q in c.quotes:
            lines.append(f"- \"{q.quote_text}\" — [{q.source_author or 'User'}]({q.permalink}) ({q.source_channel.title()})")
        lines.append("")

    return Response(content="\n".join(lines), media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=pulseradar_{session_id}.md"})

@router.get("/", response_model=List[ResearchSessionResponse])
async def list_sessions(limit: int = 15, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.clusters).selectinload(InsightCluster.quotes))
        .order_by(ResearchSession.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

# --- Channels Configuration Endpoints ---
@settings_router.get("/channels")
async def get_channels_status():
    """Returns the configuration and auth status of all supported platforms."""
    return {
        "google": {
            "name": "Google Search & Web Engine",
            "tier": "zero-auth",
            "status": "ready",
            "description": "High-authority tech articles, blogs, benchmarks, and community guides"
        },
        "firecrawl": {
            "name": "Firecrawl Deep Scraper",
            "tier": "authenticated" if settings.FIRECRAWL_API_KEY else "optional",
            "status": "configured" if settings.FIRECRAWL_API_KEY else "ready",
            "configured": bool(settings.FIRECRAWL_API_KEY),
            "description": "Converts discovered web articles into clean, LLM-ready Markdown"
        },
        "reddit": {
            "name": "Reddit",
            "tier": "zero-auth",
            "status": "ready",
            "description": "Multi-subreddit sweep and community rants"
        },
        "youtube": {
            "name": "YouTube",
            "tier": "zero-auth",
            "status": "ready",
            "description": "Timestamped video reviews & transcript chunks"
        },
        "hackernews": {
            "name": "Hacker News",
            "tier": "zero-auth",
            "status": "ready",
            "description": "High-signal developer stories and comment rants via Algolia"
        },
        "github": {
            "name": "GitHub Issues",
            "tier": "zero-auth" if not settings.GITHUB_TOKEN else "authenticated",
            "status": "ready",
            "configured": bool(settings.GITHUB_TOKEN),
            "description": "Real open-source bug reports, discussions, and feature requests"
        },
        "twitter": {
            "name": "Twitter / X",
            "tier": "authenticated" if (settings.TWITTER_AUTH_TOKEN or settings.TWITTER_BEARER_TOKEN) else "fallback",
            "status": "ready",
            "configured": bool((settings.TWITTER_AUTH_TOKEN and settings.TWITTER_CT0) or settings.TWITTER_BEARER_TOKEN),
            "description": "Live tech tweets, hot takes, and developer discussions"
        },
        "facebook": {
            "name": "Facebook",
            "tier": "authenticated" if (settings.FACEBOOK_C_USER and settings.FACEBOOK_XS) else "fallback",
            "status": "ready",
            "configured": bool(settings.FACEBOOK_C_USER and settings.FACEBOOK_XS),
            "description": "Tech founder groups and SaaS community reviews"
        }
    }

@settings_router.post("/channels")
async def update_channel_credentials(creds: Dict[str, str]):
    """Update credentials in-memory for active session (and write to .env if desired)."""
    if "twitter_auth_token" in creds:
        settings.TWITTER_AUTH_TOKEN = creds["twitter_auth_token"]
    if "twitter_ct0" in creds:
        settings.TWITTER_CT0 = creds["twitter_ct0"]
    if "twitter_bearer_token" in creds:
        settings.TWITTER_BEARER_TOKEN = creds["twitter_bearer_token"]
    if "github_token" in creds:
        settings.GITHUB_TOKEN = creds["github_token"]
    if "facebook_c_user" in creds:
        settings.FACEBOOK_C_USER = creds["facebook_c_user"]
    if "facebook_xs" in creds:
        settings.FACEBOOK_XS = creds["facebook_xs"]
    if "firecrawl_api_key" in creds:
        settings.FIRECRAWL_API_KEY = creds["firecrawl_api_key"].strip()

    return {"status": "success", "message": "Channel credentials updated successfully."}
