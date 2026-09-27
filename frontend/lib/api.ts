import { ResearchSession, StartResearchPayload, YouTubeTranscriptData, YouTubeDownloadFormatsResponse, UniverSlideData, DoctorReport } from "./types";

export function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    const url = process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
    return url.endsWith("/api/v1") ? url : `${url}/api/v1`;
  }
  // In client browser:
  if (typeof window !== "undefined") {
    // If running on Vercel or any non-localhost host, use direct Render URL
    if (
      window.location.hostname.includes("vercel.app") ||
      (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1")
    ) {
      return "https://product-research-enpj.onrender.com/api/v1";
    }
    return "/api/v1";
  }
  // Server-side rendering default to production Render URL
  return "https://product-research-enpj.onrender.com/api/v1";
}

export function getEventSourceUrl(sessionId: string): string {
  const base = getBaseUrl();
  return `${base}/research/${sessionId}/events`;
}

export async function startResearch(payload: StartResearchPayload): Promise<{ session_id: string; status: string }> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`Failed to start research: ${res.statusText} ${errorText}`);
  }
  return res.json();
}

export async function getResearchSession(sessionId: string): Promise<ResearchSession> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/research/${sessionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch research session: ${res.statusText}`);
  }
  return res.json();
}

export async function listRecentSessions(): Promise<ResearchSession[]> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/research`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return [];
    }
    return res.json();
  } catch (err) {
    console.error("Error listing sessions:", err);
    return [];
  }
}

export async function generatePrd(sessionId: string, customInstructions?: string): Promise<{ markdown_content: string }> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/research/${sessionId}/generate-prd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      spec_type: "PRD",
      custom_instructions: customInstructions,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to generate PRD: ${res.statusText}`);
  }
  return res.json();
}

export function getExportUrl(sessionId: string, format: "markdown" | "json" | "ai-bundle"): string {
  const base = getBaseUrl();
  return `${base}/research/${sessionId}/export/${format}`;
}

export async function saveChannelCredentials(credentials: Record<string, string>): Promise<any> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/settings/channels`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!res.ok) {
    throw new Error(`Failed to save credentials: ${res.statusText}`);
  }
  return res.json();
}

export async function getChannelsStatus(): Promise<any> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/settings/channels`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to get channels status: ${res.statusText}`);
  }
  return res.json();
}

// ============================================================================
// SEO API Clients
// ============================================================================

export function getSeoEventSourceUrl(auditId: string): string {
  const base = getBaseUrl();
  return `${base}/seo/audit/${auditId}/events`;
}

export function getSeoExportUrl(auditId: string, format: "markdown" | "json"): string {
  const base = getBaseUrl();
  return `${base}/seo/audit/${auditId}/export/${format}`;
}

export async function startSeoAudit(payload: { url: string; audit_type: string }): Promise<{ audit_id: string; status: string }> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/seo/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`Failed to start SEO audit: ${res.statusText} ${errorText}`);
  }
  return res.json();
}

export async function getSeoAudit(auditId: string): Promise<any> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/seo/audit/${auditId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch SEO audit: ${res.statusText}`);
  }
  return res.json();
}

export async function listRecentSeoAudits(): Promise<any[]> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/seo/audits`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error listing SEO audits:", err);
    return [];
  }
}

// ============================================================================
// Office Studio API Clients (Univer Data Bridge & Persistence)
// ============================================================================

export interface OfficeSourceItem {
  id: string;
  title: string;
  source_type: "research" | "seo";
  created_at: string;
  status: string;
  clusters_count?: number;
  signals_count?: number;
  items_count?: number;
  overall_score?: number | null;
  geo_score?: number | null;
  meta: Record<string, any>;
}

export interface OfficeSourcesResponse {
  research: OfficeSourceItem[];
  seo: OfficeSourceItem[];
}

export interface OfficeConnectedData {
  source_type: "research" | "seo";
  source_id: string;
  session_id?: string;
  query?: string;
  domain?: string;
  title: string;
  summary: string;
  workbook?: any;
  document?: {
    title: string;
    markdown: string;
  };
  document_markdown?: string;
  markdown?: string;
  slides?: UniverSlideData;
  stats?: Record<string, any>;
  scores?: Record<string, any>;
}

export interface OfficeSavedDocument {
  id: string;
  title: string;
  doc_type: "sheets" | "docs" | "slides";
  source_type?: string;
  source_id?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
  snapshot?: any;
}

export async function listOfficeSources(): Promise<OfficeSourcesResponse> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/office/sources`, { cache: "no-store" });
    if (!res.ok) return { research: [], seo: [] };
    return res.json();
  } catch (err) {
    console.error("Error fetching office sources:", err);
    return { research: [], seo: [] };
  }
}

export async function connectOfficeSource(
  sourceType: "research" | "seo",
  sourceId: string
): Promise<OfficeConnectedData> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/office/connect/${sourceType}/${sourceId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to connect ${sourceType} source: ${res.statusText}`);
  }
  return res.json();
}

