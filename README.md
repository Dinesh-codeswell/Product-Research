<div align="center">

# 📡 PulseRadar
### Autonomous Multi-Channel Product Research & Synthesis Studio
**Turn unstructured customer chatter across Reddit & YouTube into verified, evidence-backed product specs.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-green.svg)](https://www.python.org/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/Status-Implementation--Ready-orange.svg)]()

[Product Vision (PRD)](./docs/PRD.md) · [System Architecture](./docs/ARCHITECTURE.md) · [UI/UX Design](./docs/DESIGN.md) · [Feature Specs](./docs/FEATURE_SPEC.md) · [Roadmap](./docs/ROADMAP.md)

---
</div>

## 💡 What is PulseRadar?

Product Managers, Founders, and Engineers waste dozens of hours every week manually skimming forum threads, Reddit rants, and YouTube reviews to understand user pain points, feature requests, and competitor shortcomings.

**PulseRadar** is an autonomous, open-source product discovery engine that:
1. **Sweeps the Web & Walled Gardens:** Ingests unvarnished discussions across **Reddit**, **YouTube video transcripts**, and tech communities.
2. **Eliminates Noise & Clusters Semantically:** Cleans bot boilerplate, vectorizes feedback, and groups discussions into categorized themes (🔴 Pain Points, 🟡 Workarounds, 🟢 Desires, 🔵 Churn Triggers).
3. **Provides 100% Grounded Evidence:** Every synthesized insight is directly attached to verbatim quotes with clickable permalinks to original discussions.
4. **Auto-Generates Production PRDs:** Synthesizes verified user signals into structured Product Requirements Documents with user stories and acceptance criteria.

---

## 🏛️ System Architecture

```mermaid
graph LR
    subgraph Data Ingestion
        R[Reddit Adapter]
        Y[YouTube Transcripts]
        H[Hacker News]
    end

    subgraph Processing & AI Engine
        C[Text Normalizer & Dedup]
        E[Vector Embeddings]
        K[Semantic Clustering]
        S[Anthropic PM Prompt Synthesis]
    end

    subgraph UI & Experience
        W[Next.js 15 Dashboard]
        M[Cluster Matrix & Quote Drawer]
        P[PRD & Spec Studio]
    end

    R & Y & H --> C --> E --> K --> S
    S --> W --> M & P
```

---

## 🚀 Key Features

*   **Multi-Channel Ingestion:** Automated search across subreddits and YouTube video transcripts with anti-bot resilience.
*   **Semantic Theme Clustering:** Unsupervised grouping of feedback items into high-level thematic clusters (e.g. *"Connection Pool Exhaustion on Serverless"*).
*   **Zero-Hallucination Grounding:** Real user quotes with author metadata, upvotes/views, and direct URLs.
*   **Interactive PRD & Spec Studio:** Instant generation of PRDs, user stories (Given-When-Then), and opportunity solution trees.
*   **Local-First & Exportable:** Self-contained architecture with SQLite storage, ready to export as an independent open-source repository.

---

## 🎬 YouTube Transcript Intelligence (Zero-Auth)

Every YouTube signal surfaced by PulseRadar — whether discovered by the headless browser agent, the
channel sweeper, or an on-demand lookup — carries a **real, timestamped transcript** instead of a bare URL.

| Capability | Endpoint | Notes |
| --- | --- | --- |
| Full transcript + cues | `POST /api/v1/youtube/transcript` | `{ url_or_id, languages?, force_whisper?, whisper_key? }` |
| Transcript by ID/permalink | `GET /api/v1/youtube/transcript/{video_id}` | Supports `&t=` deep links and `?languages=en,hi` |
| Grounded signal chunks | `POST /api/v1/youtube/signals` | 35–75 word paragraphs, each with a `&t=NNs` permalink |
| Whisper ASR fallback | `POST /api/v1/youtube/transcribe` | Downloads lightweight audio via `yt-dlp`, then Groq/OpenAI Whisper |
| ASR readiness probe | `GET /api/v1/youtube/whisper-status` | Reports whether a backend Groq/OpenAI key exists |
| Fast metadata | `GET /api/v1/youtube/info/{video_id}` | Title, channel, duration, chapters, thumbnail |

**Resilient 4-tier extraction chain** (never hard-fails, always returns a structured payload):

1. `youtube-transcript-api` with realistic browser headers, language priority and translation fallback.
2. Benchmark/known-video resilient fallback snippets.
3. Automatic Whisper ASR transcription (Groq `whisper-large-v3`, then OpenAI) when a key is configured.
4. Video chapters and description timestamps (`01:23 Topic`) — so citations still resolve to a moment.

Results are cached in `backend/data/transcripts_cache.sqlite3`, persisted as `raw_feedbacks` rows with
`has_transcript`, `start_seconds`, `timestamp` and `stats` metadata, and exported into the Office Studio
workbook (`YouTube Video Transcripts` sheet) plus PPTX/Markdown deliverables.

In the UI, the **Transcript** button on any YouTube signal opens an in-site player with synchronized
dialogue cues: clicking a cue seeks the embedded player to that exact second, and the transcript can be
copied, exported as `.md`/`.srt`, or piped straight into an AI agent as a ready-made prompt.

> **Optional:** Audio transcription requires a key. Groq offers a free tier — add `GROQ_API_KEY="gsk_..."`
> to `.env` and captions-disabled videos get transcribed automatically. Without a key, PulseRadar still
> returns subtitles, chapters and description timestamps.

---

## 📂 Repository Structure

```
PulseRadar/
├── backend/                      # Python FastAPI backend
│   ├── app/                      # Core application source
│   │   ├── api/v1/               # REST & SSE endpoints
│   │   ├── channels/             # Scraper adapters (Reddit, YouTube)
│   │   ├── engine/               # Text cleaning, embeddings, clustering, LLM
│   │   ├── models/               # Schemas & SQLAlchemy models
│   │   └── main.py               # FastAPI entrypoint
│   └── requirements.txt          # Backend dependencies
├── frontend/                     # Next.js 15 App Router frontend
│   ├── app/                      # Pages & layouts
│   ├── components/               # React UI & cluster components
│   └── package.json              # Frontend dependencies
├── docs/                         # Comprehensive engineering documentation
│   ├── PRD.md                    # Product Requirements Document
│   ├── ARCHITECTURE.md           # System Architecture & Technical Specifications
│   ├── DESIGN.md                 # UI/UX Specifications & Wireframes
│   ├── FEATURE_SPEC.md           # Feature Listing & Acceptance Criteria
│   └── ROADMAP.md                # Multi-stage engineering roadmap
├── docker-compose.yml            # Multi-container orchestration
├── .env.example                  # Environment configuration template
├── .gitignore                    # Clean Git exclusions
└── LICENSE                       # MIT License
```

---

## 🛠️ Quick Start (Local Setup)

### Prerequisites
*   Python 3.11+
*   Node.js 20+ & pnpm / npm
*   (Optional) Docker & Docker Compose

### 1. Clone & Configure
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📑 Detailed Specifications

Explore the planning and architecture documentation:
*   📖 [Product Requirements Document (PRD)](./docs/PRD.md): Vision, user personas, functional & non-functional requirements.
*   🏛️ [System Architecture](./docs/ARCHITECTURE.md): Data pipeline, scraper adapters, vector storage, and API contracts.
*   🎨 [UI/UX Design Specifications](./docs/DESIGN.md): Visual design tokens, screen layouts, and wireframes.
*   📋 [Feature Specifications](./docs/FEATURE_SPEC.md): User stories and Gherkin acceptance criteria.
*   🗺️ [Engineering Roadmap](./docs/ROADMAP.md): 8-week phased milestone plan from MVP to production release.

---

## 📄 License
This project is open-source under the [MIT License](./LICENSE).
