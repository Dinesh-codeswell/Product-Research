"""Office SDK Data Bridge & Document Export Router
Connects Consumer Research, SEO & GEO Audits, and Browser Sweeps into Univer Sheets/Docs
and provides real-time persistence, XLSX generation, and data synchronization.
"""

import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    openpyxl = None
    HAS_OPENPYXL = False

try:
    import pptx
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    HAS_PPTX = True
except ImportError:
    pptx = None
    HAS_PPTX = False

from app.core.database import get_db
from app.models.entities import EvidenceQuote, GeneratedSpec, InsightCluster, RawFeedback, ResearchSession
from app.models.seo_entities import SeoAuditSession

logger = logging.getLogger("pulseradar.office")

router = APIRouter(prefix="/office", tags=["Office Studio & Live SDK Bridge"])

DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DOCUMENTS_FILE = os.path.join(DOCUMENTS_DIR, "office_documents.json")


def _ensure_storage():
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    if not os.path.exists(DOCUMENTS_FILE):
        with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_documents() -> List[Dict[str, Any]]:
    _ensure_storage()
    try:
        with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading office documents: {e}")
        return []


def _save_documents(docs: List[Dict[str, Any]]):
    _ensure_storage()
    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)


# --- Schemas ---

class SaveDocumentPayload(BaseModel):
    id: Optional[str] = None
    title: str = "Untitled Document"
    doc_type: str = "sheets"  # "sheets", "docs", or "slides"
    source_type: Optional[str] = None  # "research", "seo", "browser", or None
    source_id: Optional[str] = None
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None


class ExportCustomXlsxPayload(BaseModel):
    title: str = "Office_Export"
    sheets: Dict[str, List[List[Any]]] = Field(default_factory=dict)


class ExportCustomPptxPayload(BaseModel):
    title: str = "Presentation"
    slides: Dict[str, Any] = Field(default_factory=dict)


def generate_pptx_from_slides(slides_data: Dict[str, Any], presentation_title: str = "Presentation") -> io.BytesIO:
    """Generates a professional 16:9 widescreen PowerPoint presentation (.pptx) from Univer slide data."""
    if not HAS_PPTX:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PowerPoint export engine (python-pptx) is not installed in the environment."
        )

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    slide_order = slides_data.get("slideOrder", [])
    slides_map = slides_data.get("slides", {})

    if not slide_order and slides_map:
        slide_order = list(slides_map.keys())

    for slide_id in slide_order:
        s_data = slides_map.get(slide_id, {})
        slide = prs.slides.add_slide(blank_layout)

        # Dark sleek background (#12141d)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(18, 20, 29)

        # Slide Category tag
        category = s_data.get("category", "")
        if category:
            cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
            c_tf = cat_box.text_frame
            cp = c_tf.paragraphs[0]
            cp.text = category.upper()
            cp.font.name = "Arial"
            cp.font.size = Pt(11)
            cp.font.bold = True
            cp.font.color.rgb = RGBColor(146, 129, 247)

        # Slide Title & Subtitle
        top_offset = Inches(0.7) if category else Inches(0.5)
        title_box = slide.shapes.add_textbox(Inches(0.8), top_offset, Inches(11.7), Inches(1.2))
        tf = title_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = s_data.get("title", "Untitled Slide")
        p_title.font.name = "Arial"
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = RGBColor(255, 255, 255)

        sub_text = s_data.get("subtitle", "")
        if sub_text:
            p_sub = tf.add_paragraph()
            p_sub.text = sub_text
            p_sub.font.name = "Arial"
            p_sub.font.size = Pt(13)
            p_sub.font.color.rgb = RGBColor(170, 175, 195)

        # Metrics cards
        metrics = s_data.get("metrics", [])
        has_metrics = bool(metrics)
        if has_metrics:
            num_metrics = min(len(metrics), 4)
            card_width = 11.7 / num_metrics
            for m_idx, m in enumerate(metrics[:4]):
                left = Inches(0.8 + m_idx * card_width)
                top = Inches(2.1)
                width = Inches(card_width - 0.25)
                height = Inches(1.3)

                shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(30, 32, 43)
                shape.line.color.rgb = RGBColor(58, 62, 80)

                m_tf = shape.text_frame
                m_tf.word_wrap = True
                mp1 = m_tf.paragraphs[0]
                mp1.text = str(m.get("value", ""))
                mp1.font.bold = True
                mp1.font.size = Pt(22)
                mp1.font.color.rgb = RGBColor(58, 211, 137)

                mp2 = m_tf.add_paragraph()
                mp2.text = str(m.get("label", ""))
                mp2.font.size = Pt(11)
                mp2.font.color.rgb = RGBColor(200, 205, 220)

        # Bullets
        bullets = s_data.get("bullets", [])
        content_top = Inches(3.6) if has_metrics else Inches(2.1)
        content_height = Inches(3.4) if has_metrics else Inches(4.8)

        if bullets:
            content_box = slide.shapes.add_textbox(Inches(0.8), content_top, Inches(11.7), content_height)
            ctf = content_box.text_frame
            ctf.word_wrap = True
            for b_idx, bullet in enumerate(bullets):
                bp = ctf.paragraphs[0] if b_idx == 0 else ctf.add_paragraph()
                bp.text = f"•  {bullet}"
                bp.font.name = "Arial"
                bp.font.size = Pt(15)
                bp.font.color.rgb = RGBColor(230, 235, 245)
                bp.space_after = Pt(10)

        # Quote
        quote = s_data.get("quote")
        if quote and quote.get("text"):
            q_top = Inches(5.4) if (has_metrics or bullets) else Inches(2.4)
            q_box = slide.shapes.add_textbox(Inches(0.8), q_top, Inches(11.7), Inches(1.5))
            qtf = q_box.text_frame
            qtf.word_wrap = True
            qp = qtf.paragraphs[0]
            qp.text = f"“{quote.get('text')}”"
            qp.font.italic = True
            qp.font.size = Pt(14)
            qp.font.color.rgb = RGBColor(255, 200, 100)

            author = quote.get("author") or "Evidence Source"
            channel = quote.get("channel") or ""
            qp2 = qtf.add_paragraph()
            qp2.text = f"— {author} {f'({channel.upper()})' if channel else ''}"
            qp2.font.size = Pt(11)
            qp2.font.color.rgb = RGBColor(160, 165, 180)

        # Speaker notes
        notes_text = s_data.get("speakerNotes", "")
        if notes_text:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = notes_text

    out = io.BytesIO()
    prs.save(out)
    out.seek(0)
    return out


