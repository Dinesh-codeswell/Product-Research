"""Database Entities for Watchlists, Automations & Trend Monitoring (P2/P3)"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Text, Integer, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())


class WatchlistTopic(Base):
    """A tracked topic whose research runs are diffed over time (trend deltas)."""
    __tablename__ = "watchlist_topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    channels: Mapped[dict] = mapped_column(JSON, default=list)
    subreddits: Mapped[dict] = mapped_column(JSON, default=list)
    interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    snapshots: Mapped[List["WatchlistSnapshot"]] = relationship(
        "WatchlistSnapshot", back_populates="watchlist", cascade="all, delete-orphan", lazy="selectin"
    )


class WatchlistSnapshot(Base):
    """Frozen per-run metrics for one watchlist topic (used for delta diffs)."""
    __tablename__ = "watchlist_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    watchlist_id: Mapped[str] = mapped_column(String(36), ForeignKey("watchlist_topics.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)   # clusters, top themes, totals
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    watchlist: Mapped["WatchlistTopic"] = relationship("WatchlistTopic", back_populates="snapshots")


class AutomationRule(Base):
    """Event-triggered rule: when <event> matches <conditions>, do <action>."""
    __tablename__ = "automation_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)   # research.completed | seo.completed
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)          # e.g. {"min_severity": 0.8} or {"score_below": 60}
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # webhook | create_task
    action_config: Mapped[dict] = mapped_column(JSON, default=dict)       # e.g. {"url": "https://hooks..."}
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fire_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationLog(Base):
    """Audit trail of fired automations."""
    __tablename__ = "automation_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_rules.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="FIRED")  # FIRED, FAILED
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
