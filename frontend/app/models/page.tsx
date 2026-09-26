"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
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
  Compass,
  Plus,
  Trash2,
  Send,
  MessageSquare,
  RefreshCw,
  X,
  Settings2,
  BarChart2,
  Image as ImageIcon,
  Video,
  Volume2,
  Radio,
  Share2,
  Bot,
  Paperclip,
  ChevronDown,
  ArrowUp,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen
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
  modality: string;
}

interface ProviderItem {
  platform: string;
  name: string;
  description: string;
  is_keyless: boolean;
  has_key: boolean;
  masked_key: string;
  status: "healthy" | "needs_key" | "keyless" | "disabled";
  enabled: boolean;
  signup_url: string;
  key_url: string;
  rate_limit_summary: string;
  monthly_free_tokens: string;
  free_tier_models_count: number;
  default_base_url: string;
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

interface UsageMetrics {
  tokens_this_month: number;
  requests_today: number;
  per_model_usage: Record<string, number>;
  headline: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  latency_ms?: number;
  model_used?: string;
}

interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  messages: ChatMessage[];
  modelId: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

const CTX_BUCKETS = [
  { key: 0, label: "Any Context" },
  { key: 32_000, label: "32K+" },
  { key: 128_000, label: "128K+" },
  { key: 1_000_000, label: "1M+ Frontier" },
];

const MODALITY_TABS = [
  { id: "chat", label: "Chat models", icon: MessageSquare },
  { id: "embedding", label: "Embeddings", icon: Layers },
  { id: "image", label: "Image", icon: ImageIcon },
  { id: "video", label: "Video", icon: Video },
  { id: "audio", label: "Audio", icon: Volume2 },
  { id: "fusion", label: "Fusion", icon: Radio },
  { id: "keys", label: "Keys & Quotas", icon: Key },
  { id: "playground", label: "Playground", icon: Play },
  { id: "providers", label: "Providers Guide", icon: Database },
];

const CAPABILITY_FILTERS = [
  { id: "all", label: "All Capabilities", icon: Layers },
  { id: "reasoning", label: "🧠 Reasoning", icon: Brain },
  { id: "speed", label: "⚡ Ultra-Fast (>800 tps)", icon: Zap },
  { id: "tools", label: "⚙️ Tools / Function Calling", icon: Sliders },
  { id: "vision", label: "👁️ Vision", icon: Eye },
  { id: "coding", label: "💻 Specialized Code", icon: Cpu },
  { id: "massive_context", label: "🌊 1M+ Context", icon: Compass },
];

export default function AIModelsPage() {
  const [activeTab, setActiveTab] = useState<string>("chat");
  
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
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Active Config State
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [updatingConfig, setUpdatingConfig] = useState(false);
  const [configSuccess, setConfigSuccess] = useState<string | null>(null);

  // Usage Telemetry State
  const [usage, setUsage] = useState<UsageMetrics>({
    tokens_this_month: 0,
    requests_today: 0,
    per_model_usage: {},
    headline: "0 tok this month · 0 req today"
  });

  // Keys Manager State
  const [keyProviders, setKeyProviders] = useState<ProviderItem[]>([]);
  const [keyFilter, setKeyFilter] = useState<"all" | "healthy" | "needs_key" | "disabled">("all");
  const [keySearch, setKeySearch] = useState("");
  const [checkingAllKeys, setCheckingAllKeys] = useState(false);
  const [testingKeyPlatform, setTestingKeyPlatform] = useState<string | null>(null);
  const [keyTestResults, setKeyTestResults] = useState<Record<string, { status: string; latency_ms?: number; message?: string }>>({});
  
  // Add/Edit Key Modal
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [modalPlatform, setModalPlatform] = useState("");
  const [modalApiKey, setModalApiKey] = useState("");
  const [modalBaseUrl, setModalBaseUrl] = useState("");
  const [savingKey, setSavingKey] = useState(false);

  // Conversational Playground State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string>("");
  const [composerInput, setComposerInput] = useState("");
  const [playgroundModelId, setPlaygroundModelId] = useState("groq/llama-3.3-70b-versatile");
  const [playgroundSystemPrompt, setPlaygroundSystemPrompt] = useState("You are an expert Chief Product Officer helping analyze product opportunities, features, and user discovery.");
  const [playgroundTemperature, setPlaygroundTemperature] = useState(0.4);
  const [playgroundMaxTokens, setPlaygroundMaxTokens] = useState(1000);
  const [playgroundTopP, setPlaygroundTopP] = useState(0.9);
  const [tempEnabled, setTempEnabled] = useState(false);
  const [topPEnabled, setTopPEnabled] = useState(false);
  const [maxTokensEnabled, setMaxTokensEnabled] = useState(false);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);
  const [isModelSearchOpen, setIsModelSearchOpen] = useState(false);
  const [modelSearchFilter, setModelSearchFilter] = useState("");
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [testingEndpoint, setTestingEndpoint] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Fetch Catalog & Config on Load
  useEffect(() => {
    fetchCatalog();
    fetchConfig();
    fetchUsage();
    fetchKeys();
    loadConversations();
  }, []);

  // Filter Catalog by Modality when tab changes
  useEffect(() => {
    if (["chat", "embedding", "image", "video", "audio", "fusion"].includes(activeTab)) {
      fetchCatalog(activeTab);
    }
  }, [activeTab, searchQuery, selectedProvider, selectedCapability, minContext, freeOnly, sortBy]);

