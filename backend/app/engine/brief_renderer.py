"""Single-File HTML Brief Renderer (Bento pattern)

Generates a fully self-contained .html brief — no external assets, no JS
dependencies. Charts are inline SVG, styles are inline CSS. The file opens
in any browser, prints cleanly to PDF, and can be attached to emails or
dropped into Notion/slack. One file = the whole report.
"""
import html as html_mod
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

ACCENT = "#9281f7"
GREEN = "#3ad389"
RED = "#ff9592"
YELLOW = "#ffca16"
BG = "#0b0b0d"
CARD = "#141417"
BORDER = "#292d30"
TEXT = "#f0f0f0"
MUTED = "#a1a4a5"

CSS = f"""
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: {BG}; color: {TEXT}; font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
         padding: 40px 24px; line-height: 1.55; }}
  .wrap {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 30px; font-weight: 650; letter-spacing: -0.01em; margin-bottom: 6px; }}
  h2 {{ font-size: 19px; font-weight: 600; margin: 34px 0 14px; padding-bottom: 8px; border-bottom: 1px solid {BORDER}; }}
  h3 {{ font-size: 15px; font-weight: 600; margin: 18px 0 8px; }}
  .meta {{ color: {MUTED}; font-size: 12.5px; font-family: ui-monospace, 'SF Mono', Menlo, monospace; margin-bottom: 28px; }}
  .card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 20px; margin-bottom: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 14px 0; }}
  .kpi {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 16px; }}
  .kpi .num {{ font-size: 26px; font-weight: 700; }}
  .kpi .lbl {{ color: {MUTED}; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.06em; font-family: ui-monospace, monospace; margin-top: 4px; }}
  .quote {{ border-left: 3px solid {ACCENT}; padding: 10px 14px; margin: 10px 0; color: {TEXT}; background: rgba(146,129,247,0.06); border-radius: 0 8px 8px 0; font-size: 13.5px; }}
  .quote .src {{ color: {MUTED}; font-size: 11.5px; margin-top: 5px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0; }}
  th {{ text-align: left; color: {MUTED}; font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.05em;
       padding: 8px 10px; border-bottom: 1px solid {BORDER}; }}
  td {{ padding: 9px 10px; border-bottom: 1px solid rgba(41,45,48,0.6); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .bar-bg {{ background: rgba(41,45,48,0.7); border-radius: 4px; height: 8px; overflow: hidden; }}
  .bar {{ height: 100%; border-radius: 4px; background: {ACCENT}; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 5px; font-size: 10.5px; font-family: ui-monospace, monospace;
            border: 1px solid {BORDER}; color: {MUTED}; margin-right: 6px; }}
  .badge.purple {{ color: {ACCENT}; border-color: rgba(146,129,247,0.4); background: rgba(146,129,247,0.08); }}
  .badge.green {{ color: {GREEN}; border-color: rgba(58,211,137,0.4); background: rgba(58,211,137,0.08); }}
  .badge.red {{ color: {RED}; border-color: rgba(255,149,146,0.4); background: rgba(255,149,146,0.08); }}
  .badge.yellow {{ color: {YELLOW}; border-color: rgba(255,202,22,0.4); background: rgba(255,202,22,0.08); }}
  a {{ color: {ACCENT}; text-decoration: none; }}
  .muted {{ color: {MUTED}; }}
  .sm {{ font-size: 12px; }}
  footer {{ margin-top: 44px; padding-top: 14px; border-top: 1px solid {BORDER}; color: {MUTED}; font-size: 11.5px;
            font-family: ui-monospace, monospace; }}
  @media print {{ body {{ background: #fff; color: #111; }} .card, .kpi {{ border-color: #ddd; background: #fafafa; }} }}
"""


def _esc(text: Any) -> str:
    return html_mod.escape(str(text if text is not None else ""))


def _fmt_num(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n or 0)


def _severity_badge(sev: str) -> str:
    cls = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get((sev or "").upper(), "")
    return f'<span class="badge {cls}">{_esc(sev)}</span>'


def _bar(pct: float, color: str = ACCENT) -> str:
    pct = max(0, min(100, pct))
    return f'<div class="bar-bg"><div class="bar" style="width:{pct}%;background:{color}"></div></div>'


