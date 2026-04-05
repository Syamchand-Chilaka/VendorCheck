"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { listChecks, getMetrics } from "@/lib/api";
import type { CheckListItem, MetricsSummary } from "@/lib/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import VerdictBadge from "@/components/VerdictBadge";

const DECISION_BADGE: Record<string, "safe" | "verify" | "blocked" | "neutral"> = {
  approved: "safe",
  held: "verify",
  rejected: "blocked",
};

function MetricsRow({ metrics }: { metrics: MetricsSummary | null }) {
  if (!metrics) return null;
  const items = [
    { label: "Checks", value: metrics.total_checks },
    { label: "Vendors", value: metrics.total_vendors },
    { label: "Documents", value: metrics.total_documents },
    { label: "Open Reviews", value: metrics.open_review_tasks },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {items.map((m) => (
        <Card key={m.label}>
          <p className="text-sm text-gray-500">{m.label}</p>
          <p className="text-2xl font-bold text-navy-900 mt-1">{m.value}</p>
        </Card>
      ))}
    </div>
  );
}

function CheckRow({ check }: { check: CheckListItem }) {
  return (
    <Link
      href={`/dashboard/checks/${check.id}`}
      className="flex items-center gap-4 px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0"
    >
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-navy-900 truncate">
          {check.vendor_name ?? "Unknown Vendor"}
        </p>
        <p className="text-xs text-gray-500 mt-0.5">
          {new Date(check.created_at).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
      <VerdictBadge verdict={check.verdict} />
      {check.decision && (
        <Badge variant={DECISION_BADGE[check.decision] ?? "neutral"}>
          {check.decision}
        </Badge>
      )}
      {check.risk_score !== null && (
        <span className="text-xs text-gray-500 w-12 text-right">
          {check.risk_score}%
        </span>
      )}
      <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </Link>
  );
}

export default function InboxPage() {
  const { tenantId } = useAuth();
  const [checks, setChecks] = useState<CheckListItem[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantId) return;
    let cancelled = false;
    (async () => {
      try {
        const [checkRes, metricRes] = await Promise.all([
          listChecks(tenantId),
          getMetrics(tenantId),
        ]);
        if (!cancelled) {
          setChecks(checkRes.items);
          setMetrics(metricRes);
        }
      } catch (err) {
        console.error("Failed to load inbox", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [tenantId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-navy-900">Inbox</h1>
        <Link
          href="/dashboard/checks/new"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Check
        </Link>
      </div>

      <MetricsRow metrics={metrics} />

      <Card padding={false}>
        {checks.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg font-medium">No checks yet</p>
            <p className="text-sm mt-1">
              Submit your first vendor check to get started.
            </p>
          </div>
        ) : (
          <div>
            {checks.map((check) => (
              <CheckRow key={check.id} check={check} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