# --- 1. Available Data Sources ---

@router.get("/sources", summary="List connectable sessions from Research and SEO")
async def list_available_sources(db: AsyncSession = Depends(get_db)):
    """Return recent completed research sessions and SEO audits that can be loaded into Office Studio."""
    # Fetch recent Research sessions with clusters eager loaded
    stmt_research = (
        select(ResearchSession)
        .options(selectinload(ResearchSession.clusters))
        .order_by(desc(ResearchSession.created_at))
        .limit(30)
    )
    res_research = await db.execute(stmt_research)
    research_sessions = res_research.scalars().all()

    # Fetch recent SEO audits
    stmt_seo = (
        select(SeoAuditSession)
        .order_by(desc(SeoAuditSession.created_at))
        .limit(30)
    )
    res_seo = await db.execute(stmt_seo)
    seo_sessions = res_seo.scalars().all()

    return {
        "research": [
            {
                "id": s.id,
                "title": s.query,
                "type": "research",
                "source_type": "research",
                "status": s.status,
                "clusters_count": len(s.clusters) if s.clusters else 0,
                "signals_count": s.total_items_scraped or 0,
                "items_count": s.total_items_scraped or 0,
                "execution_mode": s.execution_mode or "focus",
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "meta": {
                    "clusters_count": len(s.clusters) if s.clusters else 0,
                    "signals_count": s.total_items_scraped or 0,
                }
            }
            for s in research_sessions
        ],
        "seo": [
            {
                "id": s.id,
                "title": f"{s.domain} ({s.audit_type})",
                "url": s.url,
                "type": "seo",
                "source_type": "seo",
                "status": s.status,
                "overall_score": s.overall_score or 0,
                "geo_score": s.geo_readiness_score or 0,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "meta": {
                    "overall_score": s.overall_score or 0,
                    "geo_score": s.geo_readiness_score or 0,
                }
            }
            for s in seo_sessions
        ]
    }


# --- 2. Live Data Connectors (Univer-Compatible Workbook & Doc Snapshots) ---

@router.get("/connect/research/{session_id}", summary="Get research session pre-formatted for Univer Sheets and Docs")
async def connect_research_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Transforms a Consumer Discovery research session into structured Univer Workbook and Document data."""
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

    clusters_data = []
    for c in session.clusters:
        quotes_data = [
            {
                "quote_text": q.quote_text,
                "source_author": q.source_author or "Anonymous",
                "source_channel": q.source_channel,
                "engagement_score": q.engagement_score,
                "permalink": q.permalink
            }
            for q in c.quotes
        ]
        clusters_data.append({
            "title": c.title,
            "category": c.category,
            "description": c.description,
            "severity_score": c.severity_score,
            "item_count": c.item_count,
            "keyword_tags": c.keyword_tags if isinstance(c.keyword_tags, list) else [],
            "quotes": quotes_data
        })

    feedbacks_data = [
        {
            "author": f.author or "Anonymous",
            "channel": f.channel,
            "url": f.url,
            "title": f.title or "",
            "content": f.content,
            "sentiment_score": f.sentiment_score,
            "engagement_score": f.engagement_score
        }
        for f in session.feedbacks
    ]

    # Generate Univer Sheets Cell Matrix
    # Sheet 1: Executive Summary
    summary_cells = {
        "0": {
            "0": {"v": "PULSERADAR CONSUMER RESEARCH DOSSIER", "s": {"bold": True, "color": "#9281f7"}},
        },
        "1": {
            "0": {"v": "Research Query:", "s": {"bold": True}},
            "1": {"v": session.query}
        },
        "2": {
            "0": {"v": "Execution Mode:", "s": {"bold": True}},
            "1": {"v": (session.execution_mode or "focus").upper()}
        },
        "3": {
            "0": {"v": "Total Items Analyzed:", "s": {"bold": True}},
            "1": {"v": session.total_items_scraped}
        },
        "4": {
            "0": {"v": "Insight Clusters Identified:", "s": {"bold": True}},
            "1": {"v": len(session.clusters)}
        },
        "5": {
            "0": {"v": "Analysis Status:", "s": {"bold": True}},
            "1": {"v": session.status}
        },
        "7": {
            "0": {"v": "EXECUTIVE SYNTHESIS", "s": {"bold": True, "color": "#3ad389"}}
        },
        "8": {
            "0": {"v": session.executive_summary or "Inference and aggregation in progress."}
        }
    }

    # Sheet 2: Insight Clusters
    cluster_cells = {
        "0": {
            "0": {"v": "Cluster Title", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "1": {"v": "Category", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "2": {"v": "Severity (0-1)", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "3": {"v": "Evidence Count", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "4": {"v": "Keyword Tags", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "5": {"v": "Description & Opportunity", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
        }
    }
    for idx, c in enumerate(clusters_data, start=1):
        cluster_cells[str(idx)] = {
            "0": {"v": c["title"], "s": {"bold": True}},
            "1": {"v": c["category"]},
            "2": {"v": round(c["severity_score"], 2)},
            "3": {"v": c["item_count"]},
            "4": {"v": ", ".join(c["keyword_tags"]) if c["keyword_tags"] else "None"},
            "5": {"v": c["description"]},
        }

    # Sheet 3: Evidence Quotes
    quotes_cells = {
        "0": {
            "0": {"v": "Cluster", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "1": {"v": "Channel", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "2": {"v": "Author", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "3": {"v": "Engagement", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "4": {"v": "Direct Evidence Quote", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "5": {"v": "Source URL", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
        }
    }
    row_counter = 1
    for c in clusters_data:
        for q in c["quotes"]:
            quotes_cells[str(row_counter)] = {
                "0": {"v": c["title"]},
                "1": {"v": q["source_channel"].upper()},
                "2": {"v": q["source_author"]},
                "3": {"v": q["engagement_score"]},
                "4": {"v": q["quote_text"]},
                "5": {"v": q["permalink"]},
            }
            row_counter += 1

    # Structured Univer Workbook Payload
    sheet_order = ["sheet_summary", "sheet_clusters", "sheet_quotes"]
    sheets_dict = {
        "sheet_summary": {
            "id": "sheet_summary",
            "name": "Executive Summary",
            "cellData": summary_cells,
            "rowCount": 30,
            "columnCount": 10
        },
        "sheet_clusters": {
            "id": "sheet_clusters",
            "name": "Insight Clusters",
            "cellData": cluster_cells,
            "rowCount": max(50, len(clusters_data) + 10),
            "columnCount": 10
        },
        "sheet_quotes": {
            "id": "sheet_quotes",
            "name": "Verified Quotes & Citations",
            "cellData": quotes_cells,
            "rowCount": max(50, row_counter + 10),
            "columnCount": 10
        }
    }

    # Sheet 4: YouTube Video Transcripts (if video signals present)
    yt_feedbacks = [
        f for f in session.feedbacks
        if f.channel.lower() == "youtube" or "youtube.com" in f.url or "youtu.be" in f.url
    ]
    if yt_feedbacks:
        yt_cells = {
            "0": {
                "0": {"v": "Video Title & Reference", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
                "1": {"v": "Timestamp", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
                "2": {"v": "Spoken Dialogue / Transcript Cue", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
                "3": {"v": "Speaker / Channel", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
                "4": {"v": "Engagement", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
                "5": {"v": "Video Timestamp Link", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            }
        }
        for y_idx, yf in enumerate(yt_feedbacks, start=1):
            ts = (yf.raw_metadata or {}).get("timestamp") or "00:00"
            yt_cells[str(y_idx)] = {
                "0": {"v": yf.title or f"YouTube Video ({yf.external_id})", "s": {"bold": True}},
                "1": {"v": ts, "s": {"color": "#ff6465"}},
                "2": {"v": yf.content},
                "3": {"v": yf.author or "YouTube Contributor"},
                "4": {"v": yf.engagement_score or 0},
                "5": {"v": yf.url},
            }
        sheet_order.append("sheet_transcripts")
        sheets_dict["sheet_transcripts"] = {
            "id": "sheet_transcripts",
            "name": "YouTube Video Transcripts",
            "cellData": yt_cells,
            "rowCount": max(50, len(yt_feedbacks) + 10),
            "columnCount": 10
        }

    workbook_snapshot = {
        "id": f"wb_research_{session.id}",
        "name": f"Research: {session.query[:32]}",
        "sheetOrder": sheet_order,
        "sheets": sheets_dict
    }

    # Markdown Document Payload for Word/Doc Mode
    doc_markdown = f"""# {session.query}