# =====================================================================
# Research brief
# =====================================================================
def render_research_brief(session: Dict[str, Any]) -> str:
    clusters = session.get("clusters", [])
    feedbacks = session.get("feedbacks", [])
    total = session.get("total_items", 0)

    # Category distribution chart data
    cat_counts: Dict[str, int] = {}
    for c in clusters:
        cat_counts[c.get("category", "OTHER")] = cat_counts.get(c.get("category", "OTHER"), 0) + (c.get("item_count") or 0)
    max_cat = max(cat_counts.values()) if cat_counts else 1

    cluster_rows = []
    for c in clusters[:10]:
        quotes_html = ""
        for q in (c.get("quotes") or [])[:2]:
            src = q.get("source_author") or "User"
            perm = q.get("permalink") or "#"
            quotes_html += (
                f'<div class="quote">&ldquo;{_esc(q.get("quote_text", ""))[:280]}&rdquo;'
                f'<div class="src">&mdash; <a href="{_esc(perm)}">{_esc(src)}</a> '
                f'<span class="muted">({_esc(q.get("source_channel", ""))}, {_fmt_num(q.get("engagement_score"))} engagement)</span></div></div>'
            )
        sev_pct = round((c.get("severity_score") or 0) * 100)
        cluster_rows.append(f"""
      <div class="card">
        <h3>{_esc(c.get('title'))}</h3>
        <div style="margin:6px 0 10px">
          <span class="badge purple">{_esc(c.get('category', '').replace('_', ' '))}</span>
          <span class="badge">{c.get('item_count', 0)} signals</span>
          <span class="badge">severity {c.get('severity_score', 0)}</span>
        </div>
        <p class="sm muted">{_esc(c.get('description', ''))}</p>
        {quotes_html}
        <div style="margin-top:10px">{_bar(sev_pct, RED if sev_pct >= 75 else (YELLOW if sev_pct >= 55 else GREEN))}</div>
      </div>""")

    cat_bars = "".join(
        f"""<div style="margin:8px 0"><div class="sm" style="display:flex;justify-content:space-between">
            <span>{_esc(k.replace('_', ' ').title())}</span><span class="muted">{v}</span></div>
            {_bar(100 * v / max_cat)}</div>"""
        for k, v in sorted(cat_counts.items(), key=lambda kv: -kv[1])
    )

    markdown_summary = session.get("summary") or ""
    summary_html = "".join(
        f"<p>{_esc(line.lstrip('# ').strip())}</p>"
        for line in markdown_summary.splitlines() if line.strip() and not line.strip().startswith(("#", "**", "-"))
    ) or f"<p>{_esc(markdown_summary[:600])}</p>"

    # P3: optional auto-generated SVG diagram (embedded inline)
    diagram_svg = session.get("diagram_svg")
    diagram_block = (
        f'<h2>Auto-Generated Diagram</h2><div class="card" style="text-align:center">{diagram_svg}</div>'
        if diagram_svg else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PulseRadar Brief — {_esc(session.get('query', 'Research'))}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <h1>{_esc(session.get('query', 'Research Brief'))}</h1>
  <div class="meta">PulseRadar Research Brief &bull; {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} &bull; channels: {_esc(', '.join(session.get('channels', [])))}</div>

  <div class="grid">
    <div class="kpi"><div class="num">{_fmt_num(total)}</div><div class="lbl">Signals analyzed</div></div>
    <div class="kpi"><div class="num">{len(clusters)}</div><div class="lbl">Insight clusters</div></div>
    <div class="kpi"><div class="num">{len(feedbacks)}</div><div class="lbl">Source documents</div></div>
    <div class="kpi"><div class="num">{len(set(f.get('channel', '') for f in feedbacks))}</div><div class="lbl">Platforms covered</div></div>
  </div>

  <h2>Executive Summary</h2>
  <div class="card">{summary_html}</div>

  {diagram_block}

  <h2>Signal Composition</h2>
  <div class="card">{cat_bars or '<span class="muted">No clusters.</span>'}</div>

  <h2>Insight Clusters (ranked by severity)</h2>
  {''.join(cluster_rows) or '<p class="muted">No clusters available.</p>'}

  <h2>Top Source Signals</h2>
  <table>
    <tr><th>Source</th><th>Title</th><th>Engagement</th></tr>
    {''.join(
        f"<tr><td class='sm'>{_esc(f.get('channel', ''))}</td><td class='sm'><a href='{_esc(f.get('url', '#'))}'>{_esc((f.get('title') or 'Untitled')[:90])}</a></td><td class='sm'>{_fmt_num(f.get('engagement'))}</td></tr>"
        for f in sorted(feedbacks, key=lambda x: -(x.get('engagement') or 0))[:12]
    )}
  </table>

  <footer>Generated by PulseRadar &mdash; single-file brief (self-contained HTML, prints to PDF)</footer>
</div>
</body>
</html>"""


# =====================================================================
# SEO brief
# =====================================================================
def render_seo_brief(audit: Dict[str, Any]) -> str:
    results = audit.get("results", {}) or {}
    scores = {
        "Overall": audit.get("overall_score", 0),
        "Technical": audit.get("technical_score", 0),
        "GEO (AI Citation)": audit.get("geo_readiness_score", 0),
        "On-Page": audit.get("onpage_score", 0),
        "Images": audit.get("image_score", 0),
        "Link Integrity": (results.get("scores", {}) or {}).get("link_integrity", None),
        "Sitemap": (results.get("scores", {}) or {}).get("sitemap", None),
        "International": (results.get("scores", {}) or {}).get("international", None),
    }

    kpis = "".join(
        f"""<div class="kpi"><div class="num" style="color:{GREEN if v is not None and v >= 80 else (YELLOW if v is not None and v >= 55 else RED)}">{v if v is not None else '—'}</div><div class="lbl">{_esc(k)}</div></div>"""
        for k, v in scores.items() if v is not None
    )

    geo = results.get("geo", {})
    pillars = geo.get("pillars", {}) or {}
    pillar_rows = "".join(
        f"""<div style="margin:10px 0"><div class="sm" style="display:flex;justify-content:space-between">
          <span>{_esc(p.replace('_', ' ').title())}</span><span class="muted">{d.get('percentage', 0)}%</span></div>
          {_bar(d.get('percentage', 0))}</div>"""
        for p, d in pillars.items()
    )

    tech_issues = (results.get("technical", {}) or {}).get("issues", [])
    link_issues = (results.get("link_integrity", {}) or {}).get("issues", [])
    sitemap_issues = (results.get("sitemap", {}) or {}).get("issues", [])
    intl_issues = (results.get("international", {}) or {}).get("issues", [])
    all_issues = tech_issues + link_issues + sitemap_issues + intl_issues

    issue_rows = "".join(
        f"<tr><td>{_severity_badge(i.get('severity'))}</td><td class='sm'>{_esc(i.get('field', ''))}</td><td class='sm'>{_esc(i.get('message', ''))}</td></tr>"
        for i in all_issues[:25]
    ) or "<tr><td colspan='3' class='muted'>No issues flagged.</td></tr>"

    plan = results.get("content_plan", {}) or {}
    plan_rows = "".join(
        f"<tr><td class='sm'>{_esc(t.get('publish_date', 'TBD'))}</td><td class='sm'>{_esc(t.get('title'))}</td>"
        f"<td><span class='badge purple'>{_esc(t.get('type', '').replace('_', ' '))}</span></td>"
        f"<td class='sm muted'>{_esc(t.get('target_keyword', ''))}</td></tr>"
        for t in plan.get("calendar", [])[:12]
    ) or "<tr><td colspan='4' class='muted'>No content plan generated.</td></tr>"

    summary_html = "".join(
        f"<p>{_esc(line.lstrip('* ').strip())}</p>"
        for line in (audit.get("executive_summary") or "").splitlines() if line.strip() and line.strip().startswith(("-", "**"))
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PulseRadar SEO Brief — {_esc(audit.get('url', ''))}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <h1>SEO &amp; GEO Audit: {_esc(audit.get('domain') or audit.get('url', ''))}</h1>
  <div class="meta">{_esc(audit.get('url', ''))} &bull; {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} &bull; audit type: {_esc(audit.get('audit_type', 'quick'))}</div>

  <div class="grid">{kpis}</div>

  <h2>Executive Summary</h2>
  <div class="card">{summary_html or '<span class="muted">No summary.</span>'}</div>

  <h2>GEO Citation Pillars</h2>
  <div class="card">{pillar_rows or '<span class="muted">No GEO data.</span>'}</div>

  <h2>Issues &amp; Recommendations ({len(all_issues)})</h2>
  <table><tr><th>Severity</th><th>Area</th><th>Detail</th></tr>{issue_rows}</table>

  <h2>Editorial Content Plan</h2>
  <table><tr><th>Date</th><th>Title</th><th>Type</th><th>Target keyword</th></tr>{plan_rows}</table>

  <footer>Generated by PulseRadar SEO &amp; GEO Studio &mdash; single-file brief (self-contained HTML, prints to PDF)</footer>
</div>
</body>
</html>"""


def render_brief_html(source_type: str, payload: Dict[str, Any]) -> str:
    if source_type == "seo":
        return render_seo_brief(payload)
    return render_research_brief(payload)
