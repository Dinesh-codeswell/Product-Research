"""Pydantic v2 Validation Schemas for PulseRadar API"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Requests ---
class StartResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Product, competitor, or problem statement to research")
    channels: List[str] = Field(default=["reddit", "youtube"], description="Channels to crawl")
    subreddits: Optional[List[str]] = Field(default=None, description="Optional targeted subreddits")
    max_items: int = Field(default=60, ge=10, le=200, description="Max feedback items to harvest across channels")
    execution_mode: Optional[str] = Field(default="focus", description="Execution mode: 'focus' (silent background) or 'browser' (interactive agent control)")
    browser_approved: Optional[bool] = Field(default=False, description="User consent to spawn visible browser session")

class GenerateSpecRequest(BaseModel):
    spec_type: str = Field(default="PRD", description="Type of spec to generate: PRD, OPPORTUNITY_TREE")
    custom_instructions: Optional[str] = Field(default=None, description="Optional custom focus or guidance for the spec")

# --- Responses ---
class EvidenceQuoteSchema(BaseModel):
    id: str
    quote_text: str
    permalink: str
    source_author: Optional[str] = None
    source_channel: str
    engagement_score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InsightClusterSchema(BaseModel):
    id: str
    title: str
    category: str  # PAIN_POINT, WORKAROUND, DESIRE, CHURN_TRIGGER
    description: str
    severity_score: float
    item_count: int
    keyword_tags: List[str]
    quotes: List[EvidenceQuoteSchema] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RawFeedbackSchema(BaseModel):
    id: str
    channel: str
    url: str
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    engagement_score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResearchSessionResponse(BaseModel):
    id: str
    query: str
    category: Optional[str] = None
    channels_used: List[str]
    status: str
    total_items_scraped: int
    execution_mode: Optional[str] = "focus"
    executive_summary: Optional[str] = None
    clusters: List[InsightClusterSchema] = []
    feedbacks: List[RawFeedbackSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GeneratedSpecResponse(BaseModel):
    id: str
    session_id: str
    spec_type: str
    markdown_content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- SSE Progress Event Schema ---
class SSEProgressEvent(BaseModel):
    stage: str
    percent: int
    message: str
    data: Optional[Dict[str, Any]] = None