**PulseRadar Autonomous Consumer Discovery Report**
*Generated: {session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'Real-time'} | Status: {session.status}*

---

## 1. Executive Summary
{session.executive_summary or 'Inference and aggregation in progress.'}

## 2. Key Insight Clusters & Pain Points
"""
    for idx, c in enumerate(clusters_data, start=1):
        doc_markdown += f"\n### 2.{idx} {c['title']} ({c['category']})\n"
        doc_markdown += f"- **Severity Score**: {round(c['severity_score'] * 100)}%\n"
        doc_markdown += f"- **Evidence Citations**: {c['item_count']} developer discussions\n"
        doc_markdown += f"- **Synthesis**: {c['description']}\n\n"
        if c["quotes"]:
            doc_markdown += "**Direct Evidence Quotes:**\n"
            for q in c["quotes"][:3]:
                doc_markdown += f"> \"{q['quote_text']}\"\n> — *{q['source_author']} ({q['source_channel'].upper()})*\n\n"

    if yt_feedbacks:
        doc_markdown += "\n## 3. Spoken YouTube Video Transcripts & Subtitles\n"
        for yf in yt_feedbacks[:8]:
            ts = (yf.raw_metadata or {}).get("timestamp") or "00:00"
            doc_markdown += f"- **[{ts}] [{yf.title or 'YouTube Video'}]({yf.url})**\n"
            doc_markdown += f"  > \"{yf.content}\"\n\n"

    # 6-Slide Univer Slide Presentation Model
    slide_1_metrics = [
        {"label": "Total Signals", "value": session.total_items_scraped or len(feedbacks_data)},
        {"label": "Insight Clusters", "value": len(clusters_data)},
        {"label": "Execution Mode", "value": (session.execution_mode or "focus").upper()},
        {"label": "Status", "value": session.status.upper()}
    ]
    slide_1_bullets = [
        f"Research Scope: Comprehensive multi-channel analysis for '{session.query}'.",
        f"Key Synthesis: {session.executive_summary[:200] + '...' if session.executive_summary else 'Inference and aggregation completed across live channels.'}",
        "Data ingested directly from Reddit, YouTube, X, and G2 discussions."
    ]

    slide_2_bullets = []
    for c in clusters_data[:4]:
        slide_2_bullets.append(f"{c['title']} ({c['category']}): Severity {round(c['severity_score']*100)}% — {c['description'][:140]}...")

    slide_3_quote = None
    slide_3_bullets = []
    all_quotes = [q for c in clusters_data for q in c["quotes"]]
    if all_quotes:
        slide_3_quote = {
            "text": all_quotes[0]["quote_text"],
            "author": all_quotes[0]["source_author"],
            "channel": all_quotes[0]["source_channel"]
        }
        for q in all_quotes[1:4]:
            slide_3_bullets.append(f"\"{q['quote_text'][:120]}...\" — {q['source_author']} ({q['source_channel'].upper()})")

    slide_4_bullets = []
    for yf in yt_feedbacks[:4]:
        ts = (yf.raw_metadata or {}).get("timestamp") or "00:00"
        slide_4_bullets.append(f"[{ts}] {yf.title or 'YouTube Video'}: \"{yf.content[:120]}...\"")

    slide_5_bullets = [
        "Feature Spec 1: Implement direct zero-latency automated workflow addressing core friction points.",
        "Feature Spec 2: Add real-time alerting and automated telemetry metrics for active clusters.",
        "Target Persona: Developers and product owners seeking automated evidence extraction.",
        "ROI Projection: High impact on retention by eliminating manual transcript and sentiment reviews."
    ]

    slide_6_bullets = [
        "Immediate Action: Validate top 2 clusters with rapid prototype feedback loops.",
        "Short Term: Export PRD specifications directly to issue trackers and engineering backlog.",
        "Monitoring: Track daily signal frequency and sentiment shifts across integrated channels."
    ]

    slides_snapshot = {
        "id": f"slides_research_{session.id}",
        "title": f"Pitch Deck: {session.query[:32]}",
        "pageSize": {"width": 960, "height": 540},
        "slideOrder": ["slide_1", "slide_2", "slide_3", "slide_4", "slide_5", "slide_6"],
        "slides": {
            "slide_1": {
                "id": "slide_1",
                "title": session.query,
                "subtitle": "PulseRadar Autonomous Consumer Discovery Pitch Deck",
                "category": "1. Executive Summary & Overview",
                "layout": "metrics",
                "metrics": slide_1_metrics,
                "bullets": slide_1_bullets,
                "speakerNotes": f"Executive presentation briefing for research query: {session.query}."
            },
            "slide_2": {
                "id": "slide_2",
                "title": "Key Problem Signals & Pain Points",
                "subtitle": "Synthesized Developer & Consumer Friction Clusters",
                "category": "2. Friction & Pain Points",
                "layout": "bullets",
                "bullets": slide_2_bullets or ["No high-severity friction clusters identified."],
                "speakerNotes": "Review prioritized friction clusters and severity scores to inform roadmap."
            },
            "slide_3": {
                "id": "slide_3",
                "title": "Voice of the Customer & Market Evidence",
                "subtitle": "Verbatim Developer Feedback from Reddit, YouTube, X & G2",
                "category": "3. Customer Evidence",
                "layout": "quote",
                "quote": slide_3_quote,
                "bullets": slide_3_bullets,
                "speakerNotes": "Verbatim testimonials validating customer pain points."
            },
            "slide_4": {
                "id": "slide_4",
                "title": "YouTube Video Transcripts & Spoken Dialogue",
                "subtitle": "Timestamped Expert Opinions & Video Analysis",
                "category": "4. Video Analysis",
                "layout": "bullets",
                "bullets": slide_4_bullets or ["No spoken video transcripts extracted for this query."],
                "speakerNotes": "Video discussion points with second-level timestamps."
            },
            "slide_5": {
                "id": "slide_5",
                "title": "Strategic PRD & Feature Specifications",
                "subtitle": "Actionable Product Specs Driven by Extracted Signals",
                "category": "5. Product Requirements",
                "layout": "bullets",
                "bullets": slide_5_bullets,
                "speakerNotes": "High-priority specifications derived from consumer pain points."
            },
            "slide_6": {
                "id": "slide_6",
                "title": "Execution Roadmap & Next Actions",
                "subtitle": "Timeline, Milestones & Immediate Deliverables",
                "category": "6. Roadmap & Next Steps",
                "layout": "bullets",
                "bullets": slide_6_bullets,
                "speakerNotes": "Immediate next steps for engineering and product leadership."
            }
        }
    }

    return {
        "source_type": "research",
        "source_id": session.id,
        "session_id": session.id,
        "query": session.query,
        "title": f"Research - {session.query}",
        "summary": session.executive_summary or f"Research dossier for {session.query}",
        "workbook": workbook_snapshot,
        "document_markdown": doc_markdown,
        "markdown": doc_markdown,
        "document": {
            "title": f"Research - {session.query}",
            "markdown": doc_markdown
        },
        "slides": slides_snapshot,
        "stats": {
            "total_items": session.total_items_scraped,
            "clusters_count": len(session.clusters),
            "feedbacks_count": len(session.feedbacks)
        }
    }


@router.get("/connect/seo/{audit_id}", summary="Get SEO audit pre-formatted for Univer Sheets and Docs")
async def connect_seo_session(audit_id: str, db: AsyncSession = Depends(get_db)):
    """Transforms an SEO & GEO Audit into structured Univer Workbook and Document data."""
    stmt = select(SeoAuditSession).where(SeoAuditSession.id == audit_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="SEO audit session not found")

    results = session.results or {}
    geo = results.get("geo") or {}
    tech = results.get("technical") or {}
    rendering = results.get("rendering") or {}
    meta = results.get("meta") or {}
    keywords = results.get("keywords") or {}
    images = results.get("images") or {}
    ai_insights = results.get("ai_insights") or {}

    # Sheet 1: Scorecard & Overview
    summary_cells = {
        "0": {
            "0": {"v": "PULSERADAR SEO & GEO CITATION AUDIT", "s": {"bold": True, "color": "#9281f7"}},
        },
        "1": {"0": {"v": "Audited Domain:", "s": {"bold": True}}, "1": {"v": session.domain}},
        "2": {"0": {"v": "Full Target URL:", "s": {"bold": True}}, "1": {"v": session.url}},
        "3": {"0": {"v": "Audit Type:", "s": {"bold": True}}, "1": {"v": session.audit_type.upper()}},
        "4": {"0": {"v": "Audit Status:", "s": {"bold": True}}, "1": {"v": session.status}},
        "6": {"0": {"v": "EXECUTIVE COMPOSITE SCORES", "s": {"bold": True, "color": "#3ad389"}}},
        "7": {"0": {"v": "Overall Health Score (0-100)", "s": {"bold": True}}, "1": {"v": session.overall_score}},
        "8": {"0": {"v": "GEO AI Citation Readiness Score (0-100)", "s": {"bold": True}}, "1": {"v": session.geo_readiness_score}},
        "9": {"0": {"v": "Technical SEO Crawl Score", "s": {"bold": True}}, "1": {"v": session.technical_score}},
        "10": {"0": {"v": "On-Page & Schema Score", "s": {"bold": True}}, "1": {"v": session.onpage_score}},
        "11": {"0": {"v": "Image SEO Optimization Score", "s": {"bold": True}}, "1": {"v": session.image_score}},
        "13": {"0": {"v": "EXECUTIVE DOSSIER SUMMARY", "s": {"bold": True}}},
        "14": {"0": {"v": session.executive_summary or "Audit complete."}}
    }

    # Sheet 2: GEO AI Citation Matrix (Perplexity, ChatGPT, Gemini)
    geo_pillars = geo.get("pillars") or {}
    geo_cells = {
        "0": {
            "0": {"v": "GEO Pillar", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "1": {"v": "Score", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "2": {"v": "Max", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "3": {"v": "Readiness %", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "4": {"v": "Key Signal Evaluation Notes", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
        }
    }
    r_idx = 1
    for p_name, p_data in geo_pillars.items():
        notes = []
        for itm in p_data.get("items", []):
            notes.append(f"{itm.get('rule')}: {itm.get('status')} ({itm.get('notes', '')})")
        geo_cells[str(r_idx)] = {
            "0": {"v": p_name.replace("_", " ").upper(), "s": {"bold": True}},
            "1": {"v": p_data.get("score", 0)},
            "2": {"v": p_data.get("max", 25)},
            "3": {"v": f"{p_data.get('percentage', 0)}%"},
            "4": {"v": " | ".join(notes)},
        }
        r_idx += 1

    # Sheet 3: Meta & Title Optimization Variants
    title_variants = meta.get("title_variants") or []
    meta_cells = {
        "0": {
            "0": {"v": "Variant Type", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "1": {"v": "Suggested Title Tag", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "2": {"v": "Char Count", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "3": {"v": "Status", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "4": {"v": "CTR & Search Rationale", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
        }
    }
    for idx, tv in enumerate(title_variants, start=1):
        meta_cells[str(idx)] = {
            "0": {"v": tv.get("variant", ""), "s": {"bold": True}},
            "1": {"v": tv.get("title", "")},
            "2": {"v": tv.get("char_count", 0)},
            "3": {"v": tv.get("status", "OPTIMAL")},
            "4": {"v": tv.get("description", "")},
        }

    # Sheet 4: Top Keywords & Content Density
    top_kws = keywords.get("top_keywords") or []
    kw_cells = {
        "0": {
            "0": {"v": "Keyword / Entity", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "1": {"v": "Frequency", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "2": {"v": "Density %", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "3": {"v": "Search Intent", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "4": {"v": "In H1", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "5": {"v": "In H2", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
            "6": {"v": "Prominence", "s": {"bold": True, "bg": "#1e2029", "color": "#ffffff"}},
        }
    }
    for idx, k in enumerate(top_kws[:30], start=1):
        kw_cells[str(idx)] = {
            "0": {"v": k.get("keyword", ""), "s": {"bold": True}},
            "1": {"v": k.get("frequency", 0)},
            "2": {"v": f"{k.get('density_percent', 0)}%"},
            "3": {"v": k.get("intent", "INFORMATIONAL")},
            "4": {"v": "YES" if k.get("in_h1") else "NO"},
            "5": {"v": "YES" if k.get("in_h2") else "NO"},
            "6": {"v": k.get("prominence", "MEDIUM")},
        }

    workbook_snapshot = {
        "id": f"wb_seo_{session.id}",
        "name": f"SEO: {session.domain}",
        "sheetOrder": ["sheet_overview", "sheet_geo", "sheet_meta", "sheet_keywords"],
        "sheets": {
            "sheet_overview": {
                "id": "sheet_overview",
                "name": "Executive Scorecard",
                "cellData": summary_cells,
                "rowCount": 30,
                "columnCount": 8
            },
            "sheet_geo": {
                "id": "sheet_geo",
                "name": "GEO AI Citation Matrix",
                "cellData": geo_cells,
                "rowCount": 20,
                "columnCount": 8
            },
            "sheet_meta": {
                "id": "sheet_meta",
                "name": "SERP & Title Variants",
                "cellData": meta_cells,
                "rowCount": 20,
                "columnCount": 8
            },
            "sheet_keywords": {
                "id": "sheet_keywords",
                "name": "Keywords & Entities",
                "cellData": kw_cells,
                "rowCount": max(30, len(top_kws) + 5),
                "columnCount": 8
            }
        }
    }

    doc_markdown = f"""# SEO & GEO Strategic Audit: {session.domain}
