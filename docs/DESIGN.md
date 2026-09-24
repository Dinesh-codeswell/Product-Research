# PulseRadar — UI/UX Design System & Wireframe Specifications

> **Design System Version:** 1.0.0  
> **Aesthetic Philosophy:** Precision Data Density, Developer-First Minimalism, High Contrast (Linear & Vercel Aesthetic)  
> **Primary Theme:** Modern Dark Mode Default with High-Legibility Light Mode Support

---

## 1. Design Principles & Aesthetic Identity

1. **Zero Fluff, Maximum Signal:** Avoid decorative animations that delay data consumption. Every pixel must serve the synthesis of product intelligence.
2. **Transparent Grounding:** Never show a synthesized claim without an immediate visual link to its underlying verbatim quote and permalink.
3. **Real-Time Responsiveness:** Ingestion takes 20–40 seconds; the UI must communicate live progress, current channels being crawled, and item counts via micro-steppers to keep users engaged.
4. **Keyboard-First Navigation:** Support shortcuts (`Cmd+K` for search, `Esc` to close drawers, `J/K` to traverse insight clusters).

---

## 2. Color Palette & Typography

### 2.1 Color Tokens (Tailwind CSS Mappings)

```css
/* Backgrounds & Surfaces */
--bg-base:        #090A0F; /* Deep void background */
--bg-surface:     #12141C; /* Card & container background */
--bg-surface-elevated: #1B1E2B; /* Popovers, tooltips, modals */
--border-subtle:  #25293A; /* Structural dividers */
--border-focus:   #3B82F6; /* Interactive highlight */

/* Brand & Accent Tokens */
--radar-cyan:     #06B6D4; /* Primary brand & pulse indicator */
--radar-cyan-glow: rgba(6, 182, 212, 0.15);
--radar-blue:     #3B82F6; /* Primary actions */

/* Semantic Category Indicators */
--cat-pain:       #EF4444; /* Red - Friction & Frustrations */
--cat-workaround: #F59E0B; /* Amber - Hacks & Workarounds */
--cat-desire:     #10B981; /* Emerald - Feature Requests */
--cat-churn:      #8B5CF6; /* Purple - Churn & Competitor Migrations */

/* Typography */
--text-primary:   #F8FAFC;
--text-secondary: #94A3B8;
--text-muted:     #64748B;
```

### 2.2 Typography Hierarchy
*   **Headings:** `Geist Sans` or `Inter`, font weights 600–700, tight tracking (`-0.02em`).
*   **Body & Descriptions:** `Inter`, font weight 400–500, line height 1.6 for comfortable reading.
*   **Code, Metadata & Citations:** `Geist Mono` or `JetBrains Mono`, font weight 400–500, size 12px–13px.

---

## 3. Information Architecture & Site Map

```
PulseRadar Web App
├── Top Navigation (Logo, Active Query, New Research CTA, Docs, GitHub Star)
├── Main Views:
│   ├── [View A] Research Launchpad (Root '/')
│   │   ├── Query Input Hero with Autocomplete & Presets
│   │   ├── Channel Selector Toggles (Reddit, YouTube, HN, Twitter)
│   │   └── Recent Research History Drawer
│   ├── [View B] Live Ingestion Stream ('/research/[id]')
│   │   ├── Real-Time Progress Stepper (SSE)
│   │   ├── Live Scraped Items Feed
│   │   └── Real-time Channel Status Badges
│   ├── [View C] Cluster Radar & Insights ('/research/[id]/insights')
│   │   ├── Top-line Metrics Bar (Total items, Sentiment breakdown, Top themes)
│   │   ├── Category Filter Pills (All, Pain Points, Workarounds, Desires)
│   │   ├── Interactive Cluster Cards Grid
│   │   └── Slide-Over Quote Evidence Drawer
│   └── [View D] PRD & Spec Studio ('/research/[id]/prd')
│       ├── Split View: Structured Spec Preview vs Raw Markdown
│       ├── Opportunity Solution Tree View
│       └── Export Toolbar (Copy, Download .md, Push to Notion/GitHub)
```

