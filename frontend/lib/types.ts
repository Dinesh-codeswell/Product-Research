export interface EvidenceQuote {
  id: string;
  quote_text: string;
  permalink: string;
  source_author?: string;
  source_channel: string;
  engagement_score: number;
  created_at: string;
}

export type ClusterCategory = "PAIN_POINT" | "WORKAROUND" | "DESIRE" | "CHURN_TRIGGER";

export interface InsightCluster {
  id: string;
  title: string;
  category: ClusterCategory;
  description: string;
  severity_score: number;
  item_count: number;
  keyword_tags: string[];
  quotes: EvidenceQuote[];
  created_at: string;
}

export interface RawFeedback {
  id: string;
  channel: string;
  url: string;
  title?: string;
  content: string;
  author?: string;
  engagement_score: number;
  created_at: string;
}

export interface BrowserActionEvent {
  action: string;
  url: string;
  title?: string;
  description: string;
  screenshot?: string;
  channel?: string;
  timestamp: string;
  items_count?: number;
}

export interface ResearchSession {
  id: string;
  query: string;
  category?: string;
  channels_used: string[];
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
  total_items_scraped: number;
  execution_mode?: "focus" | "browser";
  executive_summary?: string;
  clusters: InsightCluster[];
  feedbacks?: RawFeedback[];
  created_at: string;
  updated_at: string;
}

export interface SSEProgressEvent {
  stage: string;
  percent: number;
  message: string;
  data?: Record<string, any>;
}

export interface StartResearchPayload {
  query: string;
  channels: string[];
  subreddits?: string[];
  max_items?: number;
  execution_mode?: "focus" | "browser";
  browser_approved?: boolean;
}

// ============================================================================
// SEO Intelligence & GEO Studio Types
// ============================================================================

export interface SeoPillarItem {
  rule: string;
  status: "PASS" | "PARTIAL" | "FAIL" | "CRITICAL";
  score: number;
  max: number;
  notes: string;
}

export interface SeoPillar {
  score: number;
  max: number;
  percentage: number;
  items: SeoPillarItem[];
}

export interface SeoGeoData {
  overall_score: number;
  readiness_tier: string;
  badge: string;
  pillars: {
    evidence_density: SeoPillar;
    structure_and_position: SeoPillar;
    authority_signals: SeoPillar;
    ai_crawlability: SeoPillar;
  };
  recommendations: string[];
}

export interface SeoTechnicalIssue {
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  field: string;
  message: string;
}

export interface SeoTechnicalData {
  success: boolean;
  url: string;
  status_code: number;
  response_time_ms: number;
  content_length_bytes: number;
  content_type: string;
  server: string;
  title: { text: string; length: number; status: string };
  meta_description: { text: string; length: number; status: string };
  canonical: { url: string; is_self: boolean; present: boolean };
  robots: { content: string; noindex: boolean; nofollow: boolean };
  headings: {
    h1: string[];
    h2: string[];
    h3: string[];
    h1_count: number;
    h2_count: number;
    h3_count: number;
  };
  open_graph: Record<string, string>;
  twitter_card: Record<string, string>;
  json_ld_schemas: any[];
  links: {
    internal_count: number;
    external_count: number;
    internal_sample: string[];
    external_sample: string[];
  };
  word_count: number;
  score: number;
  issues: SeoTechnicalIssue[];
  passes: string[];
}

export interface SeoRenderingData {
  tested: boolean;
  rendering_mode: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  ssr: { word_count: number; title: string; meta_description: string; h1_count: number; schema_count: number };
  csr: { word_count: number; title: string; meta_description: string; h1_count: number; schema_count: number; images_count: number };
  words_difference: number;
  word_growth_ratio: number;
  findings: Array<{ severity: string; title: string; description: string }>;
  note?: string;
}

export interface SeoImageData {
  score: number;
  total_images: number;
  missing_alt_count: number;
  alt_coverage_percent: number;
  modern_format_percent: number;
  cls_safe_percent: number;
  lazy_loaded_count: number;
  images: Array<{
    src: string;
    alt: string;
    has_alt: boolean;
    format: string;
    is_modern: boolean;
    has_dimensions: boolean;
    is_lazy: boolean;
  }>;
  issues: Array<{ severity: string; category: string; message: string }>;
}

export interface SeoAuditSession {
  id: string;
  url: string;
  domain: string;
  audit_type: "quick" | "full" | "geo" | "drift";
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
  overall_score: number;
  technical_score: number;
  geo_readiness_score: number;
  onpage_score: number;
  image_score: number;
  executive_summary?: string;
  results?: {
    success: boolean;
    url: string;
    domain: string;
    audit_type: string;
    scores: {
      overall: number;
      technical: number;
      geo_readiness: number;
      onpage: number;
      image: number;
      content_completeness: number;
    };
    executive_summary: string;
    technical: SeoTechnicalData;
    geo: SeoGeoData;
    rendering: SeoRenderingData;
    schemas: {
      detected_count: number;
      detected_schemas: any[];
      validation_findings: any[];
      generated_templates: Record<string, any>;
      html_snippet_sample: string;
    };
    meta: {
      title_variants: Array<{ variant: string; title: string; char_count: number; status: string; description: string }>;
      recommended_description: { text: string; length: number; status: string };
      open_graph: Record<string, string>;
      twitter_card: Record<string, string>;
      serp_simulation: { title: string; url: string; domain: string; description: string; is_truncated: boolean };
      html_code_block: string;
    };
    images: SeoImageData;
    keywords: {
      content_completeness_score: number;
      word_count: number;
      dimensions: Record<string, { score: number; max: number }>;
      top_keywords: Array<{ keyword: string; frequency: number; density_percent: number; intent: string; in_h1: boolean; in_h2: boolean; prominence: string }>;
      thin_content_warning: boolean;
    };
    drift: {
      has_baseline: boolean;
      drift_status: string;
      score_delta: number;
      regressions: string[];
      improvements: string[];
      baseline_timestamp?: string;
    };
  };
  created_at: string;
  updated_at: string;
}

export interface StartSeoAuditPayload {
  url: string;
  audit_type: "quick" | "full" | "geo" | "drift";
}

