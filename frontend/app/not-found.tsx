import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="py-32 text-center space-y-6">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#000000] border border-[#292d30] text-xs font-mono text-[#a1a4a5]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#ff9592]" />
        <span>404_PAGE_NOT_FOUND</span>
      </div>

      <h2 className="font-serif text-5xl sm:text-6xl font-normal text-[#ffffff] tracking-[-0.01em]">
        Void.
      </h2>

      <p className="text-sm font-sans text-[#a1a4a5] max-w-md mx-auto leading-relaxed">
        The research session or parameter you requested does not exist or has expired.
      </p>

      <div className="pt-2">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-[6px] bg-[#000000] border border-[#292d30] hover:border-[#ffffff] text-xs font-mono text-[#ffffff] transition-all"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>return_to_launchpad</span>
        </Link>
      </div>
    </div>
  );
}
