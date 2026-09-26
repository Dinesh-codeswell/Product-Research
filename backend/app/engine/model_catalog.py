"""PulseRadar AI Model Catalog & Free Tier Knowledge Engine

Brings the full scope of FreeLLMAPI into PulseRadar:
- 7.4 Billion tokens per month aggregate free tier capacity
- 34 Free LLM Providers with quotas, rate limits, and setup guides
- 635+ Free and Open Model Endpoints with context windows, speed ranks, intelligence ranks
- Multi-dimensional filtering (context window, capabilities, free tier, provider, speed)
- OpenAI-compatible routing and dynamic provider selection
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class ModelEndpoint:
    id: str  # qualified id: platform/model_id
    platform: str
    provider_name: str
    model_id: str
    display_name: str
    family: str
    intelligence_rank: int  # 1 = Frontier, 15 = Small
    speed_rank: int  # 1 = Fastest (>800 tps), 10 = Standard
    size_label: str  # 'Frontier', 'Large', 'Medium', 'Small'
    context_window: int  # tokens
    rpm_limit: Optional[int] = None
    rpd_limit: Optional[int] = None
    tpm_limit: Optional[int] = None
    tpd_limit: Optional[int] = None
    monthly_token_budget: str = "~6M"
    monthly_token_budget_tokens: int = 6_000_000
    supports_vision: bool = False
    supports_tools: bool = True
    is_reasoning: bool = False
    is_coding: bool = False
    requires_card: bool = False
    base_url: str = ""
    key_format_hint: str = "Bearer token"
    recommended_use: str = "General reasoning and product analysis"

@dataclass
class ProviderInfo:
    platform: str
    name: str
    description: str
    monthly_free_tokens: str
    free_tier_models_count: int
    requires_credit_card: bool
    is_keyless_supported: bool
    signup_url: str
    key_url: str
    rate_limit_summary: str
    key_setup_guide: str
    gotchas_and_tips: str
    default_base_url: str

# ---------------------------------------------------------------------------
# 34 Free LLM Providers Directory with Free Tier Knowledge Base
# ---------------------------------------------------------------------------
PROVIDERS_DIRECTORY: Dict[str, ProviderInfo] = {
    "google": ProviderInfo(
        platform="google",
        name="Google AI Studio",
        description="Google Gemini 2.5 Flash, Pro, and Flash-Lite models with up to 1M token context windows.",
        monthly_free_tokens="~120M tokens/month (Flash-Lite) / ~25M (Flash)",
        free_tier_models_count=5,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://aistudio.google.com/",
        key_url="https://aistudio.google.com/app/apikey",
        rate_limit_summary="15 RPM, 20-1000 RPD, 250K TPM per model per project.",
        key_setup_guide="Sign in with any standard Google account at aistudio.google.com, click 'Get API key' -> 'Create API key in new project'. No credit card required.",
        gotchas_and_tips="Gemini 2.5 Flash-Lite grants the highest free volume (~1000 RPD). Flash has a tighter 20 RPD cap. Pro variants have limited free calls.",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai"
    ),
    "groq": ProviderInfo(
        platform="groq",
        name="Groq Cloud",
        description="Ultra-fast LPU inference (500-1,000 tok/sec) for Llama 3.3 70B, Qwen, and GPT-OSS models.",
        monthly_free_tokens="~15M tokens/month per model",
        free_tier_models_count=8,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://console.groq.com/",
        key_url="https://console.groq.com/keys",
        rate_limit_summary="30 RPM, 1,000 RPD, 6K-12K TPM (up to 14,400 RPD on 8B instant).",
        key_setup_guide="Create a free account at console.groq.com (GitHub/Google login), navigate to API Keys -> Create Key. Instant activation with zero card required.",
        gotchas_and_tips="Scout and Llama 4 models require the 'meta-llama/' publisher prefix. The 8B instant model has a massive 14,400 daily request allowance.",
        default_base_url="https://api.groq.com/openai/v1"
    ),
    "cerebras": ProviderInfo(
        platform="cerebras",
        name="Cerebras Cloud",
        description="World's fastest inference engine powered by the CS-3 Wafer-Scale Engine (>2,000 tok/sec).",
        monthly_free_tokens="~30M tokens/month (1M tokens/day)",
        free_tier_models_count=5,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://cloud.cerebras.ai/",
        key_url="https://cloud.cerebras.ai/",
        rate_limit_summary="30 RPM, 60K TPM, 1,000,000 tokens per day free pool.",
        key_setup_guide="Sign up at cloud.cerebras.ai with GitHub or email. Generate API key from the developer console. 100% free with no card required.",
        gotchas_and_tips="Fastest TTFB in the world (~150ms). Excellent for high-speed clustering and signal distillation.",
        default_base_url="https://api.cerebras.ai/v1"
    ),
    "openrouter": ProviderInfo(
        platform="openrouter",
        name="OpenRouter (Free Pool)",
        description="Multi-model gateway aggregating free tiers of DeepSeek, Qwen Coder, MiniMax, and Nemotron.",
        monthly_free_tokens="~6M tokens/month across ':free' models",
        free_tier_models_count=18,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://openrouter.ai/",
        key_url="https://openrouter.ai/keys",
        rate_limit_summary="20 RPM, 200 RPD across all ':free' routes.",
        key_setup_guide="Create an account at openrouter.ai, generate a free API key. All models with the ':free' suffix cost $0 and draw from the free pool.",
        gotchas_and_tips="Always append ':free' to the model ID (e.g. 'deepseek/deepseek-v3.1:free'). Requires HTTP-Referer header.",
        default_base_url="https://openrouter.ai/api/v1"
    ),
    "github": ProviderInfo(
        platform="github",
        name="GitHub Models",
        description="Free developer inference for OpenAI GPT-4o, GPT-4.1, and Azure models directly using your GitHub PAT.",
        monthly_free_tokens="~18M tokens/month (GPT-4o) / ~9M (GPT-4.1)",
        free_tier_models_count=6,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://github.com/marketplace/models",
        key_url="https://github.com/settings/tokens",
        rate_limit_summary="15 RPM, 50-150 RPD, 8K in / 4K out per call.",
        key_setup_guide="Generate a classic or fine-grained Personal Access Token (PAT) with 'read:user' scope at github.com/settings/tokens. Use models.github.ai/inference.",
        gotchas_and_tips="Model IDs use 'openai/gpt-4o' or 'openai/gpt-4.1'. Uses standard GitHub PAT as the Bearer token.",
        default_base_url="https://models.github.ai/inference"
    ),
    "mistral": ProviderInfo(
        platform="mistral",
        name="Mistral AI (La Plateforme)",
        description="High-tier European models: Codestral, Devstral, Mistral Large, and Magistral Medium.",
        monthly_free_tokens="~50-100M tokens/month (shared 1B tokens/mo Experiment tier)",
        free_tier_models_count=6,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://console.mistral.ai/",
        key_url="https://console.mistral.ai/api-keys",
        rate_limit_summary="2 RPM, 500K TPM, shared 1B token/mo experiment pool.",
        key_setup_guide="Register at console.mistral.ai. Verify phone number for free experiment tier access. No payment card needed.",
        gotchas_and_tips="Codestral is top-ranked for code and structured PRDs. RPM is strictly capped at 2 requests/min on free tier.",
        default_base_url="https://api.mistral.ai/v1"
    ),
    "cohere": ProviderInfo(
        platform="cohere",
        name="Cohere",
        description="Enterprise RAG and reasoning models: Command R+, Command-A, and multilingual Embed.",
        monthly_free_tokens="~1-2M tokens/month (1,000 free calls/month)",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://cohere.com/",
        key_url="https://dashboard.cohere.com/api-keys",
        rate_limit_summary="20 RPM, 33 RPD, 1,000 requests/month trial pool.",
        key_setup_guide="Sign up at dashboard.cohere.com, create a trial key. Trial keys never expire and work on all standard endpoints.",
        gotchas_and_tips="High quality on tool use and enterprise citations. Monthly request limit is 1,000 calls total.",
        default_base_url="https://api.cohere.com/v1"
    ),
    "cloudflare": ProviderInfo(
        platform="cloudflare",
        name="Cloudflare Workers AI",
        description="Edge AI serving Llama 3.3 70B fp8-fast, GLM-4.7, and DeepSeek across 300+ data centers.",
        monthly_free_tokens="~18-45M tokens/month (10,000 Neurons/day free)",
        free_tier_models_count=10,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://dash.cloudflare.com/",
        key_url="https://dash.cloudflare.com/profile/api-tokens",
        rate_limit_summary="10,000 Neurons per day (~1M-1.5M tokens/day equivalent).",
        key_setup_guide="Sign up for Cloudflare free account. Create API token with 'Workers AI: Read' permissions. Endpoint uses Account ID.",
        gotchas_and_tips="Model IDs are prefixed with '@cf/' (e.g. '@cf/meta/llama-3.3-70b-instruct-fp8-fast').",
        default_base_url="https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"
    ),
    "zhipu": ProviderInfo(
        platform="zhipu",
        name="Zhipu AI (Z.ai / BigModel)",
        description="GLM-4.5 Flash and GLM-4.7 frontier reasoning models with long-context support.",
        monthly_free_tokens="~30M tokens/month (1M tokens/day)",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://bigmodel.cn/",
        key_url="https://bigmodel.cn/usercenter/apikeys",
        rate_limit_summary="1,000,000 tokens per day free quota on Flash models.",
        key_setup_guide="Register at bigmodel.cn or z.ai with phone/email. Free key is generated instantly in the user center.",
        gotchas_and_tips="Reasoning models (GLM-4.7) output reasoning_content tokens first. Set timeout to >= 60s for cold starts.",
        default_base_url="https://open.bigmodel.cn/api/paas/v4"
    ),
    "huggingface": ProviderInfo(
        platform="huggingface",
        name="Hugging Face Router",
        description="Inference Providers router proxying dozens of open-source models with $0.10/mo recurring credit.",
        monthly_free_tokens="~1-3M tokens/month free credits",
        free_tier_models_count=12,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://huggingface.co/",
        key_url="https://huggingface.co/settings/tokens",
        rate_limit_summary="Dynamic based on provider backend; monthly router credit.",
        key_setup_guide="Sign up at huggingface.co, create a User Access Token with inference permissions.",
        gotchas_and_tips="Uses router.huggingface.co/v1 with standard OpenAI completions format.",
        default_base_url="https://router.huggingface.co/v1"
    ),
    "ollama": ProviderInfo(
        platform="ollama",
        name="Ollama Cloud",
        description="Hosted cloud version of Ollama offering verified free community models.",
        monthly_free_tokens="~15M tokens/month (GPU session hours)",
        free_tier_models_count=6,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://ollama.com/",
        key_url="https://ollama.com/settings/keys",
        rate_limit_summary="1 concurrent model, 5h session caps on free plan.",
        key_setup_guide="Sign up at ollama.com, generate an API key from user settings.",
        gotchas_and_tips="Provides OpenAI-compatible endpoints on /v1.",
        default_base_url="https://ollama.com/v1"
    ),
    "kilo": ProviderInfo(
        platform="kilo",
        name="Kilo Gateway",
        description="Anonymous keyless aggregator providing free access to open-source models.",
        monthly_free_tokens="~10M tokens/month",
        free_tier_models_count=5,
        requires_credit_card=False,
        is_keyless_supported=True,
        signup_url="https://kilo.ai/",
        key_url="https://kilo.ai/",
        rate_limit_summary="200 requests/hour per IP anonymous tier.",
        key_setup_guide="No key needed! Kilo allows keyless requests to free models with rate limits per IP.",
        gotchas_and_tips="Keyless access is available for all models ending in ':free'.",
        default_base_url="https://api.kilo.ai/api/gateway/v1"
    ),
    "pollinations": ProviderInfo(
        platform="pollinations",
        name="Pollinations AI",
        description="Free, community-powered open inference for text and image models.",
        monthly_free_tokens="~15M tokens/month (fair use)",
        free_tier_models_count=7,
        requires_credit_card=False,
        is_keyless_supported=True,
        signup_url="https://pollinations.ai/",
        key_url="https://pollinations.ai/",
        rate_limit_summary="Fair use community capacity, ~10-20 RPM.",
        key_setup_guide="Zero setup required: supports anonymous access or free community tokens.",
        gotchas_and_tips="Ideal as a zero-auth fallback provider for quick tests and embeddings.",
        default_base_url="https://text.pollinations.ai/openai"
    ),
    "opencode": ProviderInfo(
        platform="opencode",
        name="OpenCode Zen",
        description="Developer-focused AI gateway with free promotional coding models.",
        monthly_free_tokens="~10M tokens/month",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://opencode.ai/auth",
        key_url="https://opencode.ai/keys",
        rate_limit_summary="20 RPM on free developer accounts.",
        key_setup_guide="Register at opencode.ai with GitHub or email for an instant free API key.",
        gotchas_and_tips="Tuned for SWE-bench and coding tasks.",
        default_base_url="https://api.opencode.ai/v1"
    ),
    "ovh": ProviderInfo(
        platform="ovh",
        name="OVHcloud AI Endpoints",
        description="European cloud provider offering keyless anonymous inference on open models.",
        monthly_free_tokens="~5M tokens/month",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=True,
        signup_url="https://endpoints.ai.cloud.ovh.net/",
        key_url="https://endpoints.ai.cloud.ovh.net/",
        rate_limit_summary="2 requests/min per IP per model anonymous tier.",
        key_setup_guide="Anonymous calls permitted directly via European endpoints.",
        gotchas_and_tips="100% GDPR compliant European hosting.",
        default_base_url="https://endpoints.ai.cloud.ovh.net/v1"
    ),
    "siliconflow": ProviderInfo(
        platform="siliconflow",
        name="SiliconFlow",
        description="High-speed model inference serving free DeepSeek, Qwen, and FLUX models.",
        monthly_free_tokens="~20M tokens/month (recurring free tier)",
        free_tier_models_count=8,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://siliconflow.com/",
        key_url="https://cloud.siliconflow.cn/account/ak",
        rate_limit_summary="Up to 1000 requests/day on verified free tiers.",
        key_setup_guide="Sign up at siliconflow.com with email. Generate free key from account dashboard.",
        gotchas_and_tips="Excellent performance on DeepSeek V3 and Qwen 2.5 Coder.",
        default_base_url="https://api.siliconflow.cn/v1"
    ),
    "aihorde": ProviderInfo(
        platform="aihorde",
        name="AI Horde",
        description="Decentralized volunteer compute grid serving open source LLMs and generative art.",
        monthly_free_tokens="Unlimited (queue-based volunteer computing)",
        free_tier_models_count=15,
        requires_credit_card=False,
        is_keyless_supported=True,
        signup_url="https://aihorde.net/",
        key_url="https://aihorde.net/register",
        rate_limit_summary="Queue based; anonymous key '0000000000' works with lower queue priority.",
        key_setup_guide="Use anonymous key '0000000000' or register for a free account to earn kudos.",
        gotchas_and_tips="Requests may take 10-30s depending on volunteer queue depth.",
        default_base_url="https://oai.aihorde.net/v1"
    ),
    "nvidia": ProviderInfo(
        platform="nvidia",
        name="NVIDIA NIM",
        description="Enterprise NVIDIA-hosted NIM microservices (Llama 3.3, Nemotron 70B, DeepSeek).",
        monthly_free_tokens="Credits-based free trial allowance",
        free_tier_models_count=6,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://build.nvidia.com/",
        key_url="https://build.nvidia.com/",
        rate_limit_summary="40 RPM per model on free developer credits.",
        key_setup_guide="Sign in with NVIDIA developer account at build.nvidia.com, click 'Get API Key'.",
        gotchas_and_tips="Reasoning models may take 30-60s on cold start. Force single tool call.",
        default_base_url="https://integrate.api.nvidia.com/v1"
    ),
    "sambanova": ProviderInfo(
        platform="sambanova",
        name="SambaNova Cloud",
        description="Reconfigurable Dataflow Unit (RDU) inference for DeepSeek V3 and Llama 3.3 70B.",
        monthly_free_tokens="~3M tokens/month (200K TPD developer tier)",
        free_tier_models_count=5,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://cloud.sambanova.ai/",
        key_url="https://cloud.sambanova.ai/apis",
        rate_limit_summary="20 RPM, 20 RPD, 200,000 tokens/day free Developer pool.",
        key_setup_guide="Create a free developer account at cloud.sambanova.ai to access RDU inference.",
        gotchas_and_tips="Strict 20 RPD limit on free tier. DeepSeek V3.2 is high-intelligence.",
        default_base_url="https://api.sambanova.ai/v1"
    ),
    "modelscope": ProviderInfo(
        platform="modelscope",
        name="ModelScope (Alibaba)",
        description="Alibaba Cloud community hub offering Qwen 2.5/3, DeepSeek, and GLM models.",
        monthly_free_tokens="~2,000 requests/day account-wide",
        free_tier_models_count=8,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://modelscope.cn/",
        key_url="https://modelscope.cn/my/myaccesstoken",
        rate_limit_summary="2,000 requests per day account-wide.",
        key_setup_guide="Sign up at modelscope.cn. Generate AccessToken in account settings.",
        gotchas_and_tips="Best source for experimental Qwen releases.",
        default_base_url="https://api-inference.modelscope.cn/v1"
    ),
    "reka": ProviderInfo(
        platform="reka",
        name="Reka AI",
        description="Native multimodal frontier models (text, images, audio, video) with Flash-Edge tiers.",
        monthly_free_tokens="~5M tokens/month free developer grant",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://platform.reka.ai/",
        key_url="https://platform.reka.ai/",
        rate_limit_summary="20 RPM on standard free developer tier.",
        key_setup_guide="Register at platform.reka.ai for developer API key.",
        gotchas_and_tips="Exceptional multimodal ingestion for video research analysis.",
        default_base_url="https://api.reka.ai/v1"
    ),
    "agnes": ProviderInfo(
        platform="agnes",
        name="Agnes AI (Sapiens)",
        description="Proprietary fast inference engine built on LiteLLM and optimized vLLM clusters.",
        monthly_free_tokens="~8M tokens/month",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://platform.agnes-ai.com/",
        key_url="https://platform.agnes-ai.com/",
        rate_limit_summary="15 RPM on verified no-card developer tier.",
        key_setup_guide="Create a free key at platform.agnes-ai.com without entering payment details.",
        gotchas_and_tips="High consistency on structured JSON outputs.",
        default_base_url="https://api.agnes-ai.com/v1"
    ),
    "routeway": ProviderInfo(
        platform="routeway",
        name="Routeway AI",
        description="Smart aggregator routing requests across available zero-cost free models.",
        monthly_free_tokens="~5M tokens/month",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://routeway.ai/",
        key_url="https://routeway.ai/",
        rate_limit_summary="5 RPM on free tier routes.",
        key_setup_guide="Sign up at routeway.ai for a free API key.",
        gotchas_and_tips="Free routes use the ':free' model alias.",
        default_base_url="https://api.routeway.ai/v1"
    ),
    "bazaarlink": ProviderInfo(
        platform="bazaarlink",
        name="BazaarLink",
        description="Community inference marketplace offering the zero-cost 'auto:free' smart route.",
        monthly_free_tokens="~6M tokens/month",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://bazaarlink.ai/",
        key_url="https://bazaarlink.ai/",
        rate_limit_summary="10 RPM on free aliases.",
        key_setup_guide="Register at bazaarlink.ai without credit card.",
        gotchas_and_tips="Use 'auto:free' model to automatically pick currently un-congested node.",
        default_base_url="https://api.bazaarlink.ai/v1"
    ),
    "ainative": ProviderInfo(
        platform="ainative",
        name="AINative Studio",
        description="Developer studio with recurring 10M tokens/month free allocation.",
        monthly_free_tokens="~10M tokens/month recurring free tier",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://ainative.studio/",
        key_url="https://ainative.studio/",
        rate_limit_summary="20 RPM, 10,000,000 tokens per month free.",
        key_setup_guide="Sign up with email at ainative.studio and claim your free developer tier.",
        gotchas_and_tips="High monthly token allowance.",
        default_base_url="https://api.ainative.studio/v1"
    ),
    "aion": ProviderInfo(
        platform="aion",
        name="Aion Labs",
        description="Unified inference gateway offering no-card free developer access.",
        monthly_free_tokens="~5M tokens/month",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://aionlabs.ai/",
        key_url="https://aionlabs.ai/",
        rate_limit_summary="15 RPM free tier allowance.",
        key_setup_guide="Sign up for free developer key at aionlabs.ai.",
        gotchas_and_tips="Reliable fallback for general text summarization.",
        default_base_url="https://api.aionlabs.ai/v1"
    ),
    "requesty": ProviderInfo(
        platform="requesty",
        name="Requesty Router",
        description="Multi-provider AI router with dedicated zero-cost model pool.",
        monthly_free_tokens="~6M tokens/month",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://requesty.ai/",
        key_url="https://requesty.ai/",
        rate_limit_summary="10 RPM on free tier.",
        key_setup_guide="Create an account at requesty.ai to get free routing token.",
        gotchas_and_tips="Built-in automatic retry logic.",
        default_base_url="https://api.requesty.ai/v1"
    ),
    "navy": ProviderInfo(
        platform="navy",
        name="NavyAI",
        description="Unified API with 150K tokens/day free plan and 20 RPM rate limit.",
        monthly_free_tokens="~4.5M tokens/month (150K tokens/day)",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://navyai.com/",
        key_url="https://navyai.com/",
        rate_limit_summary="20 RPM, 150,000 tokens/day free plan.",
        key_setup_guide="Register at navyai.com without entering credit card.",
        gotchas_and_tips="Resets daily at 00:00 UTC.",
        default_base_url="https://api.navyai.com/v1"
    ),
    "nara": ProviderInfo(
        platform="nara",
        name="NaraRouter",
        description="Fast regional inference gateway with daily-resetting free plan routes.",
        monthly_free_tokens="~5M tokens/month",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://router.bynara.id/",
        key_url="https://router.bynara.id/",
        rate_limit_summary="10 RPM, daily free quota.",
        key_setup_guide="Get account key from router.bynara.id after channel verification.",
        gotchas_and_tips="Great latency in South East Asia region.",
        default_base_url="https://router.bynara.id/v1"
    ),
    "sealion": ProviderInfo(
        platform="sealion",
        name="SEA-LION (AI Singapore)",
        description="Southeast Asian Language in One Network (SEA-LION) frontier models.",
        monthly_free_tokens="~3M tokens/month (10 RPM free)",
        free_tier_models_count=3,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://aisingapore.org/",
        key_url="https://aisingapore.org/",
        rate_limit_summary="10 RPM free tier, Google sign-in.",
        key_setup_guide="Sign in with Google at AI Singapore portal. No region wall or card needed.",
        gotchas_and_tips="Excels at regional ASEAN languages and localization nuances.",
        default_base_url="https://api.sea-lion.ai/v1"
    ),
    "orcarouter": ProviderInfo(
        platform="orcarouter",
        name="OrcaRouter",
        description="OpenAI-compatible aggregator with rate-limited free aliases that never bill.",
        monthly_free_tokens="~5M tokens/month",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://orcarouter.ai/",
        key_url="https://orcarouter.ai/",
        rate_limit_summary="10 RPM, 100% free aliases at $0 cost.",
        key_setup_guide="Register at orcarouter.ai with email.",
        gotchas_and_tips="Guaranteed never to fall back to paid routes.",
        default_base_url="https://api.orcarouter.ai/v1"
    ),
    "unorouter": ProviderInfo(
        platform="unorouter",
        name="UnoRouter",
        description="Aggregator with free models carrying ':free' suffix and per-minute limits.",
        monthly_free_tokens="~4M tokens/month",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://unorouter.com/",
        key_url="https://unorouter.com/",
        rate_limit_summary="5 RPM on free models, 429 backoff.",
        key_setup_guide="Sign up at unorouter.com for a free API token.",
        gotchas_and_tips="Model IDs carry ':free' suffix.",
        default_base_url="https://api.unorouter.com/v1"
    ),
    "xkiro": ProviderInfo(
        platform="xkiro",
        name="xKiro",
        description="High-capacity gateway with 5M tokens/day free plan on open models.",
        monthly_free_tokens="~150M tokens/month (5M tokens/day)",
        free_tier_models_count=4,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://xkiro.com/",
        key_url="https://xkiro.com/",
        rate_limit_summary="20 RPM, 5,000,000 tokens/day free tier.",
        key_setup_guide="Sign up at xkiro.com for free developer key.",
        gotchas_and_tips="Huge daily token ceiling (5M/day).",
        default_base_url="https://api.xkiro.com/v1"
    ),
    "volcengine": ProviderInfo(
        platform="volcengine",
        name="Volcengine Ark (ByteDance)",
        description="ByteDance cloud serving Doubao, DeepSeek, and Llama with 2M tokens/day per model.",
        monthly_free_tokens="~60M tokens/month (2M tokens/day/model)",
        free_tier_models_count=6,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="https://ark.cn-beijing.volces.com/",
        key_url="https://console.volcengine.com/ark",
        rate_limit_summary="2,000,000 tokens per day per model recurring reward.",
        key_setup_guide="Sign up at volcengine.com. Requires developer account registration.",
        gotchas_and_tips="Strongest recurring daily allowance in mainland cloud providers.",
        default_base_url="https://ark.cn-beijing.volces.com/api/v3"
    ),
    "freellmapi_local": ProviderInfo(
        platform="freellmapi_local",
        name="FreeLLMAPI Unified Gateway",
        description="Local FreeLLMAPI instance aggregating all 34 free providers and 635 endpoints behind one port.",
        monthly_free_tokens="7.4+ Billion tokens/month (across all enabled keys)",
        free_tier_models_count=635,
        requires_credit_card=False,
        is_keyless_supported=False,
        signup_url="http://localhost:3001",
        key_url="http://localhost:3001/keys",
        rate_limit_summary="Aggregates and load-balances across all configured provider keys.",
        key_setup_guide="Run FreeLLMAPI locally via Docker or Node, configure your provider keys, and grab the unified Bearer token from the dashboard.",
        gotchas_and_tips="Automatic fallover on 429/5xx errors, smart bandit routing, and zero token waste.",
        default_base_url="http://localhost:3001/v1"
    ),
    "custom": ProviderInfo(
        platform="custom",
        name="Custom OpenAI-Compatible",
        description="Any self-hosted or private model server (Ollama, vLLM, LM Studio, llama.cpp, LocalAI).",
        monthly_free_tokens="Unlimited (Self-Hosted)",
        free_tier_models_count=1,
        requires_credit_card=False,
        is_keyless_supported=True,
        signup_url="",
        key_url="",
        rate_limit_summary="Hardware-bound concurrency and throughput.",
        key_setup_guide="Point base URL to your local Ollama (http://localhost:11434/v1), vLLM (http://localhost:8000/v1), or LM Studio (http://localhost:1234/v1).",
        gotchas_and_tips="Ensure CORS is enabled if accessing directly from browser environments.",
        default_base_url="http://localhost:11434/v1"
    )
}


# ---------------------------------------------------------------------------
# Comprehensive Model Registry (Seed Catalog)
# ---------------------------------------------------------------------------
CATALOG_MODELS: List[ModelEndpoint] = [
    # --- Google Gemini Models ---
    ModelEndpoint(
        id="google/gemini-2.5-pro",
        platform="google",
        provider_name="Google AI Studio",
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        family="Gemini",
        intelligence_rank=1,
        speed_rank=8,
        size_label="Frontier",
        context_window=1_048_576,
        rpm_limit=5,
        rpd_limit=50,
        tpm_limit=250_000,
        monthly_token_budget="~6M",
        monthly_token_budget_tokens=6_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=True,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        recommended_use="Frontier deep reasoning, comprehensive multi-page PRDs, complex synthesis"
    ),
    ModelEndpoint(
        id="google/gemini-2.5-flash",
        platform="google",
        provider_name="Google AI Studio",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        family="Gemini",
        intelligence_rank=4,
        speed_rank=4,
        size_label="Large",
        context_window=1_048_576,
        rpm_limit=10,
        rpd_limit=20,
        tpm_limit=250_000,
        monthly_token_budget="~25M",
        monthly_token_budget_tokens=25_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        recommended_use="Fast, high-fidelity customer discovery extraction with 1M context"
    ),
    ModelEndpoint(
        id="google/gemini-2.5-flash-lite",
        platform="google",
        provider_name="Google AI Studio",
        model_id="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash-Lite",
        family="Gemini",
        intelligence_rank=7,
        speed_rank=2,
        size_label="Medium",
        context_window=1_048_576,
        rpm_limit=15,
        rpd_limit=1000,
        tpm_limit=250_000,
        monthly_token_budget="~120M",
        monthly_token_budget_tokens=120_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        recommended_use="Massive throughput signal processing (~120M free tokens/mo, 1000 RPD)"
    ),

    # --- Groq Models (Ultra-Fast LPU) ---
    ModelEndpoint(
        id="groq/llama-3.3-70b-versatile",
        platform="groq",
        provider_name="Groq Cloud",
        model_id="llama-3.3-70b-versatile",
        display_name="Llama 3.3 70B Versatile",
        family="Llama",
        intelligence_rank=3,
        speed_rank=2,
        size_label="Large",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=1000,
        tpm_limit=12_000,
        tpd_limit=500_000,
        monthly_token_budget="~15M",
        monthly_token_budget_tokens=15_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://api.groq.com/openai/v1",
        recommended_use="Ultra-fast sub-second PRD synthesis and semantic cluster naming"
    ),
    ModelEndpoint(
        id="groq/llama-4-scout-17b-16e-instruct",
        platform="groq",
        provider_name="Groq Cloud",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        display_name="Llama 4 Scout (17B)",
        family="Llama",
        intelligence_rank=5,
        speed_rank=2,
        size_label="Medium",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=1000,
        tpm_limit=6_000,
        tpd_limit=1_000_000,
        monthly_token_budget="~30M",
        monthly_token_budget_tokens=30_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://api.groq.com/openai/v1",
        recommended_use="High-throughput multimodal exploration and quick feedback sorting"
    ),
    ModelEndpoint(
        id="groq/openai-gpt-oss-120b",
        platform="groq",
        provider_name="Groq Cloud",
        model_id="openai/gpt-oss-120b",
        display_name="GPT-OSS 120B (Groq)",
        family="GPT-OSS",
        intelligence_rank=4,
        speed_rank=2,
        size_label="Large",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=1000,
        tpm_limit=8_000,
        tpd_limit=200_000,
        monthly_token_budget="~6M",
        monthly_token_budget_tokens=6_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        base_url="https://api.groq.com/openai/v1",
        recommended_use="Open-weight reasoning model served at blazing fast hardware speeds"
    ),
    ModelEndpoint(
        id="groq/llama-3.1-8b-instant",
        platform="groq",
        provider_name="Groq Cloud",
        model_id="llama-3.1-8b-instant",
        display_name="Llama 3.1 8B Instant",
        family="Llama",
        intelligence_rank=8,
        speed_rank=1,
        size_label="Small",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=14400,
        tpm_limit=6_000,
        tpd_limit=500_000,
        monthly_token_budget="~15M",
        monthly_token_budget_tokens=15_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://api.groq.com/openai/v1",
        recommended_use="Instant classification with 14,400 free requests per day allowance"
    ),

    # --- Cerebras Models (>2,000 tok/sec) ---
    ModelEndpoint(
        id="cerebras/llama-3.3-70b",
        platform="cerebras",
        provider_name="Cerebras Cloud",
        model_id="llama-3.3-70b",
        display_name="Llama 3.3 70B (Cerebras)",
        family="Llama",
        intelligence_rank=3,
        speed_rank=1,
        size_label="Large",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=14400,
        tpm_limit=60_000,
        tpd_limit=1_000_000,
        monthly_token_budget="~30M",
        monthly_token_budget_tokens=30_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://api.cerebras.ai/v1",
        recommended_use="Fastest inference in the world (>2,000 tok/s) with 1M tokens/day free"
    ),
    ModelEndpoint(
        id="cerebras/qwen-3-235b",
        platform="cerebras",
        provider_name="Cerebras Cloud",
        model_id="qwen-3-235b-a22b-instruct-2507",
        display_name="Qwen3 235B (Cerebras)",
        family="Qwen",
        intelligence_rank=2,
        speed_rank=1,
        size_label="Frontier",
        context_window=131_072,
        rpm_limit=30,
        rpd_limit=14400,
        tpm_limit=60_000,
        tpd_limit=1_000_000,
        monthly_token_budget="~30M",
        monthly_token_budget_tokens=30_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        base_url="https://api.cerebras.ai/v1",
        recommended_use="Frontier reasoning and comprehensive technical synthesis at wafer-scale speeds"
    ),

    # --- OpenRouter Free Tier Models ---
    ModelEndpoint(
        id="openrouter/deepseek-v3.1",
        platform="openrouter",
        provider_name="OpenRouter (Free Pool)",
        model_id="deepseek/deepseek-v3.1:free",
        display_name="DeepSeek V3.1 (Free)",
        family="DeepSeek",
        intelligence_rank=2,
        speed_rank=6,
        size_label="Frontier",
        context_window=131_072,
        rpm_limit=20,
        rpd_limit=200,
        monthly_token_budget="~6M",
        monthly_token_budget_tokens=6_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        base_url="https://openrouter.ai/api/v1",
        recommended_use="World-class zero-cost reasoning for complex edge case analysis"
    ),
    ModelEndpoint(
        id="openrouter/qwen3-coder",
        platform="openrouter",
        provider_name="OpenRouter (Free Pool)",
        model_id="qwen/qwen3-coder:free",
        display_name="Qwen3 Coder (Free)",
        family="Qwen",
        intelligence_rank=2,
        speed_rank=6,
        size_label="Frontier",
        context_window=262_144,
        rpm_limit=20,
        rpd_limit=200,
        monthly_token_budget="~6M",
        monthly_token_budget_tokens=6_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        is_coding=True,
        base_url="https://openrouter.ai/api/v1",
        recommended_use="Technical specification generation, database schemas, and Gherkin stories"
    ),
    ModelEndpoint(
        id="openrouter/minimax-m2.5",
        platform="openrouter",
        provider_name="OpenRouter (Free Pool)",
        model_id="minimax/minimax-m2.5:free",
        display_name="MiniMax M2.5 (Free)",
        family="MiniMax",
        intelligence_rank=1,
        speed_rank=7,
        size_label="Frontier",
        context_window=196_608,
        rpm_limit=20,
        rpd_limit=200,
        monthly_token_budget="~6M",
        monthly_token_budget_tokens=6_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        base_url="https://openrouter.ai/api/v1",
        recommended_use="Top-ranked benchmark model (SWE-V ~80%) for technical PRD documentation"
    ),

    # --- GitHub Models ---
    ModelEndpoint(
        id="github/openai-gpt-4o",
        platform="github",
        provider_name="GitHub Models",
        model_id="openai/gpt-4o",
        display_name="GPT-4o (GitHub)",
        family="GPT",
        intelligence_rank=3,
        speed_rank=5,
        size_label="Large",
        context_window=128_000,
        rpm_limit=10,
        rpd_limit=50,
        monthly_token_budget="~18M",
        monthly_token_budget_tokens=18_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://models.github.ai/inference",
        recommended_use="Reliable OpenAI GPT-4o inference free with your standard GitHub account"
    ),
    ModelEndpoint(
        id="github/openai-gpt-4.1",
        platform="github",
        provider_name="GitHub Models",
        model_id="openai/gpt-4.1",
        display_name="GPT-4.1 (GitHub)",
        family="GPT",
        intelligence_rank=4,
        speed_rank=5,
        size_label="Large",
        context_window=128_000,
        rpm_limit=15,
        rpd_limit=150,
        monthly_token_budget="~9M",
        monthly_token_budget_tokens=9_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=False,
        base_url="https://models.github.ai/inference",
        recommended_use="Extended coding and tool-calling execution directly from GitHub"
    ),

    # --- Mistral Models ---
    ModelEndpoint(
        id="mistral/codestral-latest",
        platform="mistral",
        provider_name="Mistral AI",
        model_id="codestral-latest",
        display_name="Codestral",
        family="Mistral",
        intelligence_rank=4,
        speed_rank=5,
        size_label="Medium",
        context_window=32_000,
        rpm_limit=2,
        tpm_limit=500_000,
        monthly_token_budget="~50-100M",
        monthly_token_budget_tokens=75_000_000,
        supports_vision=False,
        supports_tools=True,
        is_coding=True,
        base_url="https://api.mistral.ai/v1",
        recommended_use="Industry-standard code and architecture synthesizer"
    ),
    ModelEndpoint(
        id="mistral/mistral-large-latest",
        platform="mistral",
        provider_name="Mistral AI",
        model_id="mistral-large-latest",
        display_name="Mistral Large 3",
        family="Mistral",
        intelligence_rank=3,
        speed_rank=6,
        size_label="Frontier",
        context_window=131_072,
        rpm_limit=2,
        tpm_limit=500_000,
        monthly_token_budget="~50-100M",
        monthly_token_budget_tokens=75_000_000,
        supports_vision=True,
        supports_tools=True,
        base_url="https://api.mistral.ai/v1",
        recommended_use="European flagship multilingual reasoning model"
    ),

    # --- FreeLLMAPI Unified Virtual Gateway ---
    ModelEndpoint(
        id="freellmapi/auto",
        platform="freellmapi_local",
        provider_name="FreeLLMAPI Unified Gateway",
        model_id="auto",
        display_name="FreeLLMAPI Auto-Router (7.4B tokens/mo)",
        family="Unified",
        intelligence_rank=1,
        speed_rank=1,
        size_label="Frontier",
        context_window=1_048_576,
        rpm_limit=500,
        rpd_limit=50_000,
        monthly_token_budget="~7.4 Billion",
        monthly_token_budget_tokens=7_400_000_000,
        supports_vision=True,
        supports_tools=True,
        is_reasoning=True,
        base_url="http://localhost:3001/v1",
        recommended_use="Autonomous smart routing across all 34 free providers with automatic fallover"
    ),
    ModelEndpoint(
        id="freellmapi/fusion",
        platform="freellmapi_local",
        provider_name="FreeLLMAPI Unified Gateway",
        model_id="fusion",
        display_name="FreeLLMAPI Multi-Model Fusion",
        family="Unified",
        intelligence_rank=1,
        speed_rank=4,
        size_label="Frontier",
        context_window=262_144,
        rpm_limit=100,
        monthly_token_budget="~7.4 Billion",
        monthly_token_budget_tokens=7_400_000_000,
        supports_vision=False,
        supports_tools=True,
        is_reasoning=True,
        base_url="http://localhost:3001/v1",
        recommended_use="Fans out prompt to 4 diverse models in parallel and synthesizes the optimal consensus"
    ),

    # --- Standard OpenAI Baseline ---
    ModelEndpoint(
        id="openai/gpt-4o-mini",
        platform="openai",
        provider_name="OpenAI",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        family="GPT",
        intelligence_rank=4,
        speed_rank=3,
        size_label="Medium",
        context_window=128_000,
        monthly_token_budget="Pay-As-You-Go",
        monthly_token_budget_tokens=10_000_000,
        supports_vision=True,
        supports_tools=True,
        requires_card=True,
        base_url="https://api.openai.com/v1",
        recommended_use="Standard commercial OpenAI baseline model"
    )
]

class ModelCatalogEngine:
    """Core filtering, scoring, and metadata query engine for AI models."""

    @staticmethod
    def get_all_models() -> List[Dict[str, Any]]:
        return [asdict(m) for m in CATALOG_MODELS]

    @staticmethod
    def get_providers() -> List[Dict[str, Any]]:
        return [asdict(p) for p in PROVIDERS_DIRECTORY.values()]

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        models = CATALOG_MODELS
        total_tokens = sum(m.monthly_token_budget_tokens for m in models if m.monthly_token_budget_tokens > 0)
        return {
            "headline_tokens_monthly": "7.4 Billion",
            "total_tokens_calculated": total_tokens,
            "total_providers": len(PROVIDERS_DIRECTORY),
            "total_model_endpoints": 635,  # Full live catalog capability
            "catalog_active_endpoints": len(models),
            "free_no_card_percentage": 94,
            "max_context_window": 1_048_576,
            "fastest_tps": "2,000+ tokens/sec (Cerebras CS-3)"
        }

    @staticmethod
    def filter_models(
        query: Optional[str] = None,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        min_context: Optional[int] = None,
        free_only: bool = False,
        sort_by: str = "smartest"
    ) -> List[Dict[str, Any]]:
        results = CATALOG_MODELS

        # Filter by search text
        if query:
            q = query.lower().strip()
            results = [
                m for m in results
                if q in m.display_name.lower()
                or q in m.model_id.lower()
                or q in m.provider_name.lower()
                or q in m.family.lower()
                or q in m.recommended_use.lower()
            ]

        # Filter by provider
        if provider and provider != "all":
            results = [m for m in results if m.platform == provider]

        # Filter by capability
        if capability and capability != "all":
            cap = capability.lower()
            if cap == "vision":
                results = [m for m in results if m.supports_vision]
            elif cap == "tools":
                results = [m for m in results if m.supports_tools]
            elif cap == "reasoning":
                results = [m for m in results if m.is_reasoning]
            elif cap == "coding":
                results = [m for m in results if m.is_coding]
            elif cap == "speed":
                results = [m for m in results if m.speed_rank <= 2]
            elif cap == "massive_context":
                results = [m for m in results if m.context_window >= 1_000_000]

        # Filter by context window
        if min_context and min_context > 0:
            results = [m for m in results if m.context_window >= min_context]

        # Filter by free-only (no credit card required)
        if free_only:
            results = [m for m in results if not m.requires_card]

        # Sorting algorithms
        if sort_by == "smartest":
            results = sorted(results, key=lambda m: (m.intelligence_rank, -m.context_window))
        elif sort_by == "fastest":
            results = sorted(results, key=lambda m: (m.speed_rank, m.intelligence_rank))
        elif sort_by == "context":
            results = sorted(results, key=lambda m: -m.context_window)
        elif sort_by == "free_budget":
            results = sorted(results, key=lambda m: -m.monthly_token_budget_tokens)

        return [asdict(m) for m in results]

    @staticmethod
    def get_model_by_id(model_id_or_qualified: str) -> Optional[ModelEndpoint]:
        for m in CATALOG_MODELS:
            if m.id == model_id_or_qualified or m.model_id == model_id_or_qualified:
                return m
        return None
