"use client";

import React, { useState } from "react";
import { X, Key, Check, Save, ExternalLink, Info } from "lucide-react";
import { saveChannelCredentials } from "@/lib/api";

interface ChannelSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChannelSettingsModal({ isOpen, onClose }: ChannelSettingsModalProps) {
  const [twitterAuthToken, setTwitterAuthToken] = useState("");
  const [twitterCt0, setTwitterCt0] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [facebookCUser, setFacebookCUser] = useState("");
  const [facebookXs, setFacebookXs] = useState("");
  const [firecrawlApiKey, setFirecrawlApiKey] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setStatusMsg(null);

    try {
      const payload: Record<string, string> = {};
      if (twitterAuthToken) payload.twitter_auth_token = twitterAuthToken.trim();
      if (twitterCt0) payload.twitter_ct0 = twitterCt0.trim();
      if (githubToken) payload.github_token = githubToken.trim();
      if (facebookCUser) payload.facebook_c_user = facebookCUser.trim();
      if (facebookXs) payload.facebook_xs = facebookXs.trim();
      if (firecrawlApiKey) payload.firecrawl_api_key = firecrawlApiKey.trim();

      await saveChannelCredentials(payload);
      setStatusMsg("Credentials stored for this active runtime.");
      setTimeout(() => setStatusMsg(null), 3000);
    } catch (err: any) {
      setStatusMsg("Error storing credentials: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#000000]/80 backdrop-blur-[25px] p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-xl rounded-[24px] bg-[#000000] border border-[#292d30] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-[#292d30] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-[6px] bg-[#000000] border border-[#292d30] text-[#9281f7]">
              <Key className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-sans font-medium text-[#ffffff]">
                Platform Authentication & Cookies
              </h2>
              <p className="text-xs font-mono text-[#a1a4a5]">
                Optional session tokens for deep X, Facebook, and GitHub crawling
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-[6px] text-[#a1a4a5] hover:text-[#ffffff] border border-transparent hover:border-[#292d30] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSave} className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Zero-auth note */}
          <div className="p-4 rounded-[6px] bg-[#000000] border border-[#292d30] flex items-start gap-3 text-xs font-mono text-[#a1a4a5]">
            <Info className="h-4 w-4 text-[#9281f7] shrink-0 mt-0.5" />
            <div>
              <span className="text-[#f0f0f0]">Reddit, YouTube, and Hacker News operate 100% zero-auth</span> out of the box. Paste exported browser cookies below for authenticated Twitter/X or Facebook requests.
            </div>
          </div>

          {/* Firecrawl Deep Scraper Integration */}
          <div className="space-y-3 p-4 rounded-[16px] bg-[#000000] border border-[#292d30] focus-within:border-[#9281f7]/50 transition-colors">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="font-medium text-[#ffffff]">Firecrawl API Key</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#9281f7]/20 text-[#9281f7] border border-[#9281f7]/40">
                  LLM-Ready Markdown
                </span>
              </div>
              <a
                href="https://firecrawl.dev"
                target="_blank"
                rel="noreferrer"
                className="text-[#9281f7] hover:underline flex items-center gap-1"
              >
                <span>firecrawl.dev</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <p className="text-[11px] font-mono text-[#a1a4a5]">
              Enables deep scraping of discovered Google and web articles into clean Markdown and structured JSON for AI models.
            </p>
            <input
              type="password"
              value={firecrawlApiKey}
              onChange={(e) => setFirecrawlApiKey(e.target.value)}
              placeholder="fc-xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
            />
          </div>

          {/* Twitter / X */}
          <div className="space-y-3 p-4 rounded-[16px] bg-[#000000] border border-[#292d30]">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-medium text-[#ffffff]">Twitter / X Session</span>
              <a
                href="https://cookie-editor.com"
                target="_blank"
                rel="noreferrer"
                className="text-[#9281f7] hover:underline flex items-center gap-1"
              >
                <span>Cookie-Editor</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="password"
                value={twitterAuthToken}
                onChange={(e) => setTwitterAuthToken(e.target.value)}
                placeholder="auth_token"
                className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
              />
              <input
                type="password"
                value={twitterCt0}
                onChange={(e) => setTwitterCt0(e.target.value)}
                placeholder="ct0"
                className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
              />
            </div>
          </div>

          {/* GitHub Token */}
          <div className="space-y-2 p-4 rounded-[16px] bg-[#000000] border border-[#292d30]">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-medium text-[#ffffff]">GitHub Personal Access Token</span>
              <span className="text-[#6e727a]">Optional</span>
            </div>
            <input
              type="password"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              className="w-full px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
            />
          </div>

          {/* Facebook Session */}
          <div className="space-y-3 p-4 rounded-[16px] bg-[#000000] border border-[#292d30]">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-medium text-[#ffffff]">Facebook Session</span>
              <span className="text-[#6e727a]">c_user & xs</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="password"
                value={facebookCUser}
                onChange={(e) => setFacebookCUser(e.target.value)}
                placeholder="c_user cookie"
                className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
              />
              <input
                type="password"
                value={facebookXs}
                onChange={(e) => setFacebookXs(e.target.value)}
                placeholder="xs cookie"
                className="px-3.5 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] text-xs font-mono text-[#ffffff] placeholder-[#464a4d] focus:outline-none focus:border-[#ffffff]"
              />
            </div>
          </div>

          {statusMsg && (
            <div className="p-3 rounded-[6px] bg-[#000000] border border-[#3ad389]/30 text-[#3ad389] text-xs font-mono text-center flex items-center justify-center gap-2">
              <Check className="h-3.5 w-3.5" />
              <span>{statusMsg}</span>
            </div>
          )}

          {/* Footer Controls */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-[#292d30]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#a1a4a5] hover:text-[#ffffff] transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 rounded-[6px] bg-[#3b9eff] hover:bg-[#3b9eff]/90 text-white font-sans font-medium text-xs flex items-center gap-2 transition-all disabled:opacity-40"
            >
              <Save className="h-3.5 w-3.5" />
              <span>Save & Apply</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
