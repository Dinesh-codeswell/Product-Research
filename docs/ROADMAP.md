# PulseRadar — Multi-Stage Engineering Roadmap

> **Roadmap Horizon:** 8 Weeks (MVP to Production Open-Source Release)  
> **Development Cadence:** 2-Week Sprints  
> **Core Principle:** Every sprint ends in a functional, shippable milestone.

---

## Roadmap Overview Visual

```mermaid
gantt
    title PulseRadar Engineering Roadmap
    dateFormat  YYYY-MM-DD
    section Sprint 1: MVP Core Pipeline
    Project Scaffolding & Setup          :s1_1, 2026-10-01, 3d
    Reddit & YouTube Scrapers            :s1_2, after s1_1, 5d
    Embedding & Semantic Clustering      :s1_3, after s1_2, 4d
    FastAPI Core Endpoints & SSE         :s1_4, after s1_3, 4d
    
    section Sprint 2: Frontend & MVP Release
    Next.js 15 App Router Scaffolding    :s2_1, 2026-10-15, 3d
    Live SSE Stream & Stepper UI         :s2_2, after s2_1, 4d
    Cluster Matrix & Evidence Drawer     :s2_3, after s2_2, 4d
    Markdown & JSON Export Studio        :s2_4, after s2_3, 3d
    
    section Sprint 3: PRD & Spec Studio
    Anthropic PM Prompt Synthesis        :s3_1, 2026-10-29, 4d
    Interactive PRD Generator UI         :s3_2, after s3_1, 4d
    Opportunity Solution Tree Visuals    :s3_3, after s3_2, 3d
    Session History & Search             :s3_4, after s3_3, 3d
    
    section Sprint 4: Fleet & Integrations
    Hacker News & Twitter Connectors     :s4_1, 2026-11-12, 4d
    Scheduled Background Monitoring      :s4_2, after s4_1, 4d
    Docker Compose & One-Click Deploy    :s4_3, after s4_2, 3d
    Launch & Community Documentation     :s4_4, after s4_3, 3d
```

---

## Detailed Sprint Milestones

### Sprint 1: MVP Core Pipeline (Weeks 1–2)
*Goal: Working Python backend capable of searching Reddit, transcribing YouTube, embedding items, and outputting clustered themes to SQLite.*
- [ ] Initialize Python backend with `FastAPI`, `Pydantic v2`, and `AsyncIO`.
- [ ] Build `RedditAdapter` utilizing search endpoints with backoff and User-Agent rotation.
- [ ] Build `YouTubeAdapter` integrating `youtube-transcript-api` with timestamp segmentation.
- [ ] Implement text cleaner (boilerplate stripper, noise filter, deduplication via SHA-256).
- [ ] Implement vector embedding service (local `sentence-transformers` + cloud fallback).
- [ ] Implement clustering algorithm (cosine distance + centroid labeling).
- [ ] Build SQLite persistence layer with SQLAlchemy models.
- [ ] Expose REST endpoints + SSE event stream (`/api/v1/research/start`, `/events`).

### Sprint 2: Frontend & MVP Shipped (Weeks 3–4)
*Goal: Complete, usable web application where a user can enter a query, watch the live ingestion, explore clusters, and export markdown.*
- [ ] Scaffold Next.js 15 App Router frontend with TypeScript and Tailwind CSS.
- [ ] Build Query Launchpad with presets and channel toggles.
- [ ] Build real-time SSE listener and animated progress stepper.
- [ ] Build Cluster Matrix component displaying Pain Points, Workarounds, and Desires.
- [ ] Build Slide-Over Evidence Drawer displaying verbatim quotes with clickable permalinks.
- [ ] Build Export Modal supporting one-click Markdown and JSON downloads.
- [ ] End-to-end integration tests between Next.js and FastAPI.

### Sprint 3: Autonomous PRD & Spec Studio (Weeks 5–6)
*Goal: Transform verified clusters into production-ready product specs with zero manual typing.*
- [ ] Integrate prompt engineering frameworks from Anthropic Product Management skills.
- [ ] Implement `PRDGenerator` generating Problem Statements, Goals, User Stories, and Acceptance Criteria.
- [ ] Build PRD Studio UI with split markdown preview, live editing, and section regeneration.
- [ ] Add Opportunity Solution Tree interactive visualization.
- [ ] Add local session history drawer to resume or re-run past research queries.

### Sprint 4: Advanced Connectors & Production Release (Weeks 7–8)
*Goal: Community-ready open-source package with containerization, scheduled alerts, and multiple channels.*
- [ ] Implement Hacker News Algolia API adapter.
- [ ] Implement Twitter/X discussion scraper with anti-bot handling.
- [ ] Add scheduled background monitoring (daily/weekly automated query sweeps).
- [ ] Add webhook integration (Slack/Discord alerts on sentiment shifts).
- [ ] Create multi-container `docker-compose.yml` for zero-friction local deployment.
- [ ] Write contributor guides, video walkthrough, and publish initial v1.0.0 release.
