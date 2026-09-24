"""End-to-End Integration Test for PulseRadar Research Pipeline"""
import pytest
import asyncio
import uuid
from app.api.v1.research import run_research_pipeline
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import ResearchSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@pytest.mark.anyio
async def test_full_pipeline_e2e():
    await init_db()

    # 1. Create session in DB with unique id
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        new_session = ResearchSession(
            id=session_id,
            query="Supabase vs Firebase complaints",
            channels_used=["reddit", "youtube"],
            status="QUEUED"
        )
        db.add(new_session)
        await db.commit()

    # 2. Run pipeline
    await run_research_pipeline(
        session_id=session_id,
        query="Supabase vs Firebase complaints",
        channels=["reddit", "youtube"],
        subreddits=[],
        max_items=20
    )

    # 3. Verify outputs
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ResearchSession)
            .options(
                selectinload(ResearchSession.clusters).selectinload(ResearchSession.clusters.property.mapper.class_.quotes),
                selectinload(ResearchSession.feedbacks)
            )
            .where(ResearchSession.id == session_id)
        )
        res = await db.execute(stmt)
        session = res.scalar_one()

        assert session.status == "COMPLETED"
        assert session.total_items_scraped > 0
        assert session.executive_summary is not None
        assert len(session.clusters) > 0

        # Verify cluster structure
        for cluster in session.clusters:
            assert cluster.title is not None
            assert cluster.category in ["PAIN_POINT", "WORKAROUND", "DESIRE", "CHURN_TRIGGER"]
            assert len(cluster.quotes) > 0
            for quote in cluster.quotes:
                assert quote.quote_text is not None
                assert quote.permalink.startswith("http")
