"""SQLAlchemy Database Models for PulseRadar"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    channels_used: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    total_items_scraped: Mapped[int] = mapped_column(Integer, default=0)
    execution_mode: Mapped[str] = mapped_column(String(32), default="focus")  # focus or browser
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feedbacks: Mapped[List["RawFeedback"]] = relationship("RawFeedback", back_populates="session", cascade="all, delete-orphan", lazy="selectin")
    clusters: Mapped[List["InsightCluster"]] = relationship("InsightCluster", back_populates="session", cascade="all, delete-orphan", lazy="selectin")
    specs: Mapped[List["GeneratedSpec"]] = relationship("GeneratedSpec", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

class RawFeedback(Base):
    __tablename__ = "raw_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # reddit, youtube, hackernews
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)  # upvotes, views, comments
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)  # -1.0 to 1.0
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="feedbacks")

class InsightCluster(Base):
    __tablename__ = "insight_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # PAIN_POINT, WORKAROUND, DESIRE, CHURN_TRIGGER
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    keyword_tags: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="clusters")
    quotes: Mapped[List["EvidenceQuote"]] = relationship("EvidenceQuote", back_populates="cluster", cascade="all, delete-orphan", lazy="selectin")

class EvidenceQuote(Base):
    __tablename__ = "evidence_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("insight_clusters.id", ondelete="CASCADE"), nullable=False)
    feedback_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    permalink: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_channel: Mapped[str] = mapped_column(String(50), default="reddit")
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cluster: Mapped["InsightCluster"] = relationship("InsightCluster", back_populates="quotes")

class GeneratedSpec(Base):
    __tablename__ = "generated_specs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    spec_type: Mapped[str] = mapped_column(String(50), default="PRD")  # PRD, OPPORTUNITY_TREE
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="specs")
