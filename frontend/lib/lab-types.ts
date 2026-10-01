// ============================================================================
// Lab — OS Project Integrations (Waves 1-4)
// Backups (borg) · Video Reports (video-lens) · Tweet Embeds (FxEmbed)
// Frames+OCR (mcp-video-analyzer) · Tool Gateway (treg) · Clips (Shorts-Gen)
// Security Posture (shannon) · Traffic Correlation (laravel-analytics)
// Workflows (Dagu) · Signals Grid (glide-data-grid) · Browser Session (BrowserSkill)
// ============================================================================

export interface BackupFileEntry {
  target: string;
  status: string;
  path?: string | null;
  size_bytes?: number;
  sha256?: string;
  error?: string;
}

export interface BackupManifest {
  snapshot_id: string;
  created_at: string | null;
  name: string;
  note?: string;
  file_count: number;
  total_bytes: number;
  files: BackupFileEntry[];
}

export interface BackupsResponse {
  backups: BackupManifest[];
  backup_root: string;
  targets: string[];
  rotation: { keep: number; policy: string };
}

export interface FramesStatus {
  yt_dlp: boolean;
  ffmpeg: boolean;
  tesseract: boolean;
  pil: boolean;
  ready: boolean;
  ocr_ready: boolean;
  install: string[];
}

export interface FrameResult {
  t: number;
  timestamp: string;
  permalink: string;
  frame_b64?: string | null;
  ocr_text?: string | null;
  error?: string;
}

export interface FramesResult {
  success: boolean;
  video_id: string;
  duration?: number;
  interval?: number;
  capabilities: Record<string, boolean>;
  missing_for_full?: string[];
  frames: FrameResult[];
  ocr_hits?: number;
  error?: string;
  install_hint?: string;
  note?: string;
}

export interface GatewayToolParam {
  name: string;
  required: boolean;
  type: string;
  description: string;
}

export interface GatewayTool {
  id: string;
  name: string;
  category: string;
  description: string;
  provider: string;
  internal?: string;
  params: GatewayToolParam[];
  price_hint: string;
  enabled: boolean;
}

export interface GatewayResult {
  tool: string;
  success: boolean;
  count?: number;
  results?: any[];
  markdown?: string;
  error?: string;
}

export interface ClipCandidate {
  rank?: number;
  start: number;
  end: number;
  duration: number;
  start_ts: string;
  permalink: string;
  text: string;
  score: number;
}

export interface ClipsRankResponse {
  success: boolean;
  video_id: string;
  video_title?: string;
  clips: ClipCandidate[];
  candidates_evaluated: number;
  algorithm: string;
}

export interface ClipCutResponse {
  success: boolean;
  download_url: string;
  file: string;
  size_bytes: number;
  start: number;
  end: number;
}

export interface SecurityFinding {
  check: string;
  status: string;
  detail: string;
}

export interface SecurityAuditResult {
  success: boolean;
  url: string;
  host: string;
  score: number;
  grade: string;
  passed: number;
  total: number;
  status_counts: Record<string, number>;
  critical_failures: SecurityFinding[];
  findings: SecurityFinding[];
  boundary: string;
}

export interface TrafficCorrelation {
  success: boolean;
  domain: string;
  audits: { audit_id: string; date: string; overall_score: number; url: string }[];
  traffic_series: { date: string; sessions: number; pageviews: number }[];
  correlation: number | null;
  interpretation: string;
  ga4_ready: boolean;
  note: string;
}

export interface WorkflowStepDef {
  name: string;
  type: string;
  config: Record<string, any>;
  depends_on: string[];
}

export interface WorkflowRun {
  id: string;
  started: string;
  status: string;
  steps: { step: string; status: string }[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStepDef[];
  schedule?: string | null;
  interval_hours?: number | null;
  created_at: string;
  runs: WorkflowRun[];
  enabled: boolean;
}

export interface WorkflowRunResult {
  success: boolean;
  run: { run_id: string; trigger: string; started: string; finished: string; status: string };
  logs: { step: string; type: string; status: string; result?: any; error?: string; started: string; finished: string }[];
}

export interface GridSignal {
  id: string;
  channel: string;
  title: string;
  author?: string | null;
  engagement: number;
  url: string;
  created_at: string;
  preview: string;
  has_transcript: boolean;
}

export interface GridSignalsResponse {
  count: number;
  offset: number;
  limit: number;
  items: GridSignal[];
}

export interface TweetMedia {
  type: string;
  url?: string;
  thumbnail?: string | null;
  alt?: string | null;
  duration_ms?: number;
}

export interface TweetEmbeds {
  provider: string;
  screen_name: string;
  status_id: string;
  likes?: number;
  retweets?: number;
  replies?: number;
  views?: number;
  created_at?: string;
  translated_text?: string | null;
  media: TweetMedia[];
  poll?: { total_votes: number; options: { label: string; votes: number; percent: number }[] } | null;
  quote?: { author?: string; text?: string; url?: string; likes?: number } | null;
}

export interface BrowserSessionInfo {
  user_data_dir: string;
  configured: boolean;
  profile_valid: boolean;
  how_to: string[];
  benefit: string;
  channels_benefiting: string[];
  safety: string;
}
