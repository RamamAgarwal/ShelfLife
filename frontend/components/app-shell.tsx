"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { CircleAlert, FlaskConical } from "lucide-react";

import { API_URL, getHealth } from "@/lib/api";
import type { Health } from "@/lib/types";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Check" },
  { href: "/compare", label: "Compare" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/claims", label: "Claims" },
  { href: "/monitors", label: "Monitors" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/system", label: "System" },
];

type HealthState = Health | "unreachable" | null;

function problems(health: HealthState): string[] {
  if (health === null) return [];
  if (health === "unreachable") {
    return [`Can't reach the ShelfLife API at ${API_URL}. Start the backend, then reload.`];
  }
  const found: string[] = [];
  if (!health.bifrost.ok) found.push(`Bifrost: ${health.bifrost.detail}.`);
  if (!health.tavily.ok) found.push(`Tavily: ${health.tavily.detail}.`);
  if (health.missing_settings.length > 0) {
    found.push(`Missing settings in .env: ${health.missing_settings.join(", ")}.`);
  }
  return found;
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthState>(null);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((value) => {
        if (active) setHealth(value);
      })
      .catch(() => {
        if (active) setHealth("unreachable");
      });
    return () => {
      active = false;
    };
  }, []);

  const found = problems(health);
  const demo = health !== null && health !== "unreachable" && health.demo_mode;
  const rateLimited = health !== null && health !== "unreachable" && health.tavily.rate_limited;

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <Link href="/" className="text-[15px] font-semibold tracking-tight">
            ShelfLife
          </Link>
          <nav aria-label="Main" className="-mx-1 flex min-w-0 flex-1 gap-1 overflow-x-auto">
            {NAV.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "shrink-0 rounded-md px-2.5 py-1.5 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                    active ? "bg-muted font-medium" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {demo && (
              <span className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-foreground">
                <FlaskConical className="size-3.5" aria-hidden />
                Demo mode: invented data
              </span>
            )}
            {!demo && health && health !== "unreachable" && found.length === 0 && (
              <span>{rateLimited ? "Tavily is rate-limiting requests" : "Bifrost and Tavily connected"}</span>
            )}
          </div>
        </div>
      </header>

      {found.length > 0 && (
        <div className="border-b bg-muted/50" role="alert">
          <div className="mx-auto flex w-full max-w-6xl items-start gap-2 px-4 py-2.5 text-sm sm:px-6">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
            <p>{found.join(" ")}</p>
          </div>
        </div>
      )}

      {children}
    </div>
  );
}

export function PageContainer({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <main className={cn("mx-auto flex w-full flex-1 flex-col gap-6 px-4 py-8 sm:px-6 sm:py-10", wide ? "max-w-6xl" : "max-w-5xl")}>
      {children}
    </main>
  );
}
