// ============================================================================
// Lab API Clients — OS Project Integrations (Waves 1-4)
// ============================================================================
import {
  BackupsResponse, BackupManifest, FramesStatus, FramesResult,
  GatewayTool, GatewayResult, ClipsRankResponse, ClipCutResponse,
  SecurityAuditResult, TrafficCorrelation, Workflow, WorkflowRunResult,
  GridSignalsResponse, TweetEmbeds, BrowserSessionInfo
} from "./lab-types";
import { getBaseUrl } from "./api";

function base(): string {
  return getBaseUrl();
}

// ---------------------------------------------------------------------------
// Backups (Wave 1)
// ---------------------------------------------------------------------------

export async function listBackups(): Promise<BackupsResponse> {
  const res = await fetch(`${base()}/lab/backups`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to list backups: ${res.statusText}`);
  return res.json();
}

export async function createBackup(name: string, note = ""): Promise<BackupManifest> {
  const res = await fetch(`${base()}/lab/backups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, note }),
  });
  if (!res.ok) throw new Error(`Backup failed: ${res.statusText}`);
  return res.json();
}

export async function deleteBackup(snapId: string): Promise<void> {
  const res = await fetch(`${base()}/lab/backups/${snapId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
}

export async function restoreBackup(snapId: string): Promise<{ success: boolean; restored: any[]; restart_required: boolean }> {
  const res = await fetch(`${base()}/lab/backups/${snapId}/restore`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Restore failed: ${text || res.statusText}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Video Reports (Wave 1)
// ---------------------------------------------------------------------------

export function getTranscriptReportUrl(videoId: string): string {
  return `${base()}/lab/reports/transcript/${encodeURIComponent(videoId)}`;
}

export async function renderMarkdownReport(title: string, subtitle: string, markdown: string): Promise<string> {
  const res = await fetch(`${base()}/lab/reports/markdown`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, subtitle, markdown }),
  });
  if (!res.ok) throw new Error(`Report render failed: ${res.statusText}`);
  return res.text();
}

// ---------------------------------------------------------------------------
// Tweet Embeds (Wave 1 — FxEmbed)
// ---------------------------------------------------------------------------

export async function fetchTweetEmbeds(url: string): Promise<TweetEmbeds | null> {
  try {
    const res = await fetch(`${base()}/lab/twitter/embed?url=${encodeURIComponent(url)}`, { cache: "no-store" });
    if (!res.ok) return null;
    const data = await res.json();
    return data.embeds || null;
  } catch {
    return null;
  }
}

export interface TweetBatchResult {
  success: boolean;
  found: number;
  enriched: number;
  results: { url: string; embeds: TweetEmbeds | null }[];
}

export async function extractSessionTweetMedia(sessionId: string, limit = 12): Promise<TweetBatchResult> {
  const res = await fetch(`${base()}/lab/twitter/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, limit }),
  });
  if (!res.ok) throw new Error(`Tweet media extraction failed: ${res.statusText}`);
  return res.json();
}

export async function renderInteractiveDiagram(title: string, markdown: string): Promise<string> {
  const res = await fetch(`${base()}/lab/diagrams/interactive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, subtitle: "", markdown }),
  });
  if (!res.ok) throw new Error(`Diagram build failed: ${res.statusText}`);
  return res.text();
}

// ---------------------------------------------------------------------------
// Video Frames + OCR (Wave 2)
// ---------------------------------------------------------------------------

export async function getFramesStatus(): Promise<FramesStatus> {
  const res = await fetch(`${base()}/lab/video/frames/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Frames status failed: ${res.statusText}`);
  return res.json();
}

export async function extractFrames(urlOrId: string, count = 6, ocr = true): Promise<FramesResult> {
  const res = await fetch(`${base()}/lab/video/frames`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url_or_id: urlOrId, count, ocr }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Frame extraction failed: ${res.statusText}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Tool Gateway (Wave 2)
// ---------------------------------------------------------------------------

export async function listGatewayTools(category?: string, q?: string): Promise<{ count: number; tools: GatewayTool[] }> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (q) params.set("q", q);
  const res = await fetch(`${base()}/lab/gateway/tools?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Gateway tools failed: ${res.statusText}`);
  return res.json();
}

export async function callGatewayTool(toolId: string, params: Record<string, any>, limit = 20): Promise<GatewayResult> {
  const res = await fetch(`${base()}/lab/gateway/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool_id: toolId, params, limit }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Gateway call failed: ${res.statusText}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Clip Studio (Wave 3)
// ---------------------------------------------------------------------------

export async function rankClips(urlOrId: string, maxClips = 3, minDuration = 20, maxDuration = 55): Promise<ClipsRankResponse> {
  const res = await fetch(`${base()}/lab/clips/rank`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url_or_id: urlOrId, max_clips: maxClips, min_duration: minDuration, max_duration: maxDuration }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Clip ranking failed: ${res.statusText}`);
  }
  return res.json();
}

export async function cutClip(urlOrId: string, start: number, end: number): Promise<ClipCutResponse> {
  const res = await fetch(`${base()}/lab/clips/cut`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url_or_id: urlOrId, start, end }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Clip cut failed: ${res.statusText}`);
  }
  return res.json();
}

