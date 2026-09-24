"""SEO Intelligence & GEO Studio API Endpoints"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.models.seo_entities import SeoAuditSession, SeoBaselineSnapshot
from app.seo.engine import SeoAuditEngine

logger = logging.getLogger("pulseradar.seo")

router = APIRouter(prefix="/seo", tags=["SEO & GEO Studio"])

# In-memory SSE queues for real-time audit progress
audit_event_queues: Dict[str, List[Dict[str, Any]]] = {}

# Pydantic Schemas
class StartSeoAuditRequest(BaseModel):
    url: str
    audit_type: str = "quick"  # "quick", "full", "geo", "drift"

class GenerateSchemaRequest(BaseModel):
    url: str
    entity_type: Optional[str] = "Organization"

class GenerateMetaRequest(BaseModel):
    url: str

def publish_seo_event(audit_id: str, stage: str, progress: int, message: str, data: Optional[Dict[str, Any]] = None):
    evt = {
        "stage": stage,
        "progress": progress,
        "message": message,
        "data": data or {}
    }
    if audit_id in audit_event_queues:
        audit_event_queues[audit_id].append(evt)

async def run_seo_audit_pipeline(audit_id: str, url: str, audit_type: str):
    """Background task executing the complete SEO audit."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SeoAuditSession).where(SeoAuditSession.id == audit_id))
        session = res.scalar_one_or_none()
        if not session:
            logger.error(f"SeoAuditSession {audit_id} not found in database.")
            return

        session.status = "RUNNING"
        await db.commit()

        # Check for existing baseline snapshot for this domain
        parsed_domain = urlparse(url).netloc.lower()
        baseline_stmt = (
            select(SeoBaselineSnapshot)
            .where(SeoBaselineSnapshot.domain == parsed_domain)
            .order_by(SeoBaselineSnapshot.created_at.desc())
            .limit(1)
        )
        b_res = await db.execute(baseline_stmt)
        baseline_record = b_res.scalar_one_or_none()
        baseline_snapshot = baseline_record.metrics_snapshot if baseline_record else None

        engine = SeoAuditEngine()

        def on_progress(stage: str, pct: int, msg: str):
            publish_seo_event(audit_id, stage, pct, msg)

        try:
            audit_result = await engine.run_audit(
                url=url,
                audit_type=audit_type,
                baseline_snapshot=baseline_snapshot,
                progress_cb=on_progress
            )

            if not audit_result.get("success"):
                session.status = "FAILED"
                session.executive_summary = f"Audit failed: {audit_result.get('error')}"
                await db.commit()
                publish_seo_event(audit_id, "failed", 100, f"Audit failed: {audit_result.get('error')}")
                return

            scores = audit_result.get("scores", {})
            session.overall_score = scores.get("overall", 0)
            session.technical_score = scores.get("technical", 0)
            session.geo_readiness_score = scores.get("geo_readiness", 0)
            session.onpage_score = scores.get("onpage", 0)
            session.image_score = scores.get("image", 0)
            session.executive_summary = audit_result.get("executive_summary", "")
            session.results = audit_result
            session.status = "COMPLETED"

            # Save / update baseline snapshot
            if audit_result.get("new_snapshot"):
                new_b = SeoBaselineSnapshot(
                    url=url,
                    domain=parsed_domain,
                    metrics_snapshot=audit_result["new_snapshot"]
                )
                db.add(new_b)

            await db.commit()
            publish_seo_event(audit_id, "completed", 100, f"SEO & GEO audit completed successfully ({session.overall_score}/100)!", {
                "overall_score": session.overall_score,
                "geo_score": session.geo_readiness_score,
                "technical_score": session.technical_score
            })

        except Exception as e:
            logger.error(f"Error in SEO audit pipeline: {e}", exc_info=True)
            session.status = "FAILED"
            session.executive_summary = f"Pipeline execution error: {str(e)}"
            await db.commit()
            publish_seo_event(audit_id, "failed", 100, f"Error: {str(e)}")

