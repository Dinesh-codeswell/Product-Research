"""Research Controller & Multi-Channel Streaming Endpoints"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.models.entities import ResearchSession, RawFeedback, InsightCluster, EvidenceQuote, GeneratedSpec
from app.models.workflow_entities import WatchlistTopic, WatchlistSnapshot, AutomationRule, AutomationLog
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
from app.engine.signals import MomentumScorer, CrossSourceMerger, merge_cluster_duplicates
from app.engine.discovery import DiscoveryEngine
from app.engine.watchlist import build_snapshot, diff_snapshots
from app.engine.automations import dispatch_event
from app.engine.brief_renderer import render_brief_html
from app.engine.diagram_agent import DiagramAgent
from pydantic import BaseModel

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
        from app.channels import get_channel
        ch = get_channel(channel_name)
        if ch:
            if ch.name == "reddit" and subreddits:
                return await ch.search(query=query, limit=limit, subreddits=subreddits)
            return await ch.search(query=query, limit=limit)
        else:
            logger.warning(f"Unrecognized channel: {channel_name}")
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

        # Phase 0: AI Query Analysis & Tactical Keyword Planner
        from app.engine.ai_planner import AIResearchPlanner
        from app.core.ai_config import AIConfigManager
        ai_planner = AIResearchPlanner()
        active_ai_cfg = AIConfigManager.get_instance().get_config()

        publish_event(session_id, "ai_planning", 5, f"AI Model ({active_ai_cfg.active_model_name}) analyzing intent and planning tactical keywords across {len(channels)} channels...", {
            "model": active_ai_cfg.active_model_name,
            "provider": active_ai_cfg.active_provider,
            "action": "AI_QUERY_PLANNING"
        })

        search_plan = await ai_planner.plan_research_query(query, channels)
        channel_queries = search_plan.get("channel_queries", {})
        planned_subreddits = search_plan.get("recommended_subreddits", [])
        combined_subreddits = list(set((subreddits or []) + planned_subreddits))

        try:
            if execution_mode == "browser" and browser_approved:
                publish_event(session_id, "browser_agent_start", 12, f"Spawning Live Browser Agent across {len(channels)} channels with AI keyword control...", {
                    "mode": "browser",
                    "channels": channels,
                    "action": "SPAWN_AGENT",
                    "channel": "system",
                    "title": "Autonomous Browser Agent Starting",
                    "model": active_ai_cfg.active_model_name
                })
                from app.browser_agent.agent import LiveBrowserAgent
                browser_agent = LiveBrowserAgent()
                all_raw_items = await browser_agent.run_live_browser_sweep(
                    session_id=session_id,
                    query=query,
                    channels=channels,
                    max_items=max_items,
                    event_publisher=publish_event,
                    planned_queries=channel_queries,
                    subreddits=combined_subreddits
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
                    tasks = [scrape_channel(ch, (channel_queries.get(ch) or [query])[0], per_channel_limit, combined_subreddits) for ch in channels]
                    results = await asyncio.gather(*tasks)
                    for ch_items in results:
                        all_raw_items.extend(ch_items)
            else:
                publish_event(session_id, "start", 12, f"Dispatching parallel workers with AI-optimized keywords across {len(channels)} channels...")

                # 1. Parallel Multi-Channel Ingestion (Focus Mode)
                per_channel_limit = max(15, max_items // len(channels))
                tasks = [scrape_channel(ch, (channel_queries.get(ch) or [query])[0], per_channel_limit, combined_subreddits) for ch in channels]
                results = await asyncio.gather(*tasks)

                all_raw_items = []
                for ch_items in results:
                    all_raw_items.extend(ch_items)

            publish_event(session_id, "scraped", 55, f"Harvested {len(all_raw_items)} signals across {len(channels)} channels.")

            # 2. Cleaning & Laya System 1 Triage
            publish_event(session_id, "cleaning", 62, f"Executing Laya System 1 semantic triage & noise reduction across {len(all_raw_items)} signals...")
            cleaned_items = cleaner.deduplicate_and_clean(all_raw_items, query=query)

            # 2b. Momentum scoring & cross-source story merging (last30days pattern:
            # rank by what real people engage with; same story on multiple platforms
            # merges into one corroborated signal)
            scorer = MomentumScorer()
            cleaned_items = scorer.score_items(cleaned_items)
            merger = CrossSourceMerger()
            cleaned_items, merge_records = merger.merge(cleaned_items)
            cross_confirmed = sum(
                1 for it in cleaned_items if (it.raw_metadata or {}).get("cross_source_confirmed")
            )
            cleaned_items.sort(key=MomentumScorer.rank_key)
            if merge_records:
                logger.info(f"Cross-source merge: {len(merge_records)} signals folded into corroborated stories ({cross_confirmed} confirmed stories)")

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
                    sentiment_score=getattr(it, "sentiment_score", 0.0),
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

            # 3b. Merge lookalike clusters (same theme, different wording) so one
            # story = one cluster with multi-platform evidence
            clusters_data = merge_cluster_duplicates(clusters_data)

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

            # P3: Fire any matching automation rules (webhooks) — never blocks the pipeline
            try:
                async with AsyncSessionLocal() as auto_db:
                    await dispatch_event(auto_db, "research.completed", {
                        "session_id": session_id,
                        "query": query,
                        "clusters_count": len(clusters_data),
                        "total_items": len(cleaned_items),
                        "channels": channels,
                        "clusters": [
                            {
                                "title": c.get("title"),
                                "category": c.get("category"),
                                "severity_score": c.get("severity_score"),
                                "item_count": c.get("item_count"),
                            }
                            for c in clusters_data[:10]
                        ],
                    })
            except Exception as auto_err:
                logger.warning(f"Automation dispatch skipped for {session_id}: {auto_err}")

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

    if format == "html":
        # P2: Single-file HTML brief (self-contained, prints to PDF)
        brief_payload = {
            "query": session.query,
            "channels": session.channels_used or [],
            "total_items": session.total_items_scraped,
            "summary": session.executive_summary,
            "clusters": [
                {
                    "title": c.title,
                    "category": c.category,
                    "description": c.description,
                    "severity_score": c.severity_score,
                    "item_count": c.item_count,
                    "quotes": [
                        {
                            "quote_text": q.quote_text,
                            "permalink": q.permalink,
                            "source_author": q.source_author,
                            "source_channel": q.source_channel,
                            "engagement_score": q.engagement_score,
                        }
                        for q in c.quotes
                    ],
                }
                for c in session.clusters
            ],
            "feedbacks": [
                {
                    "channel": fb.channel,
                    "url": fb.url,
                    "title": fb.title,
                    "engagement": fb.engagement_score,
                }
                for fb in (session.feedbacks or [])
            ],
        }
        # P3: embed an auto-generated diagram when a PRD exists
        try:
            if session.specs:
                source_md = max(session.specs, key=lambda s: s.created_at).markdown_content
                diagram = DiagramAgent().generate(source_md, title=f"{session.query[:48]}")
                brief_payload["diagram_svg"] = diagram.get("svg")
        except Exception as diag_err:
            logger.debug(f"Diagram generation skipped: {diag_err}")
        html_content = render_brief_html("research", brief_payload)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=pulseradar_brief_{session_id}.html"},
        )

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

# --- Channels Configuration & Diagnostic Doctor Endpoints ---
@settings_router.get("/doctor")
@router.get("/doctor")
async def get_doctor_report():
    """Run non-destructive diagnostic health checks across all 13 platforms."""
    from app.channels import run_channel_doctor
    return await run_channel_doctor()

@settings_router.get("/channels")
async def get_channels_status():
    """Returns the configuration and auth status of all supported platforms via Doctor."""
    from app.channels import run_channel_doctor
    doc = await run_channel_doctor()
    return doc.get("channels", {})

@router.post("/{session_id}/diagram")
async def generate_session_diagram(session_id: str, db: AsyncSession = Depends(get_db)):
    """Generates an SVG architecture/flow diagram from the session's PRD or
    executive summary (PaperBanana pattern: plan → visualize → critique)."""
    stmt = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.specs), selectinload(ResearchSession.clusters))
        .where(ResearchSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    # Prefer the latest PRD; fall back to executive summary + cluster titles
    source_md = ""
    if session.specs:
        source_md = max(session.specs, key=lambda s: s.created_at).markdown_content
    if not source_md:
        cluster_lines = "\n".join(f"## {c.title}" for c in session.clusters)
        source_md = f"## Problem\n{session.executive_summary or session.query}\n{cluster_lines}"

    agent = DiagramAgent()
    diagram = agent.generate(source_md, title=f"{session.query[:48]}")
    return diagram


# --- P0: Discovery Mode (velocity-ranked topic suggestions) ---
class DiscoverRequest(BaseModel):
    category: Optional[str] = None
    max_topics: int = 8


@router.post("/discover")
async def discover_topics(payload: DiscoverRequest):
    """Sweeps HN, arXiv, Polymarket & Techmeme in parallel and returns
    velocity-ranked topic briefs, each pre-resolved into a runnable query."""
    engine = DiscoveryEngine()
    return await engine.discover(category=payload.category, max_topics=payload.max_topics)


# --- P2: Watchlists (trend monitoring with delta diffs) ---
class WatchlistCreateRequest(BaseModel):
    topic: str
    channels: Optional[List[str]] = None
    subreddits: Optional[List[str]] = None
    interval_hours: int = 24


class WatchlistRunRequest(BaseModel):
    max_items: int = 60


def _watchlist_to_dict(w: WatchlistTopic, include_snapshots: bool = False) -> Dict[str, Any]:
    data = {
        "id": w.id,
        "topic": w.topic,
        "channels": w.channels or [],
        "subreddits": w.subreddits or [],
        "interval_hours": w.interval_hours,
        "active": w.active,
        "last_run_at": w.last_run_at.isoformat() if w.last_run_at else None,
        "last_session_id": w.last_session_id,
        "created_at": w.created_at.isoformat() if w.created_at else None,
        "runs": len(w.snapshots) if hasattr(w, "snapshots") else 0,
    }
    if include_snapshots:
        data["snapshots"] = [
            {
                "id": s.id,
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "metrics": s.metrics,
            }
            for s in sorted(w.snapshots, key=lambda x: x.created_at or x.id)[-20:]
        ]
    return data


@router.get("/watchlists")
async def list_watchlists(db: AsyncSession = Depends(get_db)):
    stmt = select(WatchlistTopic).order_by(WatchlistTopic.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    return [_watchlist_to_dict(w) for w in res.scalars().all()]


@router.post("/watchlists")
async def create_watchlist(payload: WatchlistCreateRequest, db: AsyncSession = Depends(get_db)):
    w = WatchlistTopic(
        topic=payload.topic.strip(),
        channels=payload.channels or ["reddit", "youtube", "hackernews"],
        subreddits=payload.subreddits or [],
        interval_hours=max(1, payload.interval_hours),
    )
    db.add(w)
    await db.commit()
    await db.refresh(w)
    return _watchlist_to_dict(w)


@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WatchlistTopic).where(WatchlistTopic.id == watchlist_id))
    w = res.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    await db.delete(w)
    await db.commit()
    return {"status": "deleted", "id": watchlist_id}


@router.post("/watchlists/{watchlist_id}/run")
async def run_watchlist(watchlist_id: str, payload: WatchlistRunRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Runs a fresh research sweep for the watchlist topic, snapshots the
    resulting themes, and diffs against the previous run's snapshot."""
    res = await db.execute(select(WatchlistTopic).where(WatchlistTopic.id == watchlist_id))
    w = res.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Create the underlying research session (reuses the whole pipeline)
    new_session = ResearchSession(
        query=w.topic,
        channels_used=w.channels or ["reddit", "youtube", "hackernews"],
        status="QUEUED",
        execution_mode="focus",
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    session_event_queues[new_session.id] = []

    watchlist_id_val = w.id
    channels_val = list(w.channels or ["reddit", "youtube", "hackernews"])
    topic_val = w.topic

    background_tasks.add_task(
        run_watchlist_pipeline,
        watchlist_id=watchlist_id_val,
        session_id=new_session.id,
        topic=topic_val,
        channels=channels_val,
        subreddits=list(w.subreddits or []),
        max_items=payload.max_items,
    )

    return {"session_id": new_session.id, "watchlist_id": watchlist_id_val, "status": "QUEUED"}


async def run_watchlist_pipeline(watchlist_id: str, session_id: str, topic: str, channels: List[str], subreddits: List[str], max_items: int):
    """Wrapper that runs the standard pipeline, then snapshots + diffs for the watchlist."""
    await run_research_pipeline(
        session_id=session_id,
        query=topic,
        channels=channels,
        subreddits=subreddits,
        max_items=max_items,
        execution_mode="focus",
        browser_approved=False,
    )

    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
            session = res.scalar_one_or_none()
            if not session or session.status != "COMPLETED":
                return

            clusters_payload = [
                {
                    "title": c.title,
                    "category": c.category,
                    "severity_score": c.severity_score,
                    "item_count": c.item_count,
                    "quotes": [
                        {"quote_text": q.quote_text, "permalink": q.permalink}
                        for q in (c.quotes or [])[:1]
                    ],
                }
                for c in session.clusters
            ]
            current_snapshot = build_snapshot(clusters_payload, session.total_items_scraped or 0, topic)

            # Fetch previous snapshot before inserting the new one
            prev_stmt = (
                select(WatchlistSnapshot)
                .where(WatchlistSnapshot.watchlist_id == watchlist_id)
                .order_by(WatchlistSnapshot.created_at.desc())
                .limit(1)
            )
            prev_res = await db.execute(prev_stmt)
            prev_snapshot = prev_res.scalar_one_or_none()
            previous_metrics = prev_snapshot.metrics if prev_snapshot else None

            delta = diff_snapshots(current_snapshot, previous_metrics)
            current_snapshot["delta"] = delta

            db.add(WatchlistSnapshot(
                watchlist_id=watchlist_id,
                session_id=session_id,
                metrics=current_snapshot,
            ))

            w_res = await db.execute(select(WatchlistTopic).where(WatchlistTopic.id == watchlist_id))
            w = w_res.scalar_one_or_none()
            if w:
                w.last_run_at = datetime.utcnow()
                w.last_session_id = session_id
            await db.commit()
            logger.info(f"Watchlist {watchlist_id} snapshot stored (delta status: {delta.get('status')})")
    except Exception as e:
        logger.error(f"Watchlist snapshot failed for {watchlist_id}: {e}", exc_info=True)


@router.get("/watchlists/{watchlist_id}")
async def get_watchlist(watchlist_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WatchlistTopic).where(WatchlistTopic.id == watchlist_id))
    w = res.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return _watchlist_to_dict(w, include_snapshots=True)


