# Integration Conflict Analysis — Which Project Wins Each Capability

Several OS projects in `C:\Useful OS Projects` overlap. This doc records the
end-to-end verdicts (winner, rationale, and what we salvaged from the loser).

| Capability | Contenders | Winner | Rationale |
|---|---|---|---|
| **YouTube captions** | `youtube-transcript-api` (ytfetcher) vs `yt-dlp` (YTSage/video-lens) | **yt-dlp, with transcript-api as cheap Tier-1** | transcript-api is lighter & faster when it works, but dies on the "Sign in to confirm you're not a bot" wall. yt-dlp speaks innerTube player clients (web_embedded/mweb/android) and borrows real browser cookies. Final chain: transcript-api → **yt-dlp captions (Tier 1.5)** → benchmark fallback → Whisper → chapters. Implemented in `engine/ytdlp_captions.py`. |
| **YouTube downloads** | `ytfetcher` vs `YTSage` vs `AI-Shorts-Gen` | **YTSage engine** (already `youtube_downloader.py`) | Multi-res merging, audio extraction, metadata embedding, resilient opts. ytfetcher's contribution remains the realistic-header session used in Tier 1. |
| **Diagram generation** | `diagram_agent` (PaperBanana SVG) vs `archify` | **Both, different jobs** | Static SVG is instant + embeds in exports (kept for briefs). Archify-style interactive HTML (pan/zoom/collapse) is for exploration — new `engine/diagram_builder.py` + `/lab/diagrams/interactive` + PRD "Diagram" button. |
| **Data grids** | `univer` (office SDK) vs `glide-data-grid` | **Univer for office docs, Glide for big data** | Univer is a full office suite (formulas/styling/xlsx) — irreplaceable for Sheets/Docs/Slides. Glide is a canvas grid that virtualizes 100k+ rows with native scroll — Univer chokes there. Now used in Lab → Signals Grid. |
| **Tweet data** | FxEmbed vs DDG site-crawler vs cookie-auth API | **Layered: cookie API → FxEmbed → DDG** | Cookie-auth gives full search but needs user keys; FxEmbed needs no auth and returns media/polls/quotes; DDG is the unauthenticated floor. FxEmbed also *replaces* fake engagement numbers with real ones (`engine/twitter_embeds.py`). |
| **X/Twitter scraping vendor** | `social-media-scraping-apis` directory vs native channels | **Native channels; directory as vendor catalog** | The 3,268-API directory is a listings repo (many paid/gray-area vendors). Surfaced as `directory` metadata in `/lab/gateway/tools`; live integrations stay in-house (free, auditable). |
| **Browser control** | `BrowserSkill` (CDP attach) vs `agent-desktop` vs `robotjs` | **BrowserSkill pattern** | Playwright `launch_persistent_context` reuses the logged-in profile (implemented: `BROWSER_USER_DATA_DIR`). agent-desktop's observe→decide→act loop is overkill for scraping; robotjs is OS-level GUI automation, wrong layer. |
| **Workflow orchestration** | `Dagu` vs existing automations vs pentagi | **Dagu pattern (Lab Workflows)** | Dagu: single-binary YAML DAGs, retries, run history — matches self-hosted PulseRadar. PentAGI's multi-agent supervisor is a security-pentest architecture, not a scheduler. Existing automations remain for event→webhook triggers. |
| **Skill capture** | `skill-recorder` vs `Power users skills` | **Complementary, deferred** | skill-recorder is an Electron app (needs desktop runtime); knowledge-work-plugins are prompts/presets. Both inform a future "record your sweep" feature — no runtime conflict today. |
| **Security auditing** | `shannon` (active pentest) vs `security-audit-skill` (agent skill) vs our passive audit | **Passive audit in product; shannon boundary respected** | Running real exploits from a web app is unsafe/unethical without authorization. Lab Security tab = headers/cookies/exposure GET-probes; shannon's methodology (no exploit, no report) documented as the manual deep-dive path. |
| **SEO traffic data** | `laravel-analytics` (GA4) vs directory SERP vendors | **GA4 patterns, demo-correlation shipped** | GA4 Data API needs service-account credentials; correlation module is live with deterministic demo series and a clean upgrade path (`GOOGLE_API_KEY`). |
| **Math visuals** | `manim` vs `vismath` | **vismath pattern if ever built** | vismath already wraps manim with parametrized scenes + render API + validated AI plans (no hallucinated manim code). manim raw is the engine underneath — no product surface yet. |
| **Android signals** | `lamda-10` (FIRERPA) vs `mobile verification` (MVT) | **Different domains — no conflict** | FIRERPA = device automation for app-store/mobile sentiment (future channel). MVT = forensics of compromised devices (out of scope). |
| **Agent framework** | `pentagi` vs `Openrouter for agents` (treg) | **treg wins for data access; pentagi for architecture reference** | Tool gateway (treg) is already live in Lab; pentagi's Docker-isolated worker pattern informs future agent fleet isolation. |

## Not integrated (by design)

| Project | Reason |
|---|---|
| GLaDOS | Personality voice-core (fun, but no research/SEO value). Optional Easter-egg TTS persona. |
| Github issue resolver (SWE-bench) | Benchmark harness for code agents — testing tool, not product feature. |
| borg DB backup | Backup *concept* adopted (snapshot/rotate/restore in Lab); borg itself is a system binary, not embeddable. |
| OpenStock | Trading platform — could be a "market signals" channel later; overlaps Polymarket/Xueqiu channels which already exist. |
| robotjs / agent-desktop | See browser-control row. |
| office SDK (univer-dev) | Already the Office Studio base — tracked upstream for upgrades (Bases/Boards). |