@router.post("/audit", response_model=Dict[str, str])
async def start_seo_audit(payload: StartSeoAuditRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Launches an asynchronous SEO & GEO audit for any web page or domain."""
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    domain = urlparse(url).netloc.lower()
    if not domain:
        raise HTTPException(status_code=400, detail="Invalid URL provided")

    audit_type = payload.audit_type if payload.audit_type in ["quick", "full", "geo", "drift"] else "quick"

    session = SeoAuditSession(
        url=url,
        domain=domain,
        audit_type=audit_type,
        status="QUEUED"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    audit_event_queues[session.id] = []

    background_tasks.add_task(
        run_seo_audit_pipeline,
        audit_id=session.id,
        url=url,
        audit_type=audit_type
    )

    return {"audit_id": session.id, "status": "QUEUED"}

@router.get("/audit/{audit_id}")
async def get_seo_audit(audit_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full status and audit results for a session."""
    stmt = select(SeoAuditSession).where(SeoAuditSession.id == audit_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="SEO audit session not found")
    return session

@router.get("/audit/{audit_id}/events")
async def stream_seo_events(audit_id: str):
    """Server-Sent Events (SSE) progress stream for live audit progress."""
    async def event_generator():
        last_index = 0
        timeout_ticks = 0

        while timeout_ticks < 120:  # 2 minute keep-alive
            if audit_id in audit_event_queues:
                events = audit_event_queues[audit_id]
                while last_index < len(events):
                    evt = events[last_index]
                    yield f"data: {json.dumps(evt)}\n\n"
                    last_index += 1
                    if evt.get("stage") in ("completed", "failed"):
                        return

            await asyncio.sleep(0.5)
            timeout_ticks += 1

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/audits", response_model=List[Dict[str, Any]])
async def list_recent_audits(limit: int = 15, db: AsyncSession = Depends(get_db)):
    """Lists recent SEO audits."""
    stmt = select(SeoAuditSession).order_by(SeoAuditSession.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return [
        {
            "id": s.id,
            "url": s.url,
            "domain": s.domain,
            "audit_type": s.audit_type,
            "status": s.status,
            "overall_score": s.overall_score,
            "technical_score": s.technical_score,
            "geo_readiness_score": s.geo_readiness_score,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in sessions
    ]

@router.post("/generate-schema")
async def generate_schema_direct(payload: GenerateSchemaRequest):
    """Direct utility to generate ready-to-use JSON-LD schema for a URL."""
    engine = SeoAuditEngine()
    crawl_data = await engine.crawler.crawl(payload.url)
    schemas = engine.schema_generator.generate_all(payload.url, crawl_data)
    return schemas

@router.post("/generate-meta")
async def generate_meta_direct(payload: GenerateMetaRequest):
    """Direct utility to generate optimized meta tags and SERP previews for a URL."""
    engine = SeoAuditEngine()
    crawl_data = await engine.crawler.crawl(payload.url)
    meta = engine.meta_generator.generate(payload.url, crawl_data)
    return meta

@router.get("/audit/{audit_id}/export/{format}")
async def export_seo_audit(audit_id: str, format: str = "markdown", db: AsyncSession = Depends(get_db)):
    """Exports the SEO & GEO Audit Dossier in Markdown or JSON format."""
    stmt = select(SeoAuditSession).where(SeoAuditSession.id == audit_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="SEO audit session not found")

    if format == "json":
        return session.results or {"error": "No results available"}

    # Markdown Export
    results = session.results or {}
    geo = results.get("geo", {})
    tech = results.get("technical", {})
    meta = results.get("meta", {})
    images = results.get("images", {})
    rendering = results.get("rendering", {})

    lines = [
        f"# PulseRadar SEO & GEO Audit Dossier: {session.url}",
        f"*Audited on {session.created_at.strftime('%Y-%m-%d %H:%M UTC')} • Audit Type: {session.audit_type.upper()}*",
        "",
        "## Overall Executive Scorecard",
        f"- **Composite Health Score:** `{session.overall_score} / 100`",
        f"- **Technical SEO Score:** `{session.technical_score} / 100`",
        f"- **AI Search Citation Readiness (GEO):** `{session.geo_readiness_score} / 100` ({geo.get('badge', 'N/A')})",
        f"- **On-Page & Schema Score:** `{session.onpage_score} / 100`",
        f"- **Image SEO Score:** `{session.image_score} / 100`",
        "",
        "---",
        "",
        "## 1. Executive Summary & Problem Framing",
        session.executive_summary or "No executive summary available.",
        "",
        "---",
        "",
        "## 2. Generative Engine Optimization (GEO) Analysis",
        f"**Readiness Tier:** {geo.get('readiness_tier')}",
        "",
        "### 4-Pillar Breakdown:",
        f"- **Evidence Density (35%):** {geo.get('pillars', {}).get('evidence_density', {}).get('score', 0)} / 35 ({geo.get('pillars', {}).get('evidence_density', {}).get('percentage', 0)}%)",
        f"- **Structure & Position (25%):** {geo.get('pillars', {}).get('structure_and_position', {}).get('score', 0)} / 25 ({geo.get('pillars', {}).get('structure_and_position', {}).get('percentage', 0)}%)",
        f"- **Authority Signals (25%):** {geo.get('pillars', {}).get('authority_signals', {}).get('score', 0)} / 25 ({geo.get('pillars', {}).get('authority_signals', {}).get('percentage', 0)}%)",
        f"- **AI Crawlability (15%):** {geo.get('pillars', {}).get('ai_crawlability', {}).get('score', 0)} / 15 ({geo.get('pillars', {}).get('ai_crawlability', {}).get('percentage', 0)}%)",
        "",
        "### Actionable AI Citation Recommendations:",
    ]
    for r in geo.get("recommendations", []):
        lines.append(f"- {r}")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Technical SEO & Crawl Diagnostics",
        f"- **HTTP Status Code:** {tech.get('status_code')}",
        f"- **Server Response Time:** {tech.get('response_time_ms')} ms",
        f"- **Word Count:** {tech.get('word_count')} words",
        f"- **Canonical URL:** `{tech.get('canonical', {}).get('url')}`",
        f"- **Robots Directive:** `{tech.get('robots', {}).get('content') or 'None (Indexable)'}`",
        "",
        "### Technical Issues Flagged:"
    ])
    for iss in tech.get("issues", []):
        lines.append(f"- `[{iss.get('severity')}]` {iss.get('field', 'General')}: {iss.get('message')}")

    if rendering.get("tested"):
        lines.extend([
            "",
            "---",
            "",
            "## 4. Playwright Client-Side Rendering (CSR) Gap Audit",
            f"- **Rendering Mode:** `{rendering.get('rendering_mode')}`",
            f"- **SSR Word Count:** {rendering.get('ssr', {}).get('word_count')} words",
            f"- **CSR Post-Hydration Word Count:** {rendering.get('csr', {}).get('word_count')} words",
            f"- **Net Difference:** +{rendering.get('words_difference')} words ({rendering.get('word_growth_ratio')}x growth)",
            f"- **Risk Level:** `{rendering.get('risk_level')}`"
        ])
        for f in rendering.get("findings", []):
            lines.append(f"- `[{f.get('severity')}]` **{f.get('title')}:** {f.get('description')}")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Recommended Meta Tags & SERP Preview",
        f"**SERP Preview Title:** {meta.get('serp_simulation', {}).get('title')}",
        f"**SERP Description:** {meta.get('recommended_description', {}).get('text')}",
        "",
        "```html",
        meta.get("html_code_block", ""),
        "```",
        "",
        "---",
        "",
        "## 6. Generated JSON-LD Structured Data",
        "```json",
        json.dumps(results.get("schemas", {}).get("generated_templates", {}).get("organization", {}), indent=2),
        "```"
    ])

    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=seo_audit_{session.id}.md"}
    )