**Target URL**: {session.url}
**Audit Date**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'Live'}

---

## 1. Executive Summary
- **Overall Health**: {session.overall_score}/100
- **GEO AI Citation Readiness**: {session.geo_readiness_score}/100
- **Technical Crawl Score**: {session.technical_score}/100
- **On-Page & Schema**: {session.onpage_score}/100
- **Image Optimization**: {session.image_score}/100

{session.executive_summary or 'Verified crawl completed.'}

## 2. AI Engine Strategic Positioning (GEO)
- **Brand Entity Recognition**: {ai_insights.get('brand_positioning', 'Verified Brand')}
- **Citation Readiness Verdict**: {ai_insights.get('geo_readiness', 'Optimized for LLM retrieval.')}

### Recommended Title Tag & SERP Optimization
- **Recommended Title**: {ai_insights.get('high_ctr_serp_title') or (title_variants[0].get('title') if title_variants else session.domain)}
- **Recommended Meta Description**: {ai_insights.get('high_ctr_meta_description') or meta.get('recommended_description', {}).get('text', '')}
"""

    # 6-Slide Univer Slide Presentation Model for SEO
    geo_score = session.geo_readiness_score or 0
    word_count = keywords.get("word_count", 0)
    render_mode = rendering.get("rendering_mode", "UNKNOWN")
    risk_level = rendering.get("risk_level", "LOW")

    seo_slide_1_metrics = [
        {"label": "Overall Score", "value": f"{session.overall_score}/100"},
        {"label": "GEO Readiness", "value": f"{geo_score}/100"},
        {"label": "Word Count", "value": word_count},
        {"label": "CSR Risk", "value": risk_level}
    ]
    seo_slide_1_bullets = [
        f"Audited Domain: {session.domain} ({session.url})",
        f"Audit Type: {session.audit_type.upper()} | Execution: {session.status.upper()}",
        f"AI Citation Readiness: {'HIGH' if geo_score >= 70 else 'MODERATE' if geo_score >= 50 else 'LOW'}"
    ]

    p_scores = geo.get("pillar_scores") or geo.get("pillars") or {}
    seo_slide_2_bullets = []
    if isinstance(p_scores, dict):
        for pk, pv in p_scores.items():
            if isinstance(pv, dict):
                seo_slide_2_bullets.append(f"{pk.replace('_', ' ').title()}: Score {pv.get('score', 0)}/{pv.get('max', 25)} ({pv.get('percentage', 0)}%)")
    if not seo_slide_2_bullets:
        seo_slide_2_bullets = [
            "Evidence Density: High density of statistical facts and numerical claims",
            "Inverted Pyramid Structure: Direct upfront answer before elaborating details",
            "E-E-A-T Authority: Verified author credentials and outbound reputable citations",
            "Bot Crawlability: Open robots.txt directives for OpenAI, Claude, and Perplexity"
        ]

    seo_slide_3_bullets = [
        f"Rendering Architecture: {render_mode}",
        f"SSR Baseline Words: {rendering.get('ssr', {}).get('word_count', 0)} words",
        f"CSR Hydrated Words: {rendering.get('csr', {}).get('word_count', 0)} words",
        f"Dynamic Gap: +{rendering.get('words_difference', 0)} words ({rendering.get('word_growth_ratio', 1.0)}x post-hydration growth)",
        f"Recommendation: {'Pre-render dynamic content server-side to prevent bot drop-off.' if risk_level == 'HIGH' else 'Server-side rendering is healthy.'}"
    ]

    ai_bots = tech.get("robots_txt", {}).get("ai_bot_access", {})
    seo_slide_4_bullets = [
        f"GPTBot (OpenAI / ChatGPT): {'ALLOWED' if ai_bots.get('gptbot', {}).get('allowed') else 'BLOCKED'}",
        f"ClaudeBot (Anthropic Claude): {'ALLOWED' if ai_bots.get('claudebot', {}).get('allowed') else 'BLOCKED'}",
        f"PerplexityBot (Perplexity AI): {'ALLOWED' if ai_bots.get('perplexitybot', {}).get('allowed') else 'BLOCKED'}",
        f"Google-Extended (Gemini): {'ALLOWED' if ai_bots.get('google_extended', {}).get('allowed') else 'BLOCKED'}"
    ]

    top_kw = keywords.get("top_keywords", [])
    seo_slide_5_bullets = [
        f"Keyword '{k.get('keyword')}': Density {k.get('density_percent')}% (Intent: {k.get('intent', 'Informational')})"
        for k in top_kw[:4]
    ] or ["Keyword extraction complete."]

    recs = geo.get("recommendations", [])
    seo_slide_6_bullets = [f"Fix: {r}" for r in recs[:5]] or [
        "Add explicit schema markup (TechArticle, Product, Organization)",
        "Allow AI search crawlers in robots.txt without Cloudflare challenge walls",
        "Introduce structured evidence tables and verified statistical numbers"
    ]

    seo_slides_snapshot = {
        "id": f"slides_seo_{session.id}",
        "title": f"SEO & GEO Deck: {session.domain}",
        "pageSize": {"width": 960, "height": 540},
        "slideOrder": ["slide_1", "slide_2", "slide_3", "slide_4", "slide_5", "slide_6"],
        "slides": {
            "slide_1": {
                "id": "slide_1",
                "title": f"SEO & GEO Audit: {session.domain}",
                "subtitle": "Generative Engine Optimization & Technical Health Deck",
                "category": "1. Executive Scorecard",
                "layout": "metrics",
                "metrics": seo_slide_1_metrics,
                "bullets": seo_slide_1_bullets,
                "speakerNotes": f"Executive briefing for domain: {session.domain}."
            },
            "slide_2": {
                "id": "slide_2",
                "title": "4-Pillar Generative Engine Optimization (GEO)",
                "subtitle": "AI Search Engine Citation Readiness & Breakdown",
                "category": "2. GEO Pillars",
                "layout": "bullets",
                "bullets": seo_slide_2_bullets,
                "speakerNotes": "Evaluation across evidence density, inverted pyramid, EEAT, and crawlability."
            },
            "slide_3": {
                "id": "slide_3",
                "title": "Playwright Client Rendering & Hydration Gap",
                "subtitle": "SSR vs Post-Hydration Content Availability",
                "category": "3. Rendering Gap",
                "layout": "bullets",
                "bullets": seo_slide_3_bullets,
                "speakerNotes": "Analysis of JavaScript hydration gaps that may prevent AI scrapers from indexing content."
            },
            "slide_4": {
                "id": "slide_4",
                "title": "AI Scraper & Search Bot Crawlability",
                "subtitle": "Robots.txt Directives for Leading LLMs",
                "category": "4. Bot Crawlability",
                "layout": "bullets",
                "bullets": seo_slide_4_bullets,
                "speakerNotes": "Robots.txt status for major AI search engines."
            },
            "slide_5": {
                "id": "slide_5",
                "title": "Keyword & Semantic Entity Distribution",
                "subtitle": "High-Intent Keyword Density & Topic Prominence",
                "category": "5. Keywords & Semantics",
                "layout": "bullets",
                "bullets": seo_slide_5_bullets,
                "speakerNotes": "High opportunity keywords for search traffic and AI answer engines."
            },
            "slide_6": {
                "id": "slide_6",
                "title": "Strategic SEO & GEO Roadmap",
                "subtitle": "Actionable Technical Priorities & Schema Optimization",
                "category": "6. Action Plan",
                "layout": "bullets",
                "bullets": seo_slide_6_bullets,
                "speakerNotes": "High-impact recommendations for immediate ranking improvement."
            }
        }
    }

    return {
        "source_type": "seo",
        "source_id": session.id,
        "audit_id": session.id,
        "domain": session.domain,
        "url": session.url,
        "title": f"SEO - {session.domain}",
        "summary": session.executive_summary or f"SEO & GEO Audit for {session.domain}",
        "workbook": workbook_snapshot,
        "document_markdown": doc_markdown,
        "markdown": doc_markdown,
        "document": {
            "title": f"SEO - {session.domain}",
            "markdown": doc_markdown
        },
        "slides": seo_slides_snapshot,
        "scores": {
            "overall": session.overall_score,
            "geo": session.geo_readiness_score,
            "technical": session.technical_score,
            "onpage": session.onpage_score,
            "image": session.image_score
        }
    }


# --- 3. Native Excel (.xlsx) and PowerPoint (.pptx) Streaming Endpoints ---

def _style_excel_sheet(ws, title: str):
    """Apply Resend-style clean dark/corporate aesthetics to openpyxl worksheets."""
    if not HAS_OPENPYXL:
        return
    header_fill = PatternFill(start_color="1E2029", end_color="1E2029", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    # Style row 1
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
            cell.border = thin_border
            if cell.row > 1:
                cell.font = Font(name="Calibri", size=10)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 60)


@router.get("/export/research/{session_id}/xlsx", summary="Download native Excel (.xlsx) file for a research session")
async def export_research_xlsx(session_id: str, db: AsyncSession = Depends(get_db)):
    """Generates and streams a professional, multi-tab Excel workbook for a research session."""
    if not HAS_OPENPYXL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Excel export engine (openpyxl) is not installed in the environment."
        )
    data = await connect_research_session(session_id, db)
    wb_data = data["workbook"]["sheets"]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet

    # Tab 1: Summary
    ws_sum = wb.create_sheet(title="Executive Summary")
    ws_sum.append(["Metric / Field", "Value / Description"])
    sum_cells = wb_data["sheet_summary"]["cellData"]
    for r in range(1, 25):
        row_str = str(r)
        if row_str in sum_cells:
            c0 = sum_cells[row_str].get("0", {}).get("v", "")
            c1 = sum_cells[row_str].get("1", {}).get("v", "")
            if c0 or c1:
                ws_sum.append([c0, c1])
    _style_excel_sheet(ws_sum, "Executive Summary")

    # Tab 2: Insight Clusters
    ws_clusters = wb.create_sheet(title="Insight Clusters")
    ws_clusters.append(["Cluster Title", "Category", "Severity Score", "Evidence Count", "Keyword Tags", "Description"])
    c_cells = wb_data["sheet_clusters"]["cellData"]
    for r in range(1, 100):
        row_str = str(r)
        if row_str in c_cells:
            ws_clusters.append([
                c_cells[row_str].get("0", {}).get("v", ""),
                c_cells[row_str].get("1", {}).get("v", ""),
                c_cells[row_str].get("2", {}).get("v", ""),
                c_cells[row_str].get("3", {}).get("v", ""),
                c_cells[row_str].get("4", {}).get("v", ""),
                c_cells[row_str].get("5", {}).get("v", "")
            ])
    _style_excel_sheet(ws_clusters, "Insight Clusters")

    # Tab 3: Quotes
    ws_quotes = wb.create_sheet(title="Evidence Quotes")
    ws_quotes.append(["Cluster", "Channel", "Author", "Engagement", "Evidence Quote", "Source URL"])
    q_cells = wb_data["sheet_quotes"]["cellData"]
    for r in range(1, 500):
        row_str = str(r)
        if row_str in q_cells:
            ws_quotes.append([
                q_cells[row_str].get("0", {}).get("v", ""),
                q_cells[row_str].get("1", {}).get("v", ""),
                q_cells[row_str].get("2", {}).get("v", ""),
                q_cells[row_str].get("3", {}).get("v", ""),
                q_cells[row_str].get("4", {}).get("v", ""),
                q_cells[row_str].get("5", {}).get("v", "")
            ])
    _style_excel_sheet(ws_quotes, "Evidence Quotes")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"PulseRadar_Research_{session_id[:8]}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/seo/{audit_id}/xlsx", summary="Download native Excel (.xlsx) file for an SEO audit")
async def export_seo_xlsx(audit_id: str, db: AsyncSession = Depends(get_db)):
    """Generates and streams a professional, multi-tab Excel workbook for an SEO audit."""
    if not HAS_OPENPYXL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Excel export engine (openpyxl) is not installed in the environment."
        )
    data = await connect_seo_session(audit_id, db)
    wb_data = data["workbook"]["sheets"]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Tab 1: Executive Scorecard
    ws_sum = wb.create_sheet(title="Executive Scorecard")
    ws_sum.append(["Metric / Dimension", "Score / Value"])
    sum_cells = wb_data["sheet_overview"]["cellData"]
    for r in range(1, 20):
        row_str = str(r)
        if row_str in sum_cells:
            c0 = sum_cells[row_str].get("0", {}).get("v", "")
            c1 = sum_cells[row_str].get("1", {}).get("v", "")
            if c0 or c1:
                ws_sum.append([c0, c1])
    _style_excel_sheet(ws_sum, "Scorecard")

    # Tab 2: GEO Matrix
    ws_geo = wb.create_sheet(title="GEO AI Citation Matrix")
    ws_geo.append(["GEO Pillar", "Score", "Max", "Readiness %", "Signals & Notes"])
    geo_cells = wb_data["sheet_geo"]["cellData"]
    for r in range(1, 20):
        row_str = str(r)
        if row_str in geo_cells:
            ws_geo.append([
                geo_cells[row_str].get("0", {}).get("v", ""),
                geo_cells[row_str].get("1", {}).get("v", ""),
                geo_cells[row_str].get("2", {}).get("v", ""),
                geo_cells[row_str].get("3", {}).get("v", ""),
                geo_cells[row_str].get("4", {}).get("v", "")
            ])
    _style_excel_sheet(ws_geo, "GEO Matrix")

    # Tab 3: Meta Variants
    ws_meta = wb.create_sheet(title="SERP & Title Variants")
    ws_meta.append(["Variant Type", "Suggested Title", "Char Count", "Status", "Rationale"])
    meta_cells = wb_data["sheet_meta"]["cellData"]
    for r in range(1, 20):
        row_str = str(r)
        if row_str in meta_cells:
            ws_meta.append([
                meta_cells[row_str].get("0", {}).get("v", ""),
                meta_cells[row_str].get("1", {}).get("v", ""),
                meta_cells[row_str].get("2", {}).get("v", ""),
                meta_cells[row_str].get("3", {}).get("v", ""),
                meta_cells[row_str].get("4", {}).get("v", "")
            ])
    _style_excel_sheet(ws_meta, "Meta Variants")

    # Tab 4: Keywords
    ws_kw = wb.create_sheet(title="Keywords & Entities")
    ws_kw.append(["Keyword", "Frequency", "Density %", "Intent", "In H1", "In H2", "Prominence"])
    kw_cells = wb_data["sheet_keywords"]["cellData"]
    for r in range(1, 50):
        row_str = str(r)
        if row_str in kw_cells:
            ws_kw.append([
                kw_cells[row_str].get("0", {}).get("v", ""),
                kw_cells[row_str].get("1", {}).get("v", ""),
                kw_cells[row_str].get("2", {}).get("v", ""),
                kw_cells[row_str].get("3", {}).get("v", ""),
                kw_cells[row_str].get("4", {}).get("v", ""),
                kw_cells[row_str].get("5", {}).get("v", ""),
                kw_cells[row_str].get("6", {}).get("v", "")
            ])
    _style_excel_sheet(ws_kw, "Keywords")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"PulseRadar_SEO_{data['domain']}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/{source_type}/{source_id}/pptx", summary="Download native PowerPoint (.pptx) presentation for research or SEO")
async def export_session_pptx(source_type: str, source_id: str, db: AsyncSession = Depends(get_db)):
    """Generates and streams a professional 16:9 widescreen PowerPoint pitch deck."""
    if not HAS_PPTX:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PowerPoint export engine (python-pptx) is not installed in the environment."
        )

    if source_type == "research":
        conn = await connect_research_session(source_id, db)
    elif source_type == "seo":
        conn = await connect_seo_session(source_id, db)
    else:
        raise HTTPException(status_code=400, detail="Invalid source type. Must be 'research' or 'seo'.")

    slides_data = conn.get("slides", {})
    raw_title = conn.get("title", f"Presentation_{source_type}_{source_id[:8]}")
    clean_title = raw_title.replace(" ", "_").replace("/", "_").replace("\\", "_")
    out = generate_pptx_from_slides(slides_data, clean_title)
    filename = f"{clean_title}.pptx"

    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/custom-pptx", summary="Download custom PowerPoint (.pptx) presentation from slide snapshot")
async def export_custom_pptx(payload: ExportCustomPptxPayload):
    """Generates and streams a PowerPoint presentation from user slide edits."""
    if not HAS_PPTX:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PowerPoint export engine (python-pptx) is not installed in the environment."
        )

    clean_title = payload.title.replace(" ", "_").replace("/", "_").replace("\\", "_")
    out = generate_pptx_from_slides(payload.slides, clean_title)
    filename = f"{clean_title}.pptx"

    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --- 4. Saved User Office Documents (Persistence & Real-Time Sync) ---

@router.get("/documents", summary="List all saved office documents")
async def list_documents():
    """Returns all saved office documents with metadata."""
    docs = _load_documents()
    return [
        {
            "id": d["id"],
            "title": d["title"],
            "doc_type": d.get("doc_type", "sheets"),
            "source_type": d.get("source_type"),
            "source_id": d.get("source_id"),
            "summary": d.get("summary", ""),
            "updated_at": d.get("updated_at"),
            "created_at": d.get("created_at")
        }
        for d in docs
    ]


@router.post("/documents", summary="Save or update an office document/workbook")
async def save_document(payload: SaveDocumentPayload):
    """Saves user changes, formula edits, or new documents created in Office Studio."""
    docs = _load_documents()
    now_iso = datetime.now(timezone.utc).isoformat()

    doc_id = payload.id or str(uuid.uuid4())
    existing = next((d for d in docs if d["id"] == doc_id), None)

    if existing:
        existing["title"] = payload.title
        existing["doc_type"] = payload.doc_type
        existing["source_type"] = payload.source_type
        existing["source_id"] = payload.source_id
        existing["snapshot"] = payload.snapshot
        existing["summary"] = payload.summary or existing.get("summary")
        existing["updated_at"] = now_iso
    else:
        new_doc = {
            "id": doc_id,
            "title": payload.title,
            "doc_type": payload.doc_type,
            "source_type": payload.source_type,
            "source_id": payload.source_id,
            "snapshot": payload.snapshot,
            "summary": payload.summary,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        docs.insert(0, new_doc)

    _save_documents(docs)
    return {"status": "saved", "id": doc_id, "updated_at": now_iso}


@router.get("/documents/{doc_id}", summary="Get a saved office document snapshot")
async def get_document(doc_id: str):
    """Retrieve full snapshot of a saved office document."""
    docs = _load_documents()
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{doc_id}", summary="Delete a saved office document")
async def delete_document(doc_id: str):
    """Delete a saved office document."""
    docs = _load_documents()
    updated = [d for d in docs if d["id"] != doc_id]
    if len(updated) == len(docs):
        raise HTTPException(status_code=404, detail="Document not found")
    _save_documents(updated)
    return {"status": "deleted", "id": doc_id}
