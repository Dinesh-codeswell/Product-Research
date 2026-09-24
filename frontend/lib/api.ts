import { ResearchSession, StartResearchPayload } from "./types";

export function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    const url = process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
    return url.endsWith("/api/v1") ? url : `${url}/api/v1`;
  }
  // In client browser, use relative path so Next.js rewrites proxy cleanly with zero CORS issues
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  // Server-side rendering
  return "http://127.0.0.1:8000/api/v1";
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
