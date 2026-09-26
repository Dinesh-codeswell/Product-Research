"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Cpu,
  Search,
  Sparkles,
  Zap,
  Brain,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Layers,
  Sliders,
  Play,
  RotateCw,
  Key,
  Database,
  ArrowRight,
  Filter,
  Check,
  Copy,
  AlertCircle,
  Eye,
  EyeOff,
  Gauge,
  HelpCircle,
  Clock,
  Compass
} from "lucide-react";

interface ModelEndpoint {
  id: string;
  platform: string;
  provider_name: string;
  model_id: string;
  display_name: string;
  family: string;
  intelligence_rank: number;
  speed_rank: number;
  size_label: string;
  context_window: number;
  rpm_limit: number | null;
  rpd_limit: number | null;
  tpm_limit: number | null;
  tpd_limit: number | null;
  monthly_token_budget: string;
  monthly_token_budget_tokens: number;
  supports_vision: boolean;
  supports_tools: boolean;
  is_reasoning: boolean;
  is_coding: boolean;
  requires_card: boolean;
  base_url: string;
  recommended_use: string;
}

interface ProviderInfo {
  platform: string;
  name: string;
  description: string;
  monthly_free_tokens: string;
  free_tier_models_count: number;
  requires_credit_card: boolean;
  is_keyless_supported: boolean;
  signup_url: string;
  key_url: string;
  rate_limit_summary: string;
  key_setup_guide: string;
  gotchas_and_tips: string;
  default_base_url: string;
}