# --- P3: Automation Rules (event-triggered webhooks) ---
class AutomationRuleRequest(BaseModel):
    name: str
    event_type: str  # research.completed | seo.completed
    conditions: Optional[Dict[str, Any]] = None
    action_type: str = "webhook"
    action_config: Optional[Dict[str, Any]] = None


@router.get("/automations")
async def list_automations(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationRule).order_by(AutomationRule.created_at.desc()).limit(100))
    rules = res.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "event_type": r.event_type,
            "conditions": r.conditions or {},
            "action_type": r.action_type,
            "action_config": {k: ("***" if k == "secret" else v) for k, v in (r.action_config or {}).items()},
            "enabled": r.enabled,
            "fire_count": r.fire_count,
            "last_fired_at": r.last_fired_at.isoformat() if r.last_fired_at else None,
        }
        for r in rules
    ]


@router.post("/automations")
async def create_automation(payload: AutomationRuleRequest, db: AsyncSession = Depends(get_db)):
    if payload.event_type not in ("research.completed", "seo.completed"):
        raise HTTPException(status_code=400, detail="event_type must be 'research.completed' or 'seo.completed'")
    if payload.action_type != "webhook":
        raise HTTPException(status_code=400, detail="Only 'webhook' actions are supported currently")
    url = (payload.action_config or {}).get("url")
    if not url or not str(url).startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="action_config.url must be a valid http(s) URL")

    rule = AutomationRule(
        name=payload.name.strip(),
        event_type=payload.event_type,
        conditions=payload.conditions or {},
        action_type=payload.action_type,
        action_config=payload.action_config or {},
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": rule.id, "status": "created", "name": rule.name}


@router.delete("/automations/{rule_id}")
async def delete_automation(rule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted", "id": rule_id}


@router.post("/automations/{rule_id}/toggle")
async def toggle_automation(rule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    rule.enabled = not rule.enabled
    await db.commit()
    return {"id": rule.id, "enabled": rule.enabled}


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
    if "exa_api_key" in creds:
        setattr(settings, "EXA_API_KEY", creds["exa_api_key"].strip())
    if "xueqiu_cookie" in creds:
        setattr(settings, "XUEQIU_COOKIE", creds["xueqiu_cookie"].strip())

    return {"status": "success", "message": "Channel credentials updated successfully."}