export function getClipFileUrl(name: string): string {
  return `${base()}/lab/clips/file/${encodeURIComponent(name)}`;
}

// ---------------------------------------------------------------------------
// Security Posture (Wave 3)
// ---------------------------------------------------------------------------

export async function runSecurityAudit(url: string): Promise<SecurityAuditResult> {
  const res = await fetch(`${base()}/lab/security/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Security audit failed: ${res.statusText}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Traffic Correlation (Wave 3)
// ---------------------------------------------------------------------------

export async function runTrafficCorrelation(domain: string, auditId?: string): Promise<TrafficCorrelation> {
  const res = await fetch(`${base()}/lab/seo/traffic-correlation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, audit_id: auditId || undefined }),
  });
  if (!res.ok) throw new Error(`Traffic correlation failed: ${res.statusText}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Workflows (Wave 4)
// ---------------------------------------------------------------------------

export interface WorkflowStepInput {
  name: string;
  type: string;
  config: Record<string, any>;
  depends_on: string[];
}

export async function listWorkflows(): Promise<{ count: number; workflows: Workflow[] }> {
  try {
    const res = await fetch(`${base()}/lab/workflows`, { cache: "no-store" });
    if (!res.ok) return { count: 0, workflows: [] };
    return res.json();
  } catch {
    return { count: 0, workflows: [] };
  }
}

export async function createWorkflow(payload: {
  name: string; description?: string; steps: WorkflowStepInput[];
  schedule?: string; interval_hours?: number;
}): Promise<{ success: boolean; workflow: Workflow }> {
  const res = await fetch(`${base()}/lab/workflows`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Workflow creation failed: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteWorkflow(wfId: string): Promise<void> {
  const res = await fetch(`${base()}/lab/workflows/${wfId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
}

export async function runWorkflow(wfId: string, trigger = "manual"): Promise<WorkflowRunResult> {
  const res = await fetch(`${base()}/lab/workflows/${wfId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trigger }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Workflow run failed: ${res.statusText}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Signals Mega-Grid (Wave 4)
// ---------------------------------------------------------------------------

export async function fetchGridSignals(opts: {
  q?: string; channel?: string; sort?: string; offset?: number; limit?: number;
}): Promise<GridSignalsResponse> {
  const params = new URLSearchParams();
  if (opts.q) params.set("q", opts.q);
  if (opts.channel) params.set("channel", opts.channel);
  if (opts.sort) params.set("sort", opts.sort);
  params.set("offset", String(opts.offset ?? 0));
  params.set("limit", String(opts.limit ?? 200));
  const res = await fetch(`${base()}/lab/grid/signals?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Grid fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchGridChannels(): Promise<{ channel: string; count: number }[]> {
  try {
    const res = await fetch(`${base()}/lab/grid/channels`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.channels || [];
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Browser Session (Wave 4)
// ---------------------------------------------------------------------------

export async function getBrowserSession(): Promise<BrowserSessionInfo> {
  const res = await fetch(`${base()}/lab/browser/session`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Browser session fetch failed: ${res.statusText}`);
  return res.json();
}

export async function setBrowserSession(userDataDir: string): Promise<{ success: boolean; user_data_dir: string; note: string }> {
  const res = await fetch(`${base()}/lab/browser/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_data_dir: userDataDir }),
  });
  if (!res.ok) throw new Error(`Browser session update failed: ${res.statusText}`);
  return res.json();
}