interface AIConfig {
  active_model_id: string;
  active_provider: string;
  active_model_name: string;
  base_url: string;
  masked_api_key?: string;
  has_api_key: boolean;
  routing_strategy: string;
  temperature: number;
  use_freellmapi_gateway: boolean;
  freellmapi_gateway_url: string;
  masked_freellmapi_token?: string;
  has_freellmapi_token: boolean;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

const CTX_BUCKETS = [
  { key: 0, label: "Any Context" },
  { key: 32_000, label: "32K+" },
  { key: 128_000, label: "128K+" },
  { key: 1_000_000, label: "1M+ Frontier" },
];

const CAPABILITY_FILTERS = [
  { id: "all", label: "All Models", icon: Layers },
  { id: "reasoning", label: "🧠 Reasoning", icon: Brain },
  { id: "speed", label: "⚡ Ultra-Fast (>800 tps)", icon: Zap },
  { id: "tools", label: "⚙️ Tools / Function Calling", icon: Sliders },
  { id: "vision", label: "👁️ Multimodal Vision", icon: Eye },
  { id: "coding", label: "💻 Specialized Code", icon: Cpu },
  { id: "massive_context", label: "🌊 1M+ Context", icon: Compass },
];

export default function AIModelsPage() {
  const [activeTab, setActiveTab] = useState<"catalog" | "providers" | "config" | "playground">("catalog");
  
  // Catalog State
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("all");
  const [selectedCapability, setSelectedCapability] = useState("all");
  const [minContext, setMinContext] = useState(0);
  const [freeOnly, setFreeOnly] = useState(false);
  const [sortBy, setSortBy] = useState("smartest");

  // Config State
  const [activeConfig, setActiveConfig] = useState<AIConfig | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [gatewayUrlInput, setGatewayUrlInput] = useState("http://localhost:3001/v1");
  const [gatewayTokenInput, setGatewayTokenInput] = useState("");
  const [useGateway, setUseGateway] = useState(false);
  const [strategyInput, setStrategyInput] = useState("balanced");
  const [configSaving, setConfigSaving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Playground State
  const [playgroundPrompt, setPlaygroundPrompt] = useState("Analyze the top user friction points in modern serverless database connection pooling.");
  const [playgroundLoading, setPlaygroundLoading] = useState(false);
  const [playgroundResult, setPlaygroundResult] = useState<any>(null);

  // Stats
  const [stats, setStats] = useState({
    headline_tokens_monthly: "7.4 Billion",
    total_providers: 34,
    total_model_endpoints: 635,
    free_no_card_percentage: 94,
    max_context_window: 1_048_576,
    fastest_tps: "2,000+ tok/sec"
  });

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Fetch Models & Providers
  const fetchData = async () => {
    setLoading(true);
    try {
      const [modelsRes, provRes, cfgRes, statsRes] = await Promise.allSettled([
        fetch(`${BACKEND_URL}/api/v1/models`),
        fetch(`${BACKEND_URL}/api/v1/models/providers`),
        fetch(`${BACKEND_URL}/api/v1/models/config`),
        fetch(`${BACKEND_URL}/api/v1/models/stats`)
      ]);

      if (modelsRes.status === "fulfilled" && modelsRes.value.ok) {
        const data = await modelsRes.value.json();
        setModels(data.models || []);
      }
      if (provRes.status === "fulfilled" && provRes.value.ok) {
        const data = await provRes.value.json();
        setProviders(data.providers || []);
      }
      if (cfgRes.status === "fulfilled" && cfgRes.value.ok) {
        const data = await cfgRes.value.json();
        setActiveConfig(data);
        setUseGateway(data.use_freellmapi_gateway || false);
        setGatewayUrlInput(data.freellmapi_gateway_url || "http://localhost:3001/v1");
        setStrategyInput(data.routing_strategy || "balanced");
      }
      if (statsRes.status === "fulfilled" && statsRes.value.ok) {
        const data = await statsRes.value.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch AI models catalog:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter Models locally or through backend query
  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      // Query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesQ =
          m.display_name.toLowerCase().includes(q) ||
          m.model_id.toLowerCase().includes(q) ||
          m.provider_name.toLowerCase().includes(q) ||
          m.family.toLowerCase().includes(q) ||
          m.recommended_use.toLowerCase().includes(q);
        if (!matchesQ) return false;
      }

      // Provider filter
      if (selectedProvider !== "all" && m.platform !== selectedProvider) {
        return false;
      }

      // Capability filter
      if (selectedCapability === "reasoning" && !m.is_reasoning) return false;
      if (selectedCapability === "speed" && m.speed_rank > 2) return false;
      if (selectedCapability === "tools" && !m.supports_tools) return false;
      if (selectedCapability === "vision" && !m.supports_vision) return false;
      if (selectedCapability === "coding" && !m.is_coding) return false;
      if (selectedCapability === "massive_context" && m.context_window < 1_000_000) return false;

      // Min context
      if (minContext > 0 && m.context_window < minContext) return false;

      // Free only
      if (freeOnly && m.requires_card) return false;

      return true;
    }).sort((a, b) => {
      if (sortBy === "smartest") return a.intelligence_rank - b.intelligence_rank;
      if (sortBy === "fastest") return a.speed_rank - b.speed_rank;
      if (sortBy === "context") return b.context_window - a.context_window;
      if (sortBy === "free_budget") return b.monthly_token_budget_tokens - a.monthly_token_budget_tokens;
      return 0;
    });
  }, [models, searchQuery, selectedProvider, selectedCapability, minContext, freeOnly, sortBy]);