  // Scroll to bottom of chat
  useEffect(() => {
    if (activeTab === "playground") {
      chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [conversations, activeConversationId, activeTab]);

  const fetchCatalog = async (modality = activeTab) => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchQuery) params.set("q", searchQuery);
      if (selectedProvider !== "all") params.set("provider", selectedProvider);
      if (selectedCapability !== "all") params.set("capability", selectedCapability);
      if (minContext > 0) params.set("min_context", minContext.toString());
      if (freeOnly) params.set("free_only", "true");
      params.set("sort_by", sortBy);
      if (["chat", "embedding", "image", "video", "audio", "fusion"].includes(modality)) {
        params.set("modality", modality);
      }

      const res = await fetch(`${BACKEND_URL}/api/v1/models?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch (e) {
      console.error("Failed to load models:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        if (data.active_model_id) {
          setPlaygroundModelId(data.active_model_id);
        }
      }
    } catch (e) {
      console.error("Failed to fetch active config:", e);
    }
  };

  const fetchUsage = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/usage`);
      if (res.ok) {
        const data = await res.json();
        setUsage(data);
      }
    } catch (e) {
      console.error("Failed to fetch usage metrics:", e);
    }
  };

  const fetchKeys = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/keys`);
      if (res.ok) {
        const data = await res.json();
        setKeyProviders(data.providers || []);
      }
    } catch (e) {
      console.error("Failed to fetch provider keys:", e);
    }
  };

  // LocalStorage Conversations Management
  const loadConversations = () => {
    try {
      const stored = localStorage.getItem("pulseradar_playground_conversations");
      if (stored) {
        const parsed: Conversation[] = JSON.parse(stored);
        setConversations(parsed);
        if (parsed.length > 0) {
          setActiveConversationId(parsed[0].id);
        } else {
          createNewConversation();
        }
      } else {
        createNewConversation();
      }
    } catch (e) {
      console.error("Error loading conversations:", e);
      createNewConversation();
    }
  };

  const saveConversations = (convs: Conversation[]) => {
    setConversations(convs);
    try {
      localStorage.setItem("pulseradar_playground_conversations", JSON.stringify(convs));
    } catch (e) {
      console.error("Error saving conversations:", e);
    }
  };

  const createNewConversation = () => {
    const newId = "conv_" + Date.now();
    const newConv: Conversation = {
      id: newId,
      title: "New Product Session",
      createdAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      messages: [
        {
          id: "msg_init",
          role: "assistant",
          content: "👋 Hello! I am your AI Product Architect. Ask me to draft a PRD, unpack friction from user reviews, compare market rivals, or generate feature prioritization matrices.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          model_used: playgroundModelId
        }
      ],
      modelId: playgroundModelId
    };
    const updated = [newConv, ...conversations];
    saveConversations(updated);
    setActiveConversationId(newId);
  };

  const deleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const filtered = conversations.filter(c => c.id !== id);
    saveConversations(filtered);
    if (activeConversationId === id) {
      if (filtered.length > 0) {
        setActiveConversationId(filtered[0].id);
      } else {
        createNewConversation();
      }
    }
  };

  const activeConversation = useMemo(() => {
    return conversations.find(c => c.id === activeConversationId) || conversations[0];
  }, [conversations, activeConversationId]);

  // Send Message in Playground
  const handleSendMessage = async () => {
    if (!composerInput.trim() || isSendingMessage) return;

    const userText = composerInput.trim();
    setComposerInput("");

    const userMsg: ChatMessage = {
      id: "usr_" + Date.now(),
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    // Update conversation immediately with user message
    const updatedMessages = [...(activeConversation?.messages || []), userMsg];
    const updatedTitle = activeConversation?.messages.length <= 1 ? userText.slice(0, 32) + "..." : activeConversation?.title || "Product Session";
    
    const updatedConvs = conversations.map(c => {
      if (c.id === activeConversation?.id) {
        return { ...c, title: updatedTitle, messages: updatedMessages, modelId: playgroundModelId };
      }
      return c;
    });
    saveConversations(updatedConvs);
    setIsSendingMessage(true);

    const payloadMessages = updatedMessages.map(m => ({ role: m.role, content: m.content }));

    try {
      const payload: any = {
        messages: payloadMessages,
        model_id: playgroundModelId,
        system_prompt: playgroundSystemPrompt
      };
      if (tempEnabled) {
        payload.temperature = playgroundTemperature;
      }
      if (maxTokensEnabled) {
        payload.max_tokens = playgroundMaxTokens;
      }

      const res = await fetch(`${BACKEND_URL}/api/v1/models/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || "Inference failed");
      }

      const resData = await res.json();
      const botMsg: ChatMessage = {
        id: "bot_" + Date.now(),
        role: "assistant",
        content: resData.message?.content || "No response received.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        latency_ms: resData.latency_ms,
        model_used: resData.model_id
      };

      const finalConvs = conversations.map(c => {
        if (c.id === activeConversation?.id) {
          return { ...c, messages: [...updatedMessages, botMsg] };
        }
        return c;
      });
      saveConversations(finalConvs);
      fetchUsage(); // Refresh usage telemetry counter
    } catch (e: any) {
      const errMsg: ChatMessage = {
        id: "err_" + Date.now(),
        role: "assistant",
        content: `⚠️ Error calling ${playgroundModelId}: ${e.message}. Please check credentials in the Keys & Quotas tab.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      const finalConvs = conversations.map(c => {
        if (c.id === activeConversation?.id) {
          return { ...c, messages: [...updatedMessages, errMsg] };
        }
        return c;
      });
      saveConversations(finalConvs);
    } finally {
      setIsSendingMessage(false);
    }
  };

  // Set Active Model in Backend
  const handleSetActiveEngine = async (model: ModelEndpoint) => {
    try {
      setUpdatingConfig(true);
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
        setConfig(data.config);
        setPlaygroundModelId(model.id);
        setConfigSuccess(`Activated ${model.display_name} as primary synthesis engine!`);
        setTimeout(() => setConfigSuccess(null), 4000);
      }
    } catch (e) {
      console.error("Failed to update active model:", e);
    } finally {
      setUpdatingConfig(false);
    }
  };

  // Toggle Provider
  const handleToggleProvider = async (platform: string, enabled: boolean) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/models/keys/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, enabled })
      });
      if (res.ok) {
        fetchKeys();
      }
    } catch (e) {
      console.error("Failed to toggle provider:", e);
    }
  };

  // Test Single Provider Key
  const handleTestKey = async (platform: string) => {
    try {
      setTestingKeyPlatform(platform);
      const res = await fetch(`${BACKEND_URL}/api/v1/models/keys/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform })
      });
      const data = await res.json();
      setKeyTestResults(prev => ({
        ...prev,
        [platform]: {
          status: data.status,
          latency_ms: data.latency_ms,
          message: data.status === "success" ? `200 OK (${data.latency_ms}ms)` : (data.error || data.message || "Failed")
        }
      }));
      fetchUsage();
    } catch (e: any) {
      setKeyTestResults(prev => ({
        ...prev,
        [platform]: { status: "error", message: e.message }
      }));
    } finally {
      setTestingKeyPlatform(null);
    }
  };

  // Check All Keys
  const handleCheckAllKeys = async () => {
    try {
      setCheckingAllKeys(true);
      const res = await fetch(`${BACKEND_URL}/api/v1/models/keys/check-all`, { method: "POST" });
      if (res.ok) {
        fetchKeys();
      }
    } catch (e) {
      console.error("Failed to check all keys:", e);
    } finally {
      setCheckingAllKeys(false);
    }
  };

  // Save Key Modal Submit
  const handleSaveKeySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalPlatform) return;
    try {
      setSavingKey(true);
      const res = await fetch(`${BACKEND_URL}/api/v1/models/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: modalPlatform,
          api_key: modalApiKey,
          base_url: modalBaseUrl || undefined
        })
      });
      if (res.ok) {
        setIsKeyModalOpen(false);
        setModalApiKey("");
        setModalBaseUrl("");
        fetchKeys();
        fetchConfig();
      }
    } catch (e) {
      console.error("Failed to save key:", e);
    } finally {
      setSavingKey(false);
    }
  };

  // Filtered Keys list
  const filteredKeyProviders = useMemo(() => {
    return keyProviders.filter(p => {
      if (keyFilter === "healthy" && p.status !== "healthy" && p.status !== "keyless") return false;
      if (keyFilter === "needs_key" && p.status !== "needs_key") return false;
      if (keyFilter === "disabled" && p.status !== "disabled") return false;
      if (keySearch) {
        const q = keySearch.toLowerCase();
        return p.name.toLowerCase().includes(q) || p.platform.toLowerCase().includes(q) || p.description.toLowerCase().includes(q);
      }
      return true;
    });
  }, [keyProviders, keyFilter, keySearch]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const selectedModel = useMemo(() => {
    return models.find(m => m.id === playgroundModelId) || null;
  }, [models, playgroundModelId]);

  const filteredModelsForPicker = useMemo(() => {
    if (!modelSearchFilter.trim()) return models;
    const q = modelSearchFilter.toLowerCase();
    return models.filter(m =>
      m.display_name.toLowerCase().includes(q) ||
      m.id.toLowerCase().includes(q) ||
      m.platform.toLowerCase().includes(q) ||
      m.provider_name.toLowerCase().includes(q)
    );
  }, [models, modelSearchFilter]);

  // DEDICATED FULL-SCREEN PLAYGROUND STUDIO (Matching Screenshot 2026-09-26 230854 & 230901)
  if (activeTab === "playground") {
    return (
      <div className="h-screen w-screen overflow-hidden flex flex-col bg-[#07080c] text-slate-100 select-none">
        {/* Sleek Top Navigation Bar (Only ~44px height, leaves 93%+ vertical space to the playground) */}
        <header className="h-11 border-b border-slate-800/80 bg-slate-950/95 px-3 flex items-center justify-between shrink-0 z-30">
          <div className="flex items-center space-x-3 overflow-x-auto no-scrollbar">
            <Link href="/" className="flex items-center space-x-1.5 text-slate-400 hover:text-white transition shrink-0">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white tracking-tight">PulseRadar</span>
            </Link>
            <span className="text-slate-800">|</span>
            <nav className="flex items-center space-x-1 shrink-0">
              {MODALITY_TABS.map(tab => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-md transition ${
                      isActive
                        ? "bg-cyan-500/10 text-cyan-400 font-semibold border border-cyan-500/30"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            {config && (
              <div className="hidden lg:flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px]">
                <span className="text-slate-500">Pipeline Engine:</span>
                <span className="font-semibold text-cyan-400">{config.active_model_name}</span>
                <span className="text-slate-600">({config.active_provider})</span>
              </div>
            )}
            <Link
              href="/"
              className="px-2.5 py-1 text-xs rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition flex items-center space-x-1"
            >
              <span>Product Research</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
            <Link
              href="/seo"
              className="px-2.5 py-1 text-xs rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition"
            >
              SEO Studio
            </Link>
          </div>
        </header>

        {/* 3-Column Edge-to-Edge Playground Layout (Matching Screenshot 2026-09-26 230854 & 230901) */}
        <div className="flex-1 min-h-0 w-full flex overflow-hidden relative">
          {/* Column 1: Conversations Sidebar (Collapsible) */}
          {isLeftSidebarOpen ? (
            <aside className="w-64 border-r border-slate-800/80 bg-slate-950/70 flex flex-col shrink-0 select-none">
              <div className="h-10 px-3 border-b border-slate-800/60 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300 tracking-wide">Conversations</span>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={createNewConversation}
                    className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition"
                    title="New Conversation"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setIsLeftSidebarOpen(false)}
                    className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition"
                    title="Collapse sidebar"
                  >
                    <PanelLeftClose className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {conversations.map(c => {
                  const isCur = c.id === activeConversation?.id;
                  return (
                    <div
                      key={c.id}
                      onClick={() => setActiveConversationId(c.id)}
                      className={`p-2.5 rounded-xl cursor-pointer transition text-xs flex items-center justify-between group ${
                        isCur
                          ? "bg-slate-800/90 text-white font-medium border border-slate-700/80 shadow-sm"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                      }`}
                    >
                      <div className="flex flex-col truncate pr-2">
                        <span className="truncate font-medium">{c.title || "New Chat"}</span>
                        <span className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {c.createdAt || "just now"} · {c.messages?.length || 0} messages
                        </span>
                      </div>
                      <button
                        onClick={e => deleteConversation(c.id, e)}
                        className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 p-1 transition"
                        title="Delete conversation"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </aside>
          ) : (
            <button
              onClick={() => setIsLeftSidebarOpen(true)}
              className="absolute left-2.5 top-2.5 z-20 p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white shadow-xl transition"
              title="Expand Conversations"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          )}

          {/* Column 2: Center Chat Testing Viewport */}
          <main className="flex-1 min-h-0 flex flex-col bg-[#050608] relative">
            {/* Top Subheader: "Playground · <Model Name>" */}
            <div className="h-10 px-4 border-b border-slate-800/60 bg-slate-950/40 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-2 text-xs">
                <span className="font-bold text-white tracking-tight">Playground</span>
                <span className="text-slate-600">·</span>
                <span className="text-cyan-400 font-semibold truncate max-w-xs md:max-w-md">
                  {selectedModel?.display_name || playgroundModelId.split("/").pop()}
                </span>
                <span className="text-[10px] text-slate-400 font-mono px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800">
                  {selectedModel?.provider_name || playgroundModelId.split("/")[0]}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    const finalConvs = conversations.map(c => {
                      if (c.id === activeConversation?.id) {
                        return { ...c, messages: [] };
                      }
                      return c;
                    });
                    saveConversations(finalConvs);
                  }}
                  className="text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded hover:bg-slate-800/60 transition"
                >
                  Clear Chat
                </button>
                {!isRightSidebarOpen && (
                  <button
                    onClick={() => setIsRightSidebarOpen(true)}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition"
                    title="Open Settings"
                  >
                    <PanelRightOpen className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Chat Message Stream (Independent scrolling, NO parent page scroll!) */}
            <div className="flex-1 overflow-y-auto px-4 md:px-12 py-6 space-y-4">
              {(!activeConversation?.messages || activeConversation.messages.length === 0) ? (
                <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-2 select-none py-28">
                  <h3 className="text-lg font-bold text-white">Send a message to get started.</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Using {selectedModel?.display_name || playgroundModelId}. Switch models in the selector on the right panel.
                  </p>
                </div>
              ) : (
                activeConversation.messages.map(msg => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                        msg.role === "user"
                          ? "bg-cyan-600 text-white shadow-md shadow-cyan-950/20 rounded-br-sm"
                          : "bg-slate-900/95 text-slate-200 border border-slate-800 shadow-md rounded-bl-sm whitespace-pre-wrap font-sans"
                      }`}
                    >
                      {msg.content}
                    </div>

                    <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-500 px-1 font-mono">
                      <span>{msg.timestamp}</span>
                      {msg.latency_ms && <span>· {msg.latency_ms} ms</span>}
                      {msg.model_used && <span>· {msg.model_used.split("/").pop()}</span>}
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="hover:text-slate-300 transition ml-1"
                        title="Copy text"
                      >
                        {copiedId === msg.id ? <Check className="w-3 h-3 text-emerald-400 inline" /> : <Copy className="w-3 h-3 inline" />}
                      </button>
                    </div>
                  </div>
                ))
              )}

              {isSendingMessage && (
                <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/80 p-3 rounded-xl border border-slate-800/80 w-max shadow">
                  <RotateCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                  <span>Inference running on {selectedModel?.display_name || playgroundModelId}...</span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Bottom Input Box matching Screenshot 2026-09-26 230854 */}
            <div className="p-4 border-t border-slate-800/60 bg-[#050608] shrink-0">
              <form
                onSubmit={e => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="max-w-4xl mx-auto flex items-center bg-[#0d0f15] border border-slate-800 hover:border-slate-700 focus-within:border-cyan-500/80 rounded-2xl px-3.5 py-2 shadow-2xl transition gap-2"
              >
                <button
                  type="button"
                  className="p-1 text-slate-500 hover:text-slate-300 transition"
                  title="Insert Product Research prompt"
                  onClick={() => setComposerInput("Identify the top 3 friction points and developer mental models for Prisma vs Drizzle.")}
                >
                  <Paperclip className="w-4 h-4" />
                </button>

                <textarea
                  rows={1}
                  value={composerInput}
                  onChange={e => setComposerInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Type a message... (↵ to send, ⇧↵ for newline)"
                  className="flex-1 bg-transparent border-0 outline-none text-xs text-slate-100 placeholder-slate-500 resize-none px-2 py-1 max-h-32"
                />

                <button
                  type="submit"
                  disabled={!composerInput.trim() || isSendingMessage}
                  className="w-8 h-8 rounded-full bg-slate-800 hover:bg-cyan-600 disabled:opacity-30 disabled:hover:bg-slate-800 text-white flex items-center justify-center transition shadow shrink-0"
                  title="Send message (Enter)"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
              </form>
            </div>
          </main>

          {/* Column 3: Settings Sidebar (Matching Screenshot 2026-09-26 230854 & 230901) */}
          {isRightSidebarOpen && (
            <aside className="w-80 border-l border-slate-800/80 bg-slate-950/70 flex flex-col shrink-0 overflow-y-auto p-4 space-y-5 text-xs relative select-none">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="font-semibold text-slate-200">Settings</span>
                <button
                  onClick={() => setIsRightSidebarOpen(false)}
                  className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition"
                  title="Collapse Settings"
                >
                  <PanelRightClose className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Model Selector Combobox (Matching Screenshot 230901) */}
              <div className="relative">
                <label className="text-[11px] font-semibold text-slate-300 block mb-1.5">Model</label>
                <button
                  type="button"
                  onClick={() => setIsModelSearchOpen(!isModelSearchOpen)}
                  className="w-full flex items-center justify-between bg-[#10121a] border border-slate-700/80 hover:border-slate-500 rounded-xl px-3 py-2 text-white font-medium text-xs transition shadow-inner"
                >
                  <span className="truncate">{selectedModel?.display_name || playgroundModelId}</span>
                  <ChevronDown className={`w-4 h-4 text-slate-400 shrink-0 ml-2 transition-transform duration-150 ${isModelSearchOpen ? "rotate-180" : ""}`} />
                </button>

                {/* Popover Dropdown matching Screenshot 230901 */}
                {isModelSearchOpen && (
                  <div className="absolute top-full left-0 right-0 mt-1.5 z-50 bg-[#0d0f17] border border-slate-700 rounded-xl shadow-2xl p-2 space-y-2 animate-in fade-in zoom-in-95 duration-100 backdrop-blur-md">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search models..."
                        value={modelSearchFilter}
                        onChange={e => setModelSearchFilter(e.target.value)}
                        autoFocus
                        className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-950/90 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-0.5 text-xs pr-1 divide-y divide-slate-800/40">
                      <div className="pb-1 space-y-0.5">
                        <button
                          onClick={() => {
                            setPlaygroundModelId("groq/llama-3.3-70b-versatile");
                            setIsModelSearchOpen(false);
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg flex items-center justify-between text-left text-slate-200 hover:bg-slate-800 transition"
                        >
                          <span className="font-semibold text-cyan-400">Auto (fallback chain)</span>
                          <span className="text-[10px] text-slate-500 font-mono">smart-route</span>
                        </button>
                        <button
                          onClick={() => {
                            setPlaygroundModelId("google/gemini-flash-latest");
                            setIsModelSearchOpen(false);
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg flex items-center justify-between text-left text-slate-200 hover:bg-slate-800 transition"
                        >
                          <span className="font-semibold text-indigo-400">Fusion (multi-model synthesis)</span>
                          <span className="text-[10px] text-slate-500 font-mono">ensemble</span>
                        </button>
                      </div>

                      <div className="pt-1 space-y-0.5">
                        {filteredModelsForPicker.slice(0, 50).map(m => {
                          const isCur = m.id === playgroundModelId;
                          return (
                            <button
                              key={m.id}
                              onClick={() => {
                                setPlaygroundModelId(m.id);
                                setIsModelSearchOpen(false);
                              }}
                              className={`w-full px-2.5 py-1.5 rounded-lg flex items-center justify-between text-left transition ${
                                isCur
                                  ? "bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30"
                                  : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                              }`}
                            >
                              <span className="truncate pr-2 font-medium">{m.display_name}</span>
                              <span className="text-[10px] text-slate-400 font-mono shrink-0 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                                {m.platform}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* System Prompt */}
              <div>
                <label className="text-[11px] font-semibold text-slate-300 block mb-1.5">System prompt</label>
                <textarea
                  rows={4}
                  value={playgroundSystemPrompt}
                  onChange={e => setPlaygroundSystemPrompt(e.target.value)}
                  placeholder="Optional. Sent as a system message before your chat."
                  className="w-full bg-[#10121a] border border-slate-800 rounded-xl p-2.5 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-[11px] leading-relaxed resize-none font-mono"
                />
              </div>

              {/* Sampling Section (Matching Screenshot 2026-09-26 230854) */}
              <div className="space-y-4 pt-1">
                <div>
                  <h4 className="font-semibold text-slate-200">Sampling</h4>
                  <p className="text-[10px] text-slate-400 leading-tight mt-0.5">
                    Switched off, the provider's own default applies. Only the controls you switch on are sent.
                  </p>
                </div>

                {/* Temperature */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300 font-medium">Temperature</span>
                    <button
                      type="button"
                      onClick={() => setTempEnabled(!tempEnabled)}
                      className="flex items-center space-x-1.5 text-[11px] text-slate-400 hover:text-white"
                    >
                      <span className={tempEnabled ? "text-cyan-400 font-semibold" : "text-slate-500"}>
                        {tempEnabled ? playgroundTemperature.toFixed(2) : "Default"}
                      </span>
                      <span className={`w-7 h-4 rounded-full flex items-center px-0.5 transition ${tempEnabled ? "bg-cyan-600 justify-end" : "bg-slate-800 justify-start"}`}>
                        <span className="w-3 h-3 rounded-full bg-white shadow"></span>
                      </span>
                    </button>
                  </div>
                  {tempEnabled && (
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={playgroundTemperature}
                      onChange={e => setPlaygroundTemperature(parseFloat(e.target.value))}
                      className="w-full accent-cyan-500 cursor-pointer"
                    />
                  )}
                </div>

                {/* Top P */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300 font-medium">Top P</span>
                    <button
                      type="button"
                      onClick={() => setTopPEnabled(!topPEnabled)}
                      className="flex items-center space-x-1.5 text-[11px] text-slate-400 hover:text-white"
                    >
                      <span className={topPEnabled ? "text-cyan-400 font-semibold" : "text-slate-500"}>
                        {topPEnabled ? playgroundTopP.toFixed(2) : "Default"}
                      </span>
                      <span className={`w-7 h-4 rounded-full flex items-center px-0.5 transition ${topPEnabled ? "bg-cyan-600 justify-end" : "bg-slate-800 justify-start"}`}>
                        <span className="w-3 h-3 rounded-full bg-white shadow"></span>
                      </span>
                    </button>
                  </div>
                  {topPEnabled && (
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={playgroundTopP}
                      onChange={e => setPlaygroundTopP(parseFloat(e.target.value))}
                      className="w-full accent-cyan-500 cursor-pointer"
                    />
                  )}
                </div>

                {/* Max Tokens */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300 font-medium">Max tokens</span>
                    <button
                      type="button"
                      onClick={() => setMaxTokensEnabled(!maxTokensEnabled)}
                      className="flex items-center space-x-1.5 text-[11px] text-slate-400 hover:text-white"
                    >
                      <span className={maxTokensEnabled ? "text-cyan-400 font-semibold" : "text-slate-500"}>
                        {maxTokensEnabled ? "Custom" : "Default"}
                      </span>
                      <span className={`w-7 h-4 rounded-full flex items-center px-0.5 transition ${maxTokensEnabled ? "bg-cyan-600 justify-end" : "bg-slate-800 justify-start"}`}>
                        <span className="w-3 h-3 rounded-full bg-white shadow"></span>
                      </span>
                    </button>
                  </div>
                  <input
                    type="number"
                    value={playgroundMaxTokens}
                    disabled={!maxTokensEnabled}
                    onChange={e => setPlaygroundMaxTokens(parseInt(e.target.value) || 1024)}
                    className="w-full bg-[#10121a] border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 disabled:text-slate-600 disabled:border-slate-850 font-mono text-xs focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Set as Active Engine Button & Pipeline status */}
              {selectedModel && (
                <div className="pt-2 border-t border-slate-800/80 space-y-2">
                  <button
                    onClick={() => handleSetActiveEngine(selectedModel)}
                    disabled={updatingConfig}
                    className="w-full py-2 px-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition shadow flex items-center justify-center space-x-1.5 disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{updatingConfig ? "Activating..." : "Make Active for All Pipelines"}</span>
                  </button>
                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[10px] text-slate-400 space-y-1">
                    <div className="flex items-center space-x-1 text-emerald-400">
                      <Check className="w-3 h-3" />
                      <span>Product Research Query Planner</span>
                    </div>
                    <div className="flex items-center space-x-1 text-emerald-400">
                      <Check className="w-3 h-3" />
                      <span>Autonomous Browser Agent Navigation</span>
                    </div>
                    <div className="flex items-center space-x-1 text-emerald-400">
                      <Check className="w-3 h-3" />
                      <span>Generative Engine Optimization (GEO)</span>
                    </div>
                  </div>
                </div>
              )}
            </aside>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Top Banner & Header */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-tr from-cyan-600 via-indigo-600 to-violet-600 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold tracking-tight text-white">AI Models & Free Tier Studio</h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  7.4B tokens/mo
                </span>
              </div>
              <p className="text-xs text-slate-400">36 Providers · 635 Endpoints · Zero-Cost Developer Inference</p>
            </div>
          </div>

          {/* Active Model Pill */}
          {config && (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
              <span className="text-slate-400">Active Engine:</span>
              <span className="font-semibold text-cyan-400">{config.active_model_name}</span>
              <span className="text-slate-500">({config.active_provider})</span>
            </div>
          )}
        </div>

        {/* Multi-Modal Category Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto no-scrollbar space-x-1 border-t border-slate-800/60">
          {MODALITY_TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
                  isActive
                    ? "border-cyan-500 text-cyan-400 bg-cyan-950/20"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* Success Alert */}
        {configSuccess && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-950/50 border border-emerald-500/30 flex items-center justify-between text-emerald-300 text-sm animate-in fade-in duration-200">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{configSuccess}</span>
            </div>
            <button onClick={() => setConfigSuccess(null)} className="text-emerald-400 hover:text-emerald-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Live Monthly Usage & Telemetry Tracker (Matching Screenshot 1 & 2) */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-900/90 border border-slate-800/80 shadow-xl flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="p-2.5 bg-cyan-950/40 border border-cyan-500/20 rounded-xl text-cyan-400">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Monthly Usage</span>
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </div>
              <p className="text-base font-bold text-white tracking-tight">
                {usage.headline || `${usage.tokens_this_month.toLocaleString()} tok this month · ${usage.requests_today} req today`}
              </p>
            </div>
          </div>

          {/* Model Breakdown Badges */}
          <div className="flex flex-wrap items-center gap-2">
            {Object.keys(usage.per_model_usage || {}).length === 0 ? (
              <span className="text-xs text-slate-500 italic">No usage recorded today. Test in Playground to view live tracking.</span>
            ) : (
              Object.entries(usage.per_model_usage).slice(0, 4).map(([mod, cnt], idx) => (
                <span key={mod} className="px-2.5 py-1 text-xs rounded-full bg-slate-800/90 border border-slate-700 text-slate-300 flex items-center space-x-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${idx % 2 === 0 ? "bg-cyan-400" : "bg-indigo-400"}`}></span>
                  <span className="font-mono text-[11px] truncate max-w-[130px]">{mod.split("/").pop()}</span>
                  <span className="text-slate-400 font-semibold">{cnt.toLocaleString()} tok</span>
                </span>
              ))
            )}
            <button
              onClick={() => fetchUsage()}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
              title="Refresh Usage Stats"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* TAB 1-6: MODALITIES (Chat, Embeddings, Image, Video, Audio, Fusion) */}
        {["chat", "embedding", "image", "video", "audio", "fusion"].includes(activeTab) && (
          <div>
            {/* Filter Bar */}
            <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {/* Search Input */}
                <div className="relative md:col-span-2">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    placeholder={`Search ${activeTab} models by name, provider, or architecture...`}
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  />
                  {searchQuery && (
                    <button onClick={() => setSearchQuery("")} className="absolute right-3 top-3 text-slate-400 hover:text-slate-200">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Provider Selector */}
                <div>
                  <select
                    value={selectedProvider}
                    onChange={e => setSelectedProvider(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="all">All Providers (36 Available)</option>
                    <option value="google">Google AI Studio</option>
                    <option value="groq">Groq Cloud (Ultra-Fast)</option>
                    <option value="cerebras">Cerebras Wafer Engine</option>
                    <option value="openrouter">OpenRouter Free Pool</option>
                    <option value="github">GitHub Models (GPT-4o/4.1)</option>
                    <option value="mistral">Mistral AI</option>
                    <option value="cloudflare">Cloudflare Workers AI</option>
                    <option value="zhipu">Zhipu AI (GLM)</option>
                    <option value="kilo">Kilo (Keyless)</option>
                    <option value="pollinations">Pollinations (Keyless)</option>
                    <option value="ovh">OVHcloud (Keyless)</option>
                    <option value="siliconflow">SiliconFlow Media</option>
                    <option value="ollama">Ollama (Local GPU)</option>
                  </select>
                </div>

                {/* Sort Order */}
                <div>
                  <select
                    value={sortBy}
                    onChange={e => setSortBy(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="smartest">Sort: Smartest (SWE-Bench)</option>
                    <option value="fastest">Sort: Fastest (&gt;800 tok/s)</option>
                    <option value="context">Sort: Largest Context (1M+)</option>
                    <option value="free_budget">Sort: Largest Free Quota</option>
                  </select>
                </div>
              </div>

              {/* Sub-filter chips */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
                <div className="flex flex-wrap items-center gap-1.5">
                  {CAPABILITY_FILTERS.map(f => (
                    <button
                      key={f.id}
                      onClick={() => setSelectedCapability(f.id)}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                        selectedCapability === f.id
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                          : "bg-slate-800/40 text-slate-400 hover:text-slate-200 border border-transparent"
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center space-x-4 text-xs text-slate-400">
                  <label className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={freeOnly}
                      onChange={e => setFreeOnly(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-cyan-600 focus:ring-0"
                    />
                    <span>100% Cardless Free Tiers Only</span>
                  </label>
                  <span>{models.length} endpoints</span>
                </div>
              </div>
            </div>

            {/* Models Grid */}
            {loading ? (
              <div className="py-20 text-center space-y-3">
                <RotateCw className="w-7 h-7 text-cyan-400 animate-spin mx-auto" />
                <p className="text-xs text-slate-400">Querying 635 endpoints across 36 providers...</p>
              </div>
            ) : models.length === 0 ? (
              <div className="py-20 text-center space-y-3 bg-slate-900/30 rounded-2xl border border-slate-800/60">
                <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
                <h3 className="text-sm font-semibold text-white">No models match your current filters</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Try clearing the search query or selecting "All Providers" to view the full endpoint catalog.
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedProvider("all");
                    setSelectedCapability("all");
                  }}
                  className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                >
                  Reset All Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {models.map(m => {
                  const isActive = config?.active_model_id === m.id;
                  return (
                    <div
                      key={m.id}
                      className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                        isActive
                          ? "bg-slate-900/90 border-cyan-500/60 shadow-lg shadow-cyan-950/30 ring-1 ring-cyan-500/30"
                          : "bg-slate-900/40 hover:bg-slate-900/70 border-slate-800/80 hover:border-slate-700"
                      }`}
                    >
                      <div>
                        {/* Provider & Modality Row */}
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[11px] font-semibold text-slate-400 tracking-wide uppercase">
                            {m.provider_name}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            m.size_label === "Frontier"
                              ? "bg-purple-950/60 text-purple-300 border border-purple-800/40"
                              : m.size_label === "Large"
                              ? "bg-blue-950/60 text-blue-300 border border-blue-800/40"
                              : "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                          }`}>
                            {m.size_label}
                          </span>
                        </div>

                        {/* Title & Copy */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="text-sm font-bold text-white tracking-tight group-hover:text-cyan-400">
                            {m.display_name}
                          </h3>
                          <button
                            onClick={() => copyToClipboard(m.id, m.id)}
                            className="text-slate-500 hover:text-slate-300 p-1"
                            title="Copy qualified Model ID"
                          >
                            {copiedId === m.id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>

                        {/* Recommended Use */}
                        <p className="text-xs text-slate-400 mb-3 line-clamp-2 leading-relaxed">
                          {m.recommended_use}
                        </p>

                        {/* Badges Bar */}
                        <div className="flex flex-wrap gap-1.5 mb-3 text-[11px]">
                          <span className="px-2 py-0.5 rounded bg-slate-800/90 text-cyan-300 border border-slate-700/60">
                            {m.context_window >= 1_000_000
                              ? `${(m.context_window / 1_000_000).toFixed(1)}M ctx`
                              : `${(m.context_window / 1024).toFixed(0)}K ctx`}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate-800/90 text-emerald-300 border border-slate-700/60 font-mono">
                            {m.monthly_token_budget}
                          </span>
                          {m.rpm_limit && (
                            <span className="px-2 py-0.5 rounded bg-slate-800/90 text-slate-400 border border-slate-700/60">
                              {m.rpm_limit} RPM
                            </span>
                          )}
                          {m.is_reasoning && (
                            <span className="px-1.5 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/40 font-semibold">
                              🧠 Reasoning
                            </span>
                          )}
                          {m.supports_vision && (
                            <span className="px-1.5 py-0.5 rounded bg-indigo-950/40 text-indigo-300 border border-indigo-800/40 font-semibold">
                              👁️ Vision
                            </span>
                          )}
                          {m.is_coding && (
                            <span className="px-1.5 py-0.5 rounded bg-cyan-950/40 text-cyan-300 border border-cyan-800/40 font-semibold">
                              💻 Code
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Card Action Buttons */}
                      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2 mt-auto">
                        <button
                          onClick={() => {
                            setPlaygroundModelId(m.id);
                            setActiveTab("playground");
                          }}
                          className="px-2.5 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 rounded-lg flex items-center space-x-1 transition"
                        >
                          <Play className="w-3 h-3 text-cyan-400" />
                          <span>Playground</span>
                        </button>

                        <button
                          onClick={() => handleSetActiveEngine(m)}
                          disabled={isActive || updatingConfig}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition flex items-center space-x-1.5 ${
                            isActive
                              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 cursor-default"
                              : "bg-cyan-600 hover:bg-cyan-500 text-white shadow-md shadow-cyan-900/20"
                          }`}
                        >
                          {isActive ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                              <span>Active Primary</span>
                            </>
                          ) : (
                            <>
                              <Zap className="w-3.5 h-3.5" />
                              <span>Set Primary</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 7: KEYS & QUOTAS MANAGER (Matching Screenshot 5) */}
        {activeTab === "keys" && (
          <div className="space-y-6">
            {/* Header Action Bar */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center space-x-2">
                <span className="text-xs text-slate-400">Filter Status:</span>
                {(["all", "healthy", "needs_key", "disabled"] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setKeyFilter(f)}
                    className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                      keyFilter === f
                        ? "bg-cyan-600 text-white shadow-md shadow-cyan-900/30"
                        : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {f === "all" ? `All (${keyProviders.length})` : 
                     f === "healthy" ? `Healthy (${keyProviders.filter(p => p.status === "healthy" || p.status === "keyless").length})` :
                     f === "needs_key" ? `Needs Key (${keyProviders.filter(p => p.status === "needs_key").length})` :
                     `Disabled (${keyProviders.filter(p => p.status === "disabled").length})`}
                  </button>
                ))}
              </div>

              <div className="flex items-center space-x-2">
                {/* Search Bar */}
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search provider..."
                    value={keySearch}
                    onChange={e => setKeySearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500 w-44"
                  />
                </div>

                <button
                  onClick={handleCheckAllKeys}
                  disabled={checkingAllKeys}
                  className="px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg flex items-center space-x-1.5 transition"
                >
                  <RotateCw className={`w-3.5 h-3.5 ${checkingAllKeys ? "animate-spin text-cyan-400" : ""}`} />
                  <span>{checkingAllKeys ? "Checking..." : "Check all"}</span>
                </button>

                <button
                  onClick={() => {
                    setModalPlatform(keyProviders[0]?.platform || "google");
                    setIsKeyModalOpen(true);
                  }}
                  className="px-3 py-1.5 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 rounded-lg flex items-center space-x-1.5 shadow-md shadow-cyan-900/20 transition"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add key</span>
                </button>
              </div>
            </div>

            {/* Provider Credential Cards List (Matching Screenshot 5) */}
            <div className="space-y-3">
              {filteredKeyProviders.map(p => {
                const testRes = keyTestResults[p.platform];
                const isTesting = testingKeyPlatform === p.platform;

                return (
                  <div
                    key={p.platform}
                    className="p-4 rounded-xl bg-slate-900/40 hover:bg-slate-900/70 border border-slate-800 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    {/* Left: Provider Info & Toggle */}
                    <div className="flex items-start md:items-center space-x-3.5">
                      {/* Toggle Switch */}
                      <button
                        onClick={() => handleToggleProvider(p.platform, !p.enabled)}
                        className={`w-9 h-5 rounded-full transition-colors relative flex-shrink-0 mt-0.5 md:mt-0 ${
                          p.enabled ? "bg-cyan-600" : "bg-slate-700"
                        }`}
                        title={p.enabled ? "Click to disable provider" : "Click to enable provider"}
                      >
                        <div
                          className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${
                            p.enabled ? "left-4.5 translate-x-3.5" : "left-0.5"
                          }`}
                        />
                      </button>

                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-bold text-white">{p.name}</h4>
                          {/* Status Pill */}
                          {p.status === "healthy" && (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              ● 1 healthy
                            </span>
                          )}
                          {p.status === "keyless" && (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              ● Keyless
                            </span>
                          )}
                          {p.status === "needs_key" && (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              Needs key
                            </span>
                          )}
                          {p.status === "disabled" && (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-800 text-slate-500 border border-slate-700">
                              Disabled
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{p.rate_limit_summary}</p>
                      </div>
                    </div>

                    {/* Middle: Masked Key Snippet */}
                    <div className="flex items-center space-x-2 font-mono text-xs text-slate-400 bg-slate-950/70 px-3 py-1.5 rounded-lg border border-slate-800/80">
                      <Key className="w-3.5 h-3.5 text-slate-500" />
                      <span>{p.masked_key}</span>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center space-x-2">
                      {testRes && (
                        <span className={`text-xs px-2 py-1 rounded font-mono ${
                          testRes.status === "success" ? "text-emerald-400 bg-emerald-950/40" : "text-amber-400 bg-amber-950/40"
                        }`}>
                          {testRes.message}
                        </span>
                      )}

                      <button
                        onClick={() => handleTestKey(p.platform)}
                        disabled={isTesting}
                        className="px-2.5 py-1 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition"
                      >
                        {isTesting ? "Testing..." : "Test Key"}
                      </button>

                      <button
                        onClick={() => {
                          setModalPlatform(p.platform);
                          setIsKeyModalOpen(true);
                        }}
                        className="px-2.5 py-1 text-xs text-cyan-400 bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-500/30 rounded-lg transition"
                      >
                        Edit Key
                      </button>

                      {p.key_url && (
                        <a
                          href={p.key_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                          title="Get API Key from provider portal"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 8: CONVERSATIONAL PLAYGROUND is rendered as full-screen dedicated studio above */}

        {/* TAB 9: PROVIDERS KNOWLEDGE BASE GUIDE */}
        {activeTab === "providers" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {keyProviders.map(p => (
              <div key={p.platform} className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">{p.name}</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {p.monthly_free_tokens}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{p.description}</p>
                <div className="p-2.5 rounded-lg bg-slate-950 text-xs font-mono text-slate-300 border border-slate-800/80">
                  {p.rate_limit_summary}
                </div>
                {p.key_url && (
                  <a
                    href={p.key_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 text-xs text-cyan-400 hover:underline"
                  >
                    <span>Developer Key Portal</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add / Edit Key Modal Dialog */}
      {isKeyModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Key className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">Add Provider Credential</h3>
              </div>
              <button onClick={() => setIsKeyModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveKeySubmit} className="space-y-4 text-xs">
              <div>
                <label className="text-slate-400 block mb-1 font-medium">Inference Provider</label>
                <select
                  value={modalPlatform}
                  onChange={e => setModalPlatform(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  {keyProviders.map(p => (
                    <option key={p.platform} value={p.platform}>
                      {p.name} ({p.is_keyless ? "Keyless" : "Requires Key"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 font-medium">API Key / Token</label>
                <input
                  type="password"
                  placeholder="Paste Bearer key or PAT..."
                  value={modalApiKey}
                  onChange={e => setModalApiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Keys are stored encrypted locally. Zero payment card required for free accounts.
                </span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 font-medium">Base URL Override (Optional)</label>
                <input
                  type="text"
                  placeholder="https://api.../v1"
                  value={modalBaseUrl}
                  onChange={e => setModalBaseUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="pt-2 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsKeyModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingKey}
                  className="px-4 py-2 rounded-lg text-white font-semibold bg-cyan-600 hover:bg-cyan-500 transition shadow"
                >
                  {savingKey ? "Saving..." : "Save Credential"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
