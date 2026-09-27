"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PlaygroundRoute() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/models?tab=playground");
  }, [router]);

  return (
    <div className="h-screen w-screen bg-[#0c0d10] flex items-center justify-center text-xs font-mono text-[#a1a4a5]">
      Redirecting to Playground...
    </div>
  );
}