---

## 4. Key Screen Wireframe Layouts

### 4.1 Screen 1: Research Launchpad (`/`)

```
+-------------------------------------------------------------------------------+
|  (•) PulseRadar      [Docs]  [GitHub ★]                       [+ New Research]|
+-------------------------------------------------------------------------------+
|                                                                               |
|                   Autonomous Product Research Studio                          |
|         Turn raw customer chatter across Reddit & YouTube into                |
|               verified, evidence-backed product specs.                        |
|                                                                               |
|   +-----------------------------------------------------------------------+   |
|   |  🔍  e.g., "Why are developers ditching Create React App?"           |   |
|   +-----------------------------------------------------------------------+   |
|                                                                               |
|   Channels to Sweep:                                                          |
|   [✓] Reddit (r/webdev, r/reactjs)   [✓] YouTube Transcripts   [ ] HackerNews |
|                                                                               |
|   Preset Templates to Try:                                                    |
|   [ Datadog vs Signoz Complaints ]  [ Supabase Missing Features ]  [ Linear UX]|
|                                                                               |
|   Recent Research Sessions:                                                   |
|   • "Prisma ORM performance issues" — 82 items scraped • 3 days ago          |
|   • "Figma AI features feedback" — 124 items scraped • 1 week ago             |
+-------------------------------------------------------------------------------+
```

---

### 4.2 Screen 2: Real-Time Ingestion & Event Stream (`/research/:id`)

```
+-------------------------------------------------------------------------------+
|  (•) PulseRadar   >   "Supabase Migration Triggers"           [Status: Running]|
+-------------------------------------------------------------------------------+
|                                                                               |
|   [============================== 65% ==============================        ] |
|   Phase: Semantic Clustering (HDBSCAN) • 74 feedback items analyzed           |
|                                                                               |
|   Channel Telemetry:                                                          |
|   • Reddit Adapter:   ✓ Completed (48 threads ingested across r/supabase)     |
|   • YouTube Adapter:  ✓ Completed (4 video transcripts parsed, 26 quotes)    |
|   • Vector Embedder:  ✓ 74/74 items vectorized (sentence-transformers)        |
|   • LLM Synthesizer:  ⟳ Grouping into 4 distinct thematic clusters...         |
|                                                                               |
|   Live Stream Ingestion Log:                                                  |
|   [10:42:01] Fetched: "Why we moved from Supabase back to plain Postgres"     |
|   [10:42:04] Transcribed: "Supabase vs Firebase in 2026: The Honest Truth"   |
|   [10:42:08] Deduped: Removed 12 duplicate cross-posts                        |
|                                                                               |
+-------------------------------------------------------------------------------+
```

---

### 4.3 Screen 3: Cluster Radar & Evidence Drawer (`/research/:id/insights`)

