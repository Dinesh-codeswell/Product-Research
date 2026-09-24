"""SQLAlchemy Database Models for SEO Intelligence & Audit Engine"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class SeoAuditSession(Base):
    __tablename__ = "seo_audit_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    audit_type: Mapped[str] = mapped_column(String(32), default="quick")  # quick, full, geo, drift
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")     # QUEUED, RUNNING, COMPLETED, FAILED
    
    # 0-100 Aggregate & Sub-Scores
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    technical_score: Mapped[int] = mapped_column(Integer, default=0)
    geo_readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    onpage_score: Mapped[int] = mapped_column(Integer, default=0)
    image_score: Mapped[int] = mapped_column(Integer, default=0)
    
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SeoBaselineSnapshot(Base):
    __tablename__ = "seo_baseline_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    metrics_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