export function getOfficeExportXlsxUrl(sourceType: "research" | "seo", sourceId: string): string {
  const base = getBaseUrl();
  return `${base}/office/export/${sourceType}/${sourceId}/xlsx`;
}

export function getOfficeExportPptxUrl(sourceType: "research" | "seo", sourceId: string): string {
  const base = getBaseUrl();
  return `${base}/office/export/${sourceType}/${sourceId}/pptx`;
}

export async function exportOfficeCustomPptx(payload: {
  title: string;
  slides: any;
}): Promise<Blob> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/office/export/custom-pptx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to export PowerPoint presentation: ${res.statusText}`);
  }
  return res.blob();
}

export async function listOfficeDocuments(): Promise<OfficeSavedDocument[]> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/office/documents`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching office documents:", err);
    return [];
  }
}

export async function getOfficeDocument(docId: string): Promise<OfficeSavedDocument> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/office/documents/${docId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch document: ${res.statusText}`);
  }
  return res.json();
}

export async function saveOfficeDocument(payload: {
  id?: string;
  title: string;
  doc_type: "sheets" | "docs" | "slides";
  source_type?: string;
  source_id?: string;
  snapshot: any;
  summary?: string;
}): Promise<{ status: string; id: string; message: string }> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/office/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to save office document: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteOfficeDocument(docId: string): Promise<{ status: string; id: string }> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/office/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete document: ${res.statusText}`);
  }
  return res.json();
}

// ============================================================================
// YouTube Transcript API Client
// ============================================================================

export async function fetchYouTubeTranscript(
  urlOrId: string,
  languages?: string[],
  forceWhisper?: boolean,
  whisperKey?: string
): Promise<YouTubeTranscriptData> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/youtube/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url_or_id: urlOrId,
      languages: languages || ["en", "en-US", "en-GB"],
      force_whisper: forceWhisper || false,
      whisper_key: whisperKey || undefined,
    }),
  });
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`Failed to fetch transcript: ${res.statusText} ${errorText}`);
  }
  return res.json();
}

export async function transcribeYouTubeAudio(
  urlOrId: string,
  apiKey?: string,
  provider?: string
): Promise<YouTubeTranscriptData> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/youtube/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url_or_id: urlOrId,
      api_key: apiKey || undefined,
      provider: provider || "auto",
    }),
  });
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`Failed to transcribe audio: ${res.statusText} ${errorText}`);
  }
  return res.json();
}

export async function getYouTubeWhisperStatus(): Promise<{
  groq_configured: boolean;
  openai_configured: boolean;
  whisper_ready: boolean;
  default_provider: string;
  model: string;
}> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/youtube/whisper-status`, { cache: "no-store" });
    if (!res.ok) return { groq_configured: false, openai_configured: false, whisper_ready: false, default_provider: "none", model: "whisper-large-v3" };
    return res.json();
  } catch {
    return { groq_configured: false, openai_configured: false, whisper_ready: false, default_provider: "none", model: "whisper-large-v3" };
  }
}

export async function getYouTubeVideoInfo(videoId: string): Promise<any> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/youtube/info/${videoId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchYouTubeFormats(urlOrId: string): Promise<YouTubeDownloadFormatsResponse> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/youtube/formats?url=${encodeURIComponent(urlOrId)}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`Failed to fetch formats: ${res.statusText} ${errorText}`);
  }
  return res.json();
}

export function getYouTubeDownloadUrl(params: {
  url: string;
  type: "video" | "audio" | "subtitle";
  quality?: string;
  audio_format?: string;
  audio_bitrate?: string;
  format_id?: string;
  sub_lang?: string;
  sub_format?: string;
  normalize?: boolean;
}): string {
  const base = getBaseUrl();
  const searchParams = new URLSearchParams();
  searchParams.set("url", params.url);
  searchParams.set("type", params.type);
  if (params.quality) searchParams.set("quality", params.quality);
  if (params.audio_format) searchParams.set("audio_format", params.audio_format);
  if (params.audio_bitrate) searchParams.set("audio_bitrate", params.audio_bitrate);
  if (params.format_id) searchParams.set("format_id", params.format_id);
  if (params.sub_lang) searchParams.set("sub_lang", params.sub_lang);
  if (params.sub_format) searchParams.set("sub_format", params.sub_format);
  if (params.normalize) searchParams.set("normalize", "true");
  return `${base}/youtube/download?${searchParams.toString()}`;
}

// ============================================================================
// Multi-Channel Diagnostic Doctor Client
// ============================================================================

export async function getDoctorReport(): Promise<DoctorReport> {
  const base = getBaseUrl();
  try {
    const res = await fetch(`${base}/doctor`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`Failed to fetch doctor report: ${res.statusText}`);
    }
    return res.json();
  } catch (err) {
    console.error("Doctor report fetch error:", err);
    throw err;
  }
}