```
+---------------------------------------------------------------------------------------------------------+
| (•) PulseRadar > Supabase Feedback   [Overview]  [Clusters (4)]  [PRD Studio]      [⬇ Export Report]   |
+---------------------------------------------------------------------------------------------------------+
| TOTAL ITEMS: 74  |  🔴 PAIN POINTS: 38%  |  🟡 WORKAROUNDS: 22%  |  🟢 DESIRES: 40%  | CONFIDENCE: 94%   |
+---------------------------------------------------------------------------------------------------------+
| Filter: [ All ]  [ 🔴 Pain Points ]  [ 🟡 Workarounds ]  [ 🟢 Desires ]  [ 🔵 Churn Triggers ]          |
|                                                                                                         |
| +------------------------------------+ +------------------------------------+ +-----------------------+ |
| | 🔴 Connection Pool Exhaustion      | | 🟢 Missing Realtime Permissions    | | EVIDENCE DRAWER (Right| |
| | Severity: High (32 mentions)       | | Severity: Medium (18 mentions)     | | --------------------- | |
| | Users hit max connections when     | | Developers want granular RLS-like  | | Cluster: Connection   | |
| | deploying on Serverless Vercel.    | | rules directly on Realtime topics. | | Pool Exhaustion       | |
| | Top Source: r/nextjs (65% share)   | | Top Source: YouTube review         | |                       | |
| |                                    | |                                    | | "Every time our site  | |
| | [ View 14 Evidence Quotes -> ]     | | [ View 7 Evidence Quotes -> ]      | | hits Reddit frontpage,| |
| +------------------------------------+ +------------------------------------+ | Supabase pooler dies  | |
|                                                                               | within 90 seconds..." | |
| +------------------------------------+ +------------------------------------+ | — u/dev_dan on Reddit | |
| | 🟡 External PgBouncer Hack         | | 🔵 Self-Hosting Backup Complexity  | | [Open Post ↗] 42 ▲    | |
| | Severity: Medium (11 mentions)     | | Severity: High (13 mentions)       | |                       | |
| | Teams deploy custom EC2 PgBouncer  | | Backups and WAL-G configuration is | | "We had to set up an  | |
| | instances to prevent serverless OOM| | documented poorly for production.  | | external PgBouncer..."| |
| |                                    | |                                    | | — Fireship Review     | |
| | [ View 5 Evidence Quotes -> ]      | | [ View 6 Evidence Quotes -> ]      | | [Watch Video ↗] 08:42 | |
| +------------------------------------+ +------------------------------------+ +-----------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

---

### 4.4 Screen 4: Autonomous PRD & Spec Studio (`/research/:id/prd`)

```
+-------------------------------------------------------------------------------+
| (•) PulseRadar > PRD Studio   [Overview] [Clusters] [★ PRD Studio]  [📋 Copy] |
+-------------------------------------------------------------------------------+
| [ Regenerate with Focus: [Serverless Scaling ▼] ]     [ ⬇ Export Markdown ]   |
|                                                                               |
| # Product Requirements Document (PRD): Supabase Serverless Connection Shield   |
|                                                                               |
| ## 1. Problem Statement                                                       |
| 38% of analyzed user complaints cite connection pool starvation when deployed  |
| on modern serverless runtimes (Next.js App Router on Vercel).                 |
| > Verified by 32 independent community quotes across Reddit and YouTube.       |
|                                                                               |
| ## 2. Target User Persona & Mental Model                                      |
| Full-Stack Next.js Developer who expects database connections to scale        |
| seamlessly without manual connection pool tuning.                             |
|                                                                               |
| ## 3. Proposed Solution Requirements                                          |
| - FR-1: Zero-configuration automatic connection multiplexing for edge workers. |
| - FR-2: Built-in pool exhaustion circuit breaker with client retry headers.   |
|                                                                               |
| ## 4. User Stories & Acceptance Criteria                                      |
| - Given a burst of 1,000 concurrent serverless requests                       |
| - When connection limits are reached                                          |
| - Then queue incoming queries for up to 500ms before returning 429 Retry-After |
+-------------------------------------------------------------------------------+
```

---

## 5. Component System & Interaction Models

*   **Pill Tabs & Filters:** Instant zero-re-render client-side filtering of clusters using Zustand.
*   **Quote Drawer:** Slides out from the right (`width: 440px`), keeping the main cluster grid visible for rapid contextual comparison.
*   **Copy to Clipboard:** Every quote and generated section features a one-click copy button with instant toast feedback (`"Copied quote with citation"`).
*   **Responsive Breakpoints:**
    *   `Desktop (> 1280px)`: Multi-column grid with persistent drawer.
    *   `Tablet (768px – 1279px)`: 2-column grid with overlay drawer.
    *   `Mobile (< 768px)`: Single-column stacked cards with bottom modal sheet.
