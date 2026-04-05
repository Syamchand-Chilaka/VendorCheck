"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { getCheck, decideCheck, ApiError } from "@/lib/api";
import type { CheckDetail } from "@/lib/types";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import VerdictBadge from "@/components/VerdictBadge";
import SignalCard from "@/components/SignalCard";

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-b-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-navy-900">{value}</span>
    </div>
  );
}

function DecisionForm({
  checkId,
  tenantId,
  onDecided,
}: {
  checkId: string;
  tenantId: string;
  onDecided: (decision: string) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const decisions = [
    { value: "approved", label: "Approve", variant: "safe" as const, desc: "Payment is safe to process" },
    { value: "held", label: "Hold", variant: "verify" as const, desc: "Need more information" },
    { value: "rejected", label: "Reject", variant: "blocked" as const, desc: "Do not process this payment" },
  ];

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setError("");
    setLoading(true);
    try {
      await decideCheck(tenantId, checkId, selected, note || undefined);
      onDecided(selected);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("A decision has already been made on this check.");
      } else {
        setError("Failed to record decision. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <h3 className="text-sm font-semibold text-navy-900 mb-3">Make a Decision</h3>
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-3 gap-2 mb-4">
          {decisions.map((d) => (
            <button
              key={d.value}
              type="button"
              onClick={() => setSelected(d.value)}
              className={`rounded-lg border-2 p-3 text-center transition-colors ${
                selected === d.value
                  ? d.variant === "safe"
                    ? "border-safe bg-safe-bg"
                    : d.variant === "verify"
                      ? "border-verify bg-verify-bg"
                      : "border-blocked bg-blocked-bg"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <p className="text-sm font-medium">{d.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{d.desc}</p>
            </button>
          ))}
        </div>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Add a note (optional)"
          rows={2}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-navy-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-accent/50 mb-3"
        />
        {error && (
          <div className="mb-3 text-sm text-red-700 bg-blocked-bg p-2 rounded-lg">
            {error}
          </div>
        )}
        <Button
          type="submit"
          disabled={!selected || loading}
          className="w-full"
        >
          {loading ? "Submitting…" : "Submit Decision"}
        </Button>
      </form>
    </Card>
  );
}

export default function CheckDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { tenantId } = useAuth();
  const router = useRouter();
  const [check, setCheck] = useState<CheckDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantId || !id) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await getCheck(tenantId, id);
        if (!cancelled) setCheck(data);
      } catch {
        if (!cancelled) router.push("/dashboard/inbox");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [tenantId, id, router]);

  if (loading || !check) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/dashboard/inbox")}
          className="text-gray-500 hover:text-navy-900"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-navy-900">
            {check.vendor_name ?? "Unknown Vendor"}
          </h1>
          <p className="text-sm text-gray-500">
            Submitted by {check.submitted_by.display_name} on{" "}
            {new Date(check.created_at).toLocaleDateString()}
          </p>
        </div>
        <VerdictBadge verdict={check.verdict} className="text-sm" />
      </div>

      {/* Verdict overview */}
      <Card>
        <div className="flex items-center gap-4 mb-4">
          <div
            className={`h-12 w-12 rounded-full flex items-center justify-center text-lg font-bold ${
              check.verdict === "safe"
                ? "bg-safe-bg text-green-700"
                : check.verdict === "blocked"
                  ? "bg-blocked-bg text-red-700"
                  : "bg-verify-bg text-yellow-700"
            }`}
          >
            {check.risk_score ?? "?"}
          </div>
          <div>
            <p className="text-sm font-semibold text-navy-900">
              Risk Score: {check.risk_score ?? "N/A"}/100
            </p>
            <p className="text-sm text-gray-600">{check.verdict_explanation}</p>
          </div>
        </div>
        {check.recommended_action && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Recommended Action
            </p>
            <p className="text-sm text-navy-900 mt-1">{check.recommended_action}</p>
          </div>
        )}
      </Card>

      {/* Extracted data */}
      <Card>
        <h3 className="text-sm font-semibold text-navy-900 mb-3">Extracted Details</h3>
        <InfoRow label="Vendor" value={check.vendor_name} />
        <InfoRow label="Contact Email" value={check.vendor_contact_email} />
        <InfoRow label="Contact Phone" value={check.vendor_contact_phone} />
        <InfoRow label="Bank" value={check.bank_name} />
        <InfoRow label="Account (masked)" value={check.bank_account_masked} />
        <InfoRow label="Routing (masked)" value={check.bank_routing_masked} />
        {check.bank_details_changed !== null && (
          <div className="flex justify-between py-2">
            <span className="text-sm text-gray-500">Bank Details Changed</span>
            <Badge variant={check.bank_details_changed ? "blocked" : "safe"}>
              {check.bank_details_changed ? "Yes" : "No"}
            </Badge>
          </div>
        )}
      </Card>

      {/* Risk signals */}
      {check.signals.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-navy-900 mb-3">
            Risk Signals ({check.signals.length})
          </h3>
          <div className="space-y-2">
            {check.signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        </div>
      )}

      {/* Decision section */}
      {check.decision ? (
        <Card>
          <h3 className="text-sm font-semibold text-navy-900 mb-3">Decision</h3>
          <div className="flex items-center gap-3">
            <Badge
              variant={
                check.decision === "approved"
                  ? "safe"
                  : check.decision === "rejected"
                    ? "blocked"
                    : "verify"
              }
            >
              {check.decision.charAt(0).toUpperCase() + check.decision.slice(1)}
            </Badge>
            {check.decided_at && (
              <span className="text-xs text-gray-500">
                {new Date(check.decided_at).toLocaleString()}
              </span>
            )}
          </div>
          {check.decision_note && (
            <p className="text-sm text-gray-600 mt-2">{check.decision_note}</p>
          )}
        </Card>
      ) : (
        <DecisionForm
          checkId={check.id}
          tenantId={tenantId!}
          onDecided={(d) => setCheck({ ...check, decision: d })}
        />
      )}

      {/* Raw input */}
      {check.raw_input_text && (
        <Card>
          <h3 className="text-sm font-semibold text-navy-900 mb-3">
            Original Input
          </h3>
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap overflow-x-auto max-h-60">
            {check.raw_input_text}
          </pre>
        </Card>
      )}
    </div>
  );
}
