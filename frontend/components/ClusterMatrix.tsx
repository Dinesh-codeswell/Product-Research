"use client";

import React, { useState } from "react";
import { ChevronRight, MessageSquare } from "lucide-react";
import { InsightCluster, ClusterCategory } from "@/lib/types";

interface ClusterMatrixProps {
  clusters: InsightCluster[];
  onSelectCluster: (cluster: InsightCluster) => void;
}

export function ClusterMatrix({ clusters, onSelectCluster }: ClusterMatrixProps) {
  const [activeCategory, setActiveCategory] = useState<string>("ALL");

  const filteredClusters = clusters.filter((c) => {
    if (activeCategory === "ALL") return true;
    return c.category === activeCategory;
  });

  const getCategoryMeta = (category: ClusterCategory) => {
    switch (category) {
      case "PAIN_POINT":
        return {
          label: "Pain Point",
          dotColor: "bg-[#ff9592]",
          textColor: "text-[#ff9592]",
        };
      case "WORKAROUND":
        return {
          label: "Workaround",
          dotColor: "bg-[#ffca16]",
          textColor: "text-[#ffca16]",
        };
      case "DESIRE":
        return {
          label: "Feature Request",
          dotColor: "bg-[#70b8ff]",
          textColor: "text-[#70b8ff]",
        };
      case "CHURN_TRIGGER":
        return {
          label: "Churn Trigger",
          dotColor: "bg-[#baa7ff]",
          textColor: "text-[#baa7ff]",
        };
      default:
        return {
          label: category,
          dotColor: "bg-[#a1a4a5]",
          textColor: "text-[#a1a4a5]",
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Category Filter Pills (Ghost buttons on Black) */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#292d30] pb-4">
        {[
          { id: "ALL", label: "All Themes", dot: "bg-[#ffffff]" },
          { id: "PAIN_POINT", label: "Pain Points", dot: "bg-[#ff9592]" },
          { id: "WORKAROUND", label: "Workarounds", dot: "bg-[#ffca16]" },
          { id: "DESIRE", label: "Desires", dot: "bg-[#70b8ff]" },
          { id: "CHURN_TRIGGER", label: "Churn Triggers", dot: "bg-[#baa7ff]" },
        ].map((tab) => {
          const isSelected = activeCategory === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveCategory(tab.id)}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-mono flex items-center gap-2 transition-all duration-150 border ${
                isSelected
                  ? "bg-[#000000] text-[#ffffff] border-[#ffffff]"
                  : "bg-[#000000] text-[#a1a4a5] border-[#292d30] hover:text-[#ffffff] hover:border-[#464a4d]"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${tab.dot}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Grid of Clusters (Resend 16px Section Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredClusters.map((cluster) => {
          const meta = getCategoryMeta(cluster.category);

          return (
            <div
              key={cluster.id}
              onClick={() => onSelectCluster(cluster)}
              className="p-6 rounded-[16px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] transition-all duration-150 cursor-pointer flex flex-col justify-between group space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[6px] border border-[#292d30] bg-[#000000] text-[11px] font-mono">
                    <span className={`h-1.5 w-1.5 rounded-full ${meta.dotColor}`} />
                    <span className={meta.textColor}>{meta.label}</span>
                  </div>

                  <span className="text-[11px] font-mono text-[#a1a4a5]">
                    {cluster.item_count} signals
                  </span>
                </div>

                <h3 className="text-base font-sans font-medium text-[#f0f0f0] group-hover:text-[#ffffff] transition-colors leading-snug">
                  {cluster.title}
                </h3>

                <p className="text-xs font-sans text-[#a1a4a5] line-clamp-3 leading-relaxed">
                  {cluster.description}
                </p>
              </div>

              {/* Bottom Quote Evidence Indicator & Inspect Link */}
              <div className="pt-4 border-t border-[#292d30] flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-1.5 text-[#6e727a]">
                  <MessageSquare className="h-3 w-3" />
                  <span>{cluster.quotes.length} Quotes</span>
                </div>

                <div className="flex items-center gap-1 text-[#f0f0f0] group-hover:text-[#ffffff] transition-colors">
                  <span>Inspect</span>
                  <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