  // Activate Model
  const handleSelectModel = async (model: ModelEndpoint) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          active_model_id: model.id,
          active_provider: model.platform,
          active_model_name: model.display_name,
          base_url: model.base_url
        })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveConfig(data.config);
        showToast(`Activated ${model.display_name} for PulseRadar Synthesis!`);
      } else {
        showToast("Error updating active model.");
      }
    } catch (e) {
      showToast("Could not reach PulseRadar backend.");
    }
  };

  // Save Settings
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setConfigSaving(true);
    try {
      const payload: any = {
        routing_strategy: strategyInput,
        use_freellmapi_gateway: useGateway,
        freellmapi_gateway_url: gatewayUrlInput
      };
      if (apiKeyInput.trim()) payload.api_key = apiKeyInput.trim();
      if (gatewayTokenInput.trim()) payload.freellmapi_token = gatewayTokenInput.trim();

      const res = await fetch(`${BACKEND_URL}/api/v1/models/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setActiveConfig(data.config);
        setApiKeyInput("");
        setGatewayTokenInput("");
        showToast("AI Configuration & Credentials saved successfully!");
      } else {
        showToast("Failed to save settings.");
      }
    } catch (e) {
      showToast("Backend connection error.");
    } finally {
      setConfigSaving(false);
    }
  };

  // Run Test Playground
  const handleRunPlayground = async () => {
    setPlaygroundLoading(true);
    setPlaygroundResult(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: playgroundPrompt })
      });
      const data = await res.json();
      setPlaygroundResult(data);
    } catch (e: any) {
      setPlaygroundResult({
        status: "error",
        error: e.message || "Failed to contact backend."
      });
    } finally {
      setPlaygroundLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#000000] text-[#ffffff] font-sans antialiased selection:bg-[#9281f7]/30 selection:text-[#ffffff]">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-[#111315] border border-[#3ad389]/40 text-[#ffffff] rounded-[8px] shadow-2xl animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 className="h-4 w-4 text-[#3ad389]" />
          <span className="text-xs font-mono">{toastMessage}</span>
        </div>
      )}

      {/* Hero Header */}
      <section className="border-b border-[#292d30] bg-gradient-to-b from-[#0a0a0f] to-[#000000] py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1200px]">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-[6px] bg-[#9281f7]/10 border border-[#9281f7]/30 text-[#9281f7] text-xs font-mono mb-4">
                <Sparkles className="h-3.5 w-3.5" />
                <span>7.4 Billion Free Tokens Monthly · FreeLLMAPI Core Integration</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#ffffff]">
                AI Models & Free Tier Studio
              </h1>
              <p className="mt-2 text-sm text-[#a1a4a5] max-w-2xl">
                Aggregate 34 free LLM providers, 635 model endpoints, and OpenAI-compatible routing directly into PulseRadar for high-velocity, zero-token-waste product discovery.
              </p>
            </div>

            {/* Active Model Quick Indicator */}
            {activeConfig && (
              <div className="flex items-center gap-3 p-3 bg-[#111315] border border-[#292d30] rounded-[8px]">
                <div className="h-3 w-3 rounded-full bg-[#3ad389] animate-pulse" />
                <div className="text-xs">
                  <div className="text-[#a1a4a5] font-mono uppercase tracking-wider text-[10px]">Active Synthesis Engine</div>
                  <div className="font-semibold text-[#ffffff] flex items-center gap-1.5 mt-0.5">
                    <span>{activeConfig.active_model_name}</span>
                    <span className="text-[10px] text-[#9281f7] bg-[#9281f7]/15 px-1.5 py-0.2 rounded font-mono">
                      {activeConfig.active_provider}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Headline Numbers Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-8">
            <div className="p-4 rounded-[8px] bg-[#090a0c] border border-[#292d30]/80">
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#3ad389]">
                {stats.headline_tokens_monthly}
              </div>
              <div className="text-xs text-[#a1a4a5] mt-1">Free Monthly Token Pool</div>
            </div>
            <div className="p-4 rounded-[8px] bg-[#090a0c] border border-[#292d30]/80">
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#9281f7]">
                {stats.total_providers} Providers
              </div>
              <div className="text-xs text-[#a1a4a5] mt-1">34 Free AI Labs & Clouds</div>
            </div>
            <div className="p-4 rounded-[8px] bg-[#090a0c] border border-[#292d30]/80">
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#ffffff]">
                {stats.total_model_endpoints} Endpoints
              </div>
              <div className="text-xs text-[#a1a4a5] mt-1">Frontier, Reasoning & Vision</div>
            </div>
            <div className="p-4 rounded-[8px] bg-[#090a0c] border border-[#292d30]/80">
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#38bdf8]">
                {stats.fastest_tps}
              </div>
              <div className="text-xs text-[#a1a4a5] mt-1">Peak Inference Speed</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 border-b border-[#292d30] pb-4 mb-8 overflow-x-auto">
          <button
            onClick={() => setActiveTab("catalog")}
            className={`px-4 py-2 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
              activeTab === "catalog"
                ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                : "text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1a1c1e]"
            }`}
          >
            <Layers className="h-3.5 w-3.5 text-[#9281f7]" />
            <span>Model Catalog & Explorer</span>
            <span className="text-[10px] bg-[#292d30] px-1.5 py-0.2 rounded text-[#a1a4a5]">
              {models.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("providers")}
            className={`px-4 py-2 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
              activeTab === "providers"
                ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                : "text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1a1c1e]"
            }`}
          >
            <Database className="h-3.5 w-3.5 text-[#3ad389]" />
            <span>Free Tier Knowledge Base</span>
            <span className="text-[10px] bg-[#3ad389]/20 text-[#3ad389] px-1.5 py-0.2 rounded font-mono">
              34 Free Tiers
            </span>
          </button>

          <button
            onClick={() => setActiveTab("config")}
            className={`px-4 py-2 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
              activeTab === "config"
                ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                : "text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1a1c1e]"
            }`}
          >
            <Key className="h-3.5 w-3.5 text-[#eab308]" />
            <span>AI Engine Credentials & Routing</span>
            {activeConfig?.has_api_key && (
              <span className="h-2 w-2 rounded-full bg-[#3ad389]" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("playground")}
            className={`px-4 py-2 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all ${
              activeTab === "playground"
                ? "bg-[#9281f7]/20 border border-[#9281f7]/40 text-[#ffffff] font-medium"
                : "text-[#a1a4a5] hover:text-[#ffffff] hover:bg-[#1a1c1e]"
            }`}
          >
            <Play className="h-3.5 w-3.5 text-[#38bdf8]" />
            <span>Model Connectivity Playground</span>
          </button>
        </div>

        {/* TAB 1: MODEL CATALOG & EXPLORER */}
        {activeTab === "catalog" && (
          <div className="space-y-6">
            {/* Search and Filters Bar */}
            <div className="p-4 rounded-[10px] bg-[#0c0d0f] border border-[#292d30] space-y-4">
              <div className="flex flex-col sm:flex-row items-center gap-3">
                {/* Search Input */}
                <div className="relative flex-1 w-full">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#a1a4a5]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by model name (e.g. Gemini 2.5, Llama 3.3, Qwen Coder, DeepSeek)..."
                    className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] pl-9 pr-4 py-2 text-xs text-[#ffffff] placeholder-[#666] focus:outline-none focus:border-[#9281f7]"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-3 top-2.5 text-xs text-[#a1a4a5] hover:text-[#ffffff]"
                    >
                      ×
                    </button>
                  )}
                </div>

                {/* Provider Dropdown */}
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#ffffff] focus:outline-none focus:border-[#9281f7] w-full sm:w-auto"
                >
                  <option value="all">All Providers ({providers.length})</option>
                  {providers.map((p) => (
                    <option key={p.platform} value={p.platform}>
                      {p.name}
                    </option>
                  ))}
                </select>

                {/* Sort Order */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#ffffff] focus:outline-none focus:border-[#9281f7] w-full sm:w-auto"
                >
                  <option value="smartest">Smartest (Intelligence Rank)</option>
                  <option value="fastest">Fastest (Wafer/LPU Speed)</option>
                  <option value="context">Largest Context Window</option>
                  <option value="free_budget">Highest Free Monthly Tokens</option>
                </select>
              </div>

              {/* Capability Filters Pills */}
              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#1f2326]">
                <span className="text-[11px] font-mono text-[#a1a4a5] flex items-center gap-1 mr-1">
                  <Filter className="h-3 w-3" /> Filters:
                </span>
                {CAPABILITY_FILTERS.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedCapability(f.id)}
                    className={`px-2.5 py-1 rounded-[6px] text-[11px] font-mono transition-all ${
                      selectedCapability === f.id
                        ? "bg-[#9281f7]/25 text-[#ffffff] border border-[#9281f7]"
                        : "bg-[#16181a] text-[#a1a4a5] hover:text-[#ffffff] border border-[#292d30]"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}

                {/* Context Buckets */}
                <div className="flex items-center gap-1 ml-auto">
                  <span className="text-[11px] font-mono text-[#a1a4a5] mr-1">Context:</span>
                  {CTX_BUCKETS.map((b) => (
                    <button
                      key={b.key}
                      onClick={() => setMinContext(b.key)}
                      className={`px-2 py-0.5 rounded-[4px] text-[10px] font-mono transition-all ${
                        minContext === b.key
                          ? "bg-[#38bdf8]/20 text-[#38bdf8] border border-[#38bdf8]/50"
                          : "text-[#a1a4a5] hover:text-[#ffffff] bg-[#16181a]"
                      }`}
                    >
                      {b.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Results Count Banner */}
            <div className="flex items-center justify-between text-xs text-[#a1a4a5] font-mono px-1">
              <span>Showing {filteredModels.length} models</span>
              <span>100% OpenAI Wire Compatible</span>
            </div>

            {/* Models Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredModels.map((model) => {
                const isActive = activeConfig?.active_model_id === model.id;
                return (
                  <div
                    key={model.id}
                    className={`rounded-[10px] bg-[#0c0d0f] border transition-all flex flex-col justify-between p-5 relative overflow-hidden group ${
                      isActive
                        ? "border-[#3ad389] shadow-[0_0_20px_rgba(58,211,137,0.15)]"
                        : "border-[#292d30] hover:border-[#9281f7]/60"
                    }`}
                  >
                    {isActive && (
                      <div className="absolute top-0 right-0 bg-[#3ad389] text-[#000000] text-[10px] font-mono font-bold px-2 py-0.5 rounded-bl-[6px]">
                        ACTIVE SYNTHESIS
                      </div>
                    )}

                    <div>
                      {/* Top Badges */}
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="text-[11px] font-mono text-[#9281f7] bg-[#9281f7]/10 px-2 py-0.5 rounded border border-[#9281f7]/30">
                          {model.provider_name}
                        </span>
                        <span className="text-[10px] font-mono text-[#a1a4a5] bg-[#16181a] px-2 py-0.5 rounded border border-[#292d30]">
                          {(model.context_window / 1000).toFixed(0)}K Context
                        </span>
                      </div>

                      {/* Model Name and ID */}
                      <h3 className="text-base font-semibold text-[#ffffff] group-hover:text-[#9281f7] transition-colors">
                        {model.display_name}
                      </h3>
                      <div className="text-[11px] font-mono text-[#a1a4a5] mt-0.5 break-all">
                        {model.model_id}
                      </div>

                      <p className="text-xs text-[#a1a4a5] mt-3 line-clamp-2 leading-relaxed">
                        {model.recommended_use}
                      </p>

                      {/* Capabilities and Ranks */}
                      <div className="mt-4 pt-3 border-t border-[#1f2326] space-y-2">
                        {/* Monthly Free Budget */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-[#a1a4a5] font-mono text-[11px]">Free Allowance:</span>
                          <span className="text-[#3ad389] font-mono font-medium">
                            {model.monthly_token_budget}
                          </span>
                        </div>

                        {/* Rate limits */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-[#a1a4a5] font-mono text-[11px]">Rate Limits:</span>
                          <span className="text-[#ffffff] font-mono text-[11px]">
                            {model.rpm_limit ? `${model.rpm_limit} RPM` : "Uncapped"}
                            {model.rpd_limit ? ` · ${model.rpd_limit} RPD` : ""}
                          </span>
                        </div>

                        {/* Speed & Intel Badges */}
                        <div className="flex items-center gap-2 pt-1">
                          <div className="flex-1 bg-[#16181a] px-2 py-1 rounded text-center">
                            <div className="text-[9px] text-[#a1a4a5] font-mono uppercase">Speed</div>
                            <div className="text-xs font-mono font-bold text-[#38bdf8]">
                              {model.speed_rank <= 2 ? "⚡ Ultra" : `Tier ${model.speed_rank}`}
                            </div>
                          </div>
                          <div className="flex-1 bg-[#16181a] px-2 py-1 rounded text-center">
                            <div className="text-[9px] text-[#a1a4a5] font-mono uppercase">Intel</div>
                            <div className="text-xs font-mono font-bold text-[#9281f7]">
                              {model.size_label}
                            </div>
                          </div>
                          {model.is_reasoning && (
                            <div className="flex-1 bg-[#9281f7]/15 px-2 py-1 rounded text-center border border-[#9281f7]/30">
                              <div className="text-[9px] text-[#9281f7] font-mono uppercase">Reasoning</div>
                              <div className="text-xs font-mono font-bold text-[#ffffff]">🧠 Deep</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="mt-5 pt-3 border-t border-[#1f2326]">
                      <button
                        onClick={() => handleSelectModel(model)}
                        disabled={isActive}
                        className={`w-full py-2 px-3 rounded-[6px] text-xs font-mono flex items-center justify-center gap-2 transition-all ${
                          isActive
                            ? "bg-[#3ad389]/15 text-[#3ad389] border border-[#3ad389]/40 cursor-default"
                            : "bg-[#111315] hover:bg-[#9281f7] text-[#ffffff] hover:text-[#000000] border border-[#292d30] hover:border-[#9281f7]"
                        }`}
                      >
                        {isActive ? (
                          <>
                            <Check className="h-3.5 w-3.5" />
                            <span>Currently Active Model</span>
                          </>
                        ) : (
                          <>
                            <Zap className="h-3.5 w-3.5" />
                            <span>Set as Synthesis Model</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: FREE TIER KNOWLEDGE BASE */}
        {activeTab === "providers" && (
          <div className="space-y-6">
            <div className="p-4 rounded-[8px] bg-[#0c0d0f] border border-[#292d30]">
              <h2 className="text-base font-semibold text-[#ffffff] flex items-center gap-2">
                <Database className="h-4 w-4 text-[#3ad389]" />
                34 Free LLM Providers Encyclopedia
              </h2>
              <p className="text-xs text-[#a1a4a5] mt-1">
                Verified free-tier quotas, signup links, zero-credit-card onboarding guides, and rate-limit guardrails.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {providers.map((p) => (
                <div
                  key={p.platform}
                  className="rounded-[10px] bg-[#0c0d0f] border border-[#292d30] p-5 hover:border-[#3ad389]/60 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-semibold text-[#ffffff]">{p.name}</h3>
                        {!p.requires_credit_card && (
                          <span className="text-[10px] font-mono text-[#3ad389] bg-[#3ad389]/15 px-2 py-0.5 rounded border border-[#3ad389]/30">
                            100% No Card Required
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#a1a4a5] mt-1.5">{p.description}</p>
                    </div>
                    {p.key_url && (
                      <a
                        href={p.key_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 rounded-[6px] bg-[#16181a] border border-[#292d30] hover:border-[#ffffff] text-[#a1a4a5] hover:text-[#ffffff] transition-colors shrink-0"
                        title="Get API Key"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>

                  <div className="mt-4 space-y-2.5 text-xs">
                    <div className="p-2.5 rounded-[6px] bg-[#16181a] border border-[#1f2326]">
                      <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">Monthly Free Allowance</div>
                      <div className="text-xs font-mono font-medium text-[#3ad389] mt-0.5">
                        {p.monthly_free_tokens}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-[6px] bg-[#16181a] border border-[#1f2326]">
                      <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">Rate Limits</div>
                      <div className="text-xs font-mono text-[#ffffff] mt-0.5">
                        {p.rate_limit_summary}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-[6px] bg-[#16181a] border border-[#1f2326]">
                      <div className="text-[10px] font-mono uppercase text-[#a1a4a5]">Setup Instructions</div>
                      <div className="text-xs text-[#a1a4a5] mt-0.5 leading-relaxed">
                        {p.key_setup_guide}
                      </div>
                    </div>

                    {p.gotchas_and_tips && (
                      <div className="p-2.5 rounded-[6px] bg-[#eab308]/10 border border-[#eab308]/30">
                        <div className="text-[10px] font-mono uppercase text-[#eab308] flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> Pro Tip & Gotchas
                        </div>
                        <div className="text-xs text-[#ffffff] mt-0.5 leading-relaxed">
                          {p.gotchas_and_tips}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: AI CREDENTIALS & ROUTING */}
        {activeTab === "config" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="p-5 rounded-[10px] bg-[#0c0d0f] border border-[#292d30]">
              <h2 className="text-base font-semibold text-[#ffffff] flex items-center gap-2">
                <Key className="h-4 w-4 text-[#eab308]" />
                PulseRadar AI Engine Credentials & Routing
              </h2>
              <p className="text-xs text-[#a1a4a5] mt-1">
                Configure your API keys or connect to a local FreeLLMAPI Unified Gateway to route inference across all 34 free providers.
              </p>

              <form onSubmit={handleSaveConfig} className="mt-6 space-y-5">
                {/* Active Synthesis Model Display */}
                <div>
                  <label className="block text-xs font-mono text-[#a1a4a5] mb-1">
                    Currently Selected Synthesis Model
                  </label>
                  <input
                    type="text"
                    disabled
                    value={`${activeConfig?.active_model_name || "Llama 3.3 70B"} (${activeConfig?.active_model_id || "groq/llama-3.3-70b-versatile"})`}
                    className="w-full bg-[#16181a] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#a1a4a5] cursor-not-allowed font-mono"
                  />
                  <span className="text-[11px] text-[#a1a4a5] mt-1 block">
                    To change this model, pick any model from the <strong>Model Catalog</strong> tab.
                  </span>
                </div>

                {/* FreeLLMAPI Gateway Switch */}
                <div className="p-3.5 rounded-[8px] bg-[#16181a] border border-[#292d30] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-[#ffffff] flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-[#3ad389]" />
                        <span>Route Through FreeLLMAPI Gateway</span>
                      </div>
                      <div className="text-[11px] text-[#a1a4a5]">
                        Auto-balances requests across all 34 providers via your local FreeLLMAPI instance.
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={useGateway}
                      onChange={(e) => setUseGateway(e.target.checked)}
                      className="h-4 w-4 rounded accent-[#9281f7] cursor-pointer"
                    />
                  </div>

                  {useGateway && (
                    <div className="space-y-3 pt-2 border-t border-[#292d30]">
                      <div>
                        <label className="block text-[11px] font-mono text-[#a1a4a5] mb-1">
                          FreeLLMAPI Gateway Base URL
                        </label>
                        <input
                          type="text"
                          value={gatewayUrlInput}
                          onChange={(e) => setGatewayUrlInput(e.target.value)}
                          placeholder="http://localhost:3001/v1"
                          className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#ffffff] font-mono focus:outline-none focus:border-[#9281f7]"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-mono text-[#a1a4a5] mb-1">
                          FreeLLMAPI Unified Token (Optional)
                        </label>
                        <input
                          type="password"
                          value={gatewayTokenInput}
                          onChange={(e) => setGatewayTokenInput(e.target.value)}
                          placeholder={activeConfig?.masked_freellmapi_token || "freellmapi-..."}
                          className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#ffffff] font-mono focus:outline-none focus:border-[#9281f7]"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Direct Provider API Key */}
                {!useGateway && (
                  <div>
                    <label className="block text-xs font-mono text-[#a1a4a5] mb-1">
                      Provider API Key ({activeConfig?.active_provider || "active provider"})
                    </label>
                    <div className="relative">
                      <input
                        type={showKey ? "text" : "password"}
                        value={apiKeyInput}
                        onChange={(e) => setApiKeyInput(e.target.value)}
                        placeholder={activeConfig?.masked_api_key || "Enter your provider API key..."}
                        className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] pl-3 pr-10 py-2 text-xs text-[#ffffff] font-mono focus:outline-none focus:border-[#9281f7]"
                      />
                      <button
                        type="button"
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-3 top-2.5 text-[#a1a4a5] hover:text-[#ffffff]"
                      >
                        {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <span className="text-[11px] text-[#a1a4a5] mt-1 block">
                      Stored encrypted locally on your server. Never shared with third parties.
                    </span>
                  </div>
                )}

                {/* Routing Strategy */}
                <div>
                  <label className="block text-xs font-mono text-[#a1a4a5] mb-1">
                    Smart Routing Strategy
                  </label>
                  <select
                    value={strategyInput}
                    onChange={(e) => setStrategyInput(e.target.value)}
                    className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] px-3 py-2 text-xs text-[#ffffff] focus:outline-none focus:border-[#9281f7]"
                  >
                    <option value="balanced">Balanced (Prioritizes reliability with speed & intelligence)</option>
                    <option value="smartest">Smartest (Frontier reasoning for deep PRD analysis)</option>
                    <option value="fastest">Fastest (Wafer/LPU ultra-low latency &lt;200ms TTFB)</option>
                    <option value="free_quota">Free Quota Maximizer (Routes to highest remaining free allowance)</option>
                  </select>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={configSaving}
                  className="w-full py-2.5 px-4 rounded-[6px] bg-[#9281f7] hover:bg-[#806ff5] text-[#000000] font-semibold text-xs font-mono flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  {configSaving ? (
                    <>
                      <RotateCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Saving Credentials...</span>
                    </>
                  ) : (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      <span>Save AI Credentials & Settings</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TAB 4: PLAYGROUND & TESTER */}
        {activeTab === "playground" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="p-5 rounded-[10px] bg-[#0c0d0f] border border-[#292d30]">
              <h2 className="text-base font-semibold text-[#ffffff] flex items-center gap-2">
                <Play className="h-4 w-4 text-[#38bdf8]" />
                Live Model Connectivity Playground
              </h2>
              <p className="text-xs text-[#a1a4a5] mt-1">
                Test prompt inference against your currently active model endpoint to verify latency and tokens.
              </p>

              <div className="mt-5 space-y-4">
                <div>
                  <label className="block text-xs font-mono text-[#a1a4a5] mb-1">
                    Test Prompt
                  </label>
                  <textarea
                    rows={3}
                    value={playgroundPrompt}
                    onChange={(e) => setPlaygroundPrompt(e.target.value)}
                    className="w-full bg-[#000000] border border-[#292d30] rounded-[6px] p-3 text-xs text-[#ffffff] focus:outline-none focus:border-[#38bdf8]"
                  />
                </div>

                <button
                  onClick={handleRunPlayground}
                  disabled={playgroundLoading}
                  className="py-2.5 px-4 rounded-[6px] bg-[#38bdf8] hover:bg-[#0ea5e9] text-[#000000] font-semibold text-xs font-mono flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  {playgroundLoading ? (
                    <>
                      <RotateCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Executing Inference...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5 fill-current" />
                      <span>Run Test Inference</span>
                    </>
                  )}
                </button>

                {playgroundResult && (
                  <div className="mt-4 p-4 rounded-[8px] bg-[#16181a] border border-[#292d30] space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono border-b border-[#292d30] pb-2">
                      <span className="flex items-center gap-1.5">
                        <span
                          className={`h-2 w-2 rounded-full ${
                            playgroundResult.status === "success" ? "bg-[#3ad389]" : "bg-red-500"
                          }`}
                        />
                        Status: <strong>{playgroundResult.status?.toUpperCase()}</strong>
                      </span>
                      {playgroundResult.latency_ms && (
                        <span className="text-[#38bdf8]">
                          Latency: {playgroundResult.latency_ms} ms
                        </span>
                      )}
                    </div>

                    {playgroundResult.response && (
                      <div>
                        <div className="text-[10px] font-mono uppercase text-[#a1a4a5] mb-1">
                          Model Response Output:
                        </div>
                        <div className="text-xs text-[#ffffff] leading-relaxed whitespace-pre-wrap bg-[#000000] p-3 rounded border border-[#292d30]">
                          {playgroundResult.response}
                        </div>
                      </div>
                    )}

                    {playgroundResult.error && (
                      <div className="text-xs text-red-400 bg-red-950/20 p-3 rounded border border-red-800/40">
                        {playgroundResult.error}
                      </div>
                    )}

                    <div className="text-[10px] font-mono text-[#a1a4a5] flex items-center justify-between pt-1">
                      <span>Endpoint: {playgroundResult.endpoint_tested}</span>
                      <span>Served Model: {playgroundResult.served_model}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
