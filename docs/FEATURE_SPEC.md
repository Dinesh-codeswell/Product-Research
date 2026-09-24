# PulseRadar — Detailed Feature Listing & User Stories

> **Specification Version:** 1.0.0  
> **Status:** Implementation-Ready  
> **Methodology:** Agile Epics, User Stories, and Gherkin Acceptance Criteria (Given-When-Then)

---

## Epic 1: Multi-Channel Data Ingestion

### Feature 1.1: Multi-Subreddit Query Dispatcher
*   **Description:** Allows the user to specify a research query or competitor name and target either specific subreddits (e.g., `r/reactjs`, `r/webdev`) or broad topic search across Reddit.
*   **User Story:** As a Product Manager, I want to query Reddit for complaints regarding a specific framework so that I can see unvarnished developer feedback.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: User runs a targeted query on Reddit
      Given the user enters query "Next.js App Router" and selects Reddit channel
      When the ingestion starts
      Then the Reddit adapter dispatches search requests to relevant tech subreddits
      And retrieves up to 50 relevant posts and top-level comments
      And ignores deleted or removed posts
    ```

### Feature 1.2: YouTube Video Review & Transcript Extraction
*   **Description:** Searches YouTube for high-engagement product reviews, comparisons, and walkthroughs, pulling full timestamped transcripts.
*   **User Story:** As a Founder, I want to extract transcripts from YouTube video reviews so that I can capture nuanced long-form feedback that users speak rather than write.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Extracting YouTube review transcripts
      Given a query targeting a SaaS tool (e.g., "Supabase vs Firebase")
      When YouTube search returns top 5 relevant review videos
      Then the YouTube adapter extracts video title, author, view count, and full transcripts
      And segments the transcript into timestamped thematic paragraphs
      And links each paragraph to the exact video URL at that timestamp (?t=120s)
    ```

### Feature 1.3: Anti-Bot Resilience & Local Session Re-use
*   **Description:** Borrows local browser cookies or uses randomized user agents and exponential backoff to ensure continuous scraping without 403 blocks.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Handling rate limits gracefully
      Given Reddit responds with HTTP 429 (Too Many Requests)
      When the scraper encounters the 429 status code
      Then it logs an exponential backoff notice
      And waits for 2 seconds before retrying with an alternative User-Agent
      And never crashes the main research pipeline
    ```

---

## Epic 2: Processing, Embeddings & Semantic Clustering

### Feature 2.1: Noise Reduction & Text Cleaning
*   **Description:** Strips promotional links, bot disclaimers, automoderator warnings, and boilerplate markdown from raw text.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Cleaning noisy forum comments
      Given a Reddit comment contains bot disclaimers like "I am a bot, and this action was performed automatically"
      When the cleaner runs
      Then the bot boilerplate is stripped
      And any remaining text under 30 characters is dropped as low-signal
    ```

### Feature 2.2: Vector Embedding & Similarity Indexing
*   **Description:** Converts cleaned feedback items into dense vector embeddings using local or cloud models for high-speed semantic retrieval.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Vectorizing feedback items
      Given 80 cleaned feedback items
      When the embedding pipeline executes
      Then all 80 items are converted into 384-dimensional vector embeddings
      And stored in an in-memory/ChromaDB vector collection scoped to the active session
    ```

### Feature 2.3: Semantic Categorization & Clustering
*   **Description:** Groups feedback items into coherent thematic clusters and tags each cluster with a primary category: **Pain Point**, **Workaround**, **Feature Request**, or **Churn Trigger**.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Categorizing a thematic cluster
      Given a cluster of 15 items discussing "Database connection limits on Vercel"
      When the clustering and LLM classifier process the items
      Then the cluster is assigned Category="Pain Point"
      And Severity="High" based on volume and frustration sentiment
      And Title="Connection Pool Exhaustion on Serverless Runtimes"
    ```

---

## Epic 3: Grounded Evidence & Verbatim Quotes

### Feature 3.1: Verbatim Evidence Linker
*   **Description:** Every cluster must contain 3–5 representative verbatim quotes with author name, platform badge, upvote/view count, and clickable permalink.
*   **User Story:** As an Engineering Lead, I want to click any claim in the report to see the exact user quote and original forum thread so that I can verify the signal is real.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Viewing evidence quotes for an insight
      Given a user clicks on an insight cluster card
      When the Evidence Drawer opens
      Then it displays at least 3 verbatim quotes matching that theme
      And each quote has a clickable link that opens the original Reddit post or YouTube video timestamp
    ```

---

## Epic 4: Autonomous PRD & Spec Studio

### Feature 4.1: Automated PRD Generator
*   **Description:** Synthesizes verified user pain points into a structured Product Requirements Document following industry-standard formats (Problem, Persona, Functional Requirements, Edge Cases).
*   **User Story:** As a PM, I want to convert verified customer pain points into a draft PRD with one click so that I can immediately share it with my design and engineering teams.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Generating a PRD from research clusters
      Given a research session has identified at least 2 Pain Points and 1 Feature Request
      When the user clicks "Generate PRD"
      Then an LLM agent creates a structured markdown PRD
      And grounds every requirement in the identified user quotes
      And formats user stories with Given-When-Then acceptance criteria
    ```

### Feature 4.2: Markdown & JSON Export
*   **Description:** Exports the complete research report, quote ledger, and PRD into clean GitHub-flavored markdown or raw JSON.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Exporting report to Markdown
      Given a completed research session
      When the user clicks "Export to Markdown"
      Then a `.md` file downloads immediately
      And contains executive summary, cluster tables, verbatim quotes, and full PRD
    ```

---

## Epic 5: Real-Time Observability & UI Experience

### Feature 5.1: Live Ingestion Stepper via SSE
*   **Description:** Real-time event stream from the FastAPI backend updating the Next.js frontend on scraping progress, items parsed, and clustering phases.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Streaming ingestion progress to UI
      Given a research query has been launched
      When the backend executes scraping and clustering stages
      Then the UI progress bar advances in real time via Server-Sent Events
      And a live ticker shows the latest items fetched without page reload
    ```

### Feature 5.2: Instant Category Filtering & Search
*   **Description:** Client-side filtering of clusters by category (Pain Points, Workarounds, Desires) and instant keyword search across all scraped quotes.
*   **Acceptance Criteria:**
    ```gherkin
    Scenario: Filtering clusters by category
      Given 8 clusters displayed on screen
      When the user selects the "Pain Points" pill filter
      Then only clusters marked as "Pain Point" remain visible
      And the cluster count badge updates instantly
    ```
