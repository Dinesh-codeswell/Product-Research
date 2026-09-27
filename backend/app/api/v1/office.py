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

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

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
    doc_type: str = "sheets"  # "sheets" or "docs"
    source_type: Optional[str] = None  # "research", "seo", "browser", or None
    source_id: Optional[str] = None
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None


class ExportCustomXlsxPayload(BaseModel):
    title: str = "Office_Export"
    sheets: Dict[str, List[List[Any]]] = Field(default_factory=dict)


# --- 1. Available Data Sources ---

@router.get("/sources", summary="List connectable sessions from Research and SEO")
async def list_available_sources(db: AsyncSession = Depends(get_db)):
    """Return recent completed research sessions and SEO audits that can be loaded into Office Studio."""
    # Fetch recent Research sessions
    stmt_research = (
        select(ResearchSession)
        .order_by(desc(ResearchSession.created_at))
        .limit(20)
    )
    res_research = await db.execute(stmt_research)
    research_sessions = res_research.scalars().all()

    # Fetch recent SEO audits
    stmt_seo = (
        select(SeoAuditSession)
        .order_by(desc(SeoAuditSession.created_at))
        .limit(20)
    )
    res_seo = await db.execute(stmt_seo)
    seo_sessions = res_seo.scalars().all()

    return {
        "research": [
            {
                "id": s.id,
                "title": s.query,
                "type": "research",
                "status": s.status,
                "items_count": s.total_items_scraped,
                "execution_mode": s.execution_mode,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in research_sessions
        ],
        "seo": [
            {
                "id": s.id,
                "title": f"{s.domain} ({s.audit_type})",
                "url": s.url,
                "type": "seo",
                "status": s.status,
                "overall_score": s.overall_score,
                "geo_score": s.geo_readiness_score,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in seo_sessions
        ]
    }


# --- 2. Live Data Connectors (Univer-Compatible Workbook & Doc Snapshots) ---

@router.get("/connect/research/{session_id}", summary="Get research session pre-formatted for Univer Sheets and Docs")
async def connect_research_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Transforms a Consumer Discovery research session into structured Univer Workbook and Document data."""
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
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
            "0": {"v": "PULSERADAR CONSUMER RESEARCH DOSSIER", "s": {"b": 1, "fs": 14, "cl": {"rgb": "#9281F7"}}},
        },
        "1": {
            "0": {"v": "Research Query:", "s": {"b": 1}},
            "1": {"v": session.query}
        },
        "2": {
            "0": {"v": "Execution Mode:", "s": {"b": 1}},
            "1": {"v": session.execution_mode.upper()}
        },
        "3": {
            "0": {"v": "Total Items Analyzed:", "s": {"b": 1}},
            "1": {"v": session.total_items_scraped}
        },
        "4": {
            "0": {"v": "Insight Clusters Identified:", "s": {"b": 1}},
            "1": {"v": len(session.clusters)}
        },
        "5": {
            "0": {"v": "Analysis Status:", "s": {"b": 1}},
            "1": {"v": session.status}
        },
        "7": {
            "0": {"v": "EXECUTIVE SYNTHESIS", "s": {"b": 1, "fs": 12, "cl": {"rgb": "#3AD389"}}}
        },
        "8": {
            "0": {"v": session.executive_summary or "Inference and aggregation in progress."}
        }
    }

    # Sheet 2: Insight Clusters
    cluster_cells = {
        "0": {
            "0": {"v": "Cluster Title", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "1": {"v": "Category", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "2": {"v": "Severity (0-1)", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "3": {"v": "Evidence Count", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "4": {"v": "Keyword Tags", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "5": {"v": "Description & Opportunity", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
        }
    }
    for idx, c in enumerate(clusters_data, start=1):
        cluster_cells[str(idx)] = {
            "0": {"v": c["title"], "s": {"b": 1}},
            "1": {"v": c["category"]},
            "2": {"v": round(c["severity_score"], 2)},
            "3": {"v": c["item_count"]},
            "4": {"v": ", ".join(c["keyword_tags"]) if c["keyword_tags"] else "None"},
            "5": {"v": c["description"]},
        }

    # Sheet 3: Evidence Quotes
    quotes_cells = {
        "0": {
            "0": {"v": "Cluster", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "1": {"v": "Channel", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "2": {"v": "Author", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "3": {"v": "Engagement", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "4": {"v": "Direct Evidence Quote", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "5": {"v": "Source URL", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
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
    workbook_snapshot = {
        "id": f"wb_research_{session.id}",
        "name": f"Research: {session.query[:32]}",
        "sheetOrder": ["sheet_summary", "sheet_clusters", "sheet_quotes"],
        "sheets": {
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

    return {
        "session_id": session.id,
        "query": session.query,
        "title": f"Research - {session.query}",
        "workbook": workbook_snapshot,
        "document_markdown": doc_markdown,
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
            "0": {"v": "PULSERADAR SEO & GEO CITATION AUDIT", "s": {"b": 1, "fs": 14, "cl": {"rgb": "#9281F7"}}},
        },
        "1": {"0": {"v": "Audited Domain:", "s": {"b": 1}}, "1": {"v": session.domain}},
        "2": {"0": {"v": "Full Target URL:", "s": {"b": 1}}, "1": {"v": session.url}},
        "3": {"0": {"v": "Audit Type:", "s": {"b": 1}}, "1": {"v": session.audit_type.upper()}},
        "4": {"0": {"v": "Audit Status:", "s": {"b": 1}}, "1": {"v": session.status}},
        "6": {"0": {"v": "EXECUTIVE COMPOSITE SCORES", "s": {"b": 1, "fs": 12, "cl": {"rgb": "#3AD389"}}}},
        "7": {"0": {"v": "Overall Health Score (0-100)", "s": {"b": 1}}, "1": {"v": session.overall_score}},
        "8": {"0": {"v": "GEO AI Citation Readiness Score (0-100)", "s": {"b": 1}}, "1": {"v": session.geo_readiness_score}},
        "9": {"0": {"v": "Technical SEO Crawl Score", "s": {"b": 1}}, "1": {"v": session.technical_score}},
        "10": {"0": {"v": "On-Page & Schema Score", "s": {"b": 1}}, "1": {"v": session.onpage_score}},
        "11": {"0": {"v": "Image SEO Optimization Score", "s": {"b": 1}}, "1": {"v": session.image_score}},
        "13": {"0": {"v": "EXECUTIVE DOSSIER SUMMARY", "s": {"b": 1, "fs": 11}}},
        "14": {"0": {"v": session.executive_summary or "Audit complete."}}
    }

    # Sheet 2: GEO AI Citation Matrix (Perplexity, ChatGPT, Gemini)
    geo_pillars = geo.get("pillars") or {}
    geo_cells = {
        "0": {
            "0": {"v": "GEO Pillar", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "1": {"v": "Score", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "2": {"v": "Max", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "3": {"v": "Readiness %", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "4": {"v": "Key Signal Evaluation Notes", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
        }
    }
    r_idx = 1
    for p_name, p_data in geo_pillars.items():
        notes = []
        for itm in p_data.get("items", []):
            notes.append(f"{itm.get('rule')}: {itm.get('status')} ({itm.get('notes', '')})")
        geo_cells[str(r_idx)] = {
            "0": {"v": p_name.replace("_", " ").upper(), "s": {"b": 1}},
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
            "0": {"v": "Variant Type", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "1": {"v": "Suggested Title Tag", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "2": {"v": "Char Count", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "3": {"v": "Status", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "4": {"v": "CTR & Search Rationale", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
        }
    }
    for idx, tv in enumerate(title_variants, start=1):
        meta_cells[str(idx)] = {
            "0": {"v": tv.get("variant", ""), "s": {"b": 1}},
            "1": {"v": tv.get("title", "")},
            "2": {"v": tv.get("char_count", 0)},
            "3": {"v": tv.get("status", "OPTIMAL")},
            "4": {"v": tv.get("description", "")},
        }

    # Sheet 4: Top Keywords & Content Density
    top_kws = keywords.get("top_keywords") or []
    kw_cells = {
        "0": {
            "0": {"v": "Keyword / Entity", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "1": {"v": "Frequency", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "2": {"v": "Density %", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "3": {"v": "Search Intent", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "4": {"v": "In H1", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "5": {"v": "In H2", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
            "6": {"v": "Prominence", "s": {"b": 1, "bg": {"rgb": "#1E2029"}, "cl": {"rgb": "#FFFFFF"}}},
        }
    }
    for idx, k in enumerate(top_kws[:30], start=1):
        kw_cells[str(idx)] = {
            "0": {"v": k.get("keyword", ""), "s": {"b": 1}},
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

    return {
        "audit_id": session.id,
        "domain": session.domain,
        "url": session.url,
        "title": f"SEO - {session.domain}",
        "workbook": workbook_snapshot,
        "document_markdown": doc_markdown,
        "scores": {
            "overall": session.overall_score,
            "geo": session.geo_readiness_score,
            "technical": session.technical_score,
            "onpage": session.onpage_score,
            "image": session.image_score
        }
    }


# --- 3. Native Excel (.xlsx) Streaming Endpoints ---

def _style_excel_sheet(ws, title: str):
    """Apply Resend-style clean dark/corporate aesthetics to openpyxl worksheets."""
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
