"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { createCheck } from "@/lib/api";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

export default function NewCheckPage() {
  const { tenantId } = useAuth();
  const router = useRouter();
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!rawText.trim()) {
      setError("Please paste the vendor request text.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("input_type", "paste_text");
      fd.append("raw_text", rawText);
      const result = await createCheck(tenantId!, fd);
      router.push(`/dashboard/checks/${result.id}`);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to create check.";
      setError(msg);
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => router.push("/dashboard/inbox")}
          className="text-gray-500 hover:text-navy-900"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h1 className="text-2xl font-bold text-navy-900">New Check</h1>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="raw-text"
              className="block text-sm font-medium text-navy-800 mb-2"
            >
              Paste vendor request
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Paste the email or message from your vendor containing bank
              details, payment instructions, or any request you want to verify.
            </p>
            <textarea
              id="raw-text"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={12}
              placeholder={"Dear Finance Team,\n\nPlease update our bank details for future payments.\n\nNew Bank: Chase\nAccount: 123456789\nRouting: 021000021\n\nPlease process this change urgently.\n\nRegards,\nVendor Name"}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-navy-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-accent/50 font-mono"
              required
            />
          </div>

          {error && (
            <div className="rounded-lg bg-blocked-bg border border-blocked-border p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <Button type="submit" disabled={loading} className="flex-1">
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner className="h-4 w-4" />
                  Analyzing…
                </span>
              ) : (
                "Analyze & Submit"
              )}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => router.push("/dashboard/inbox")}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Card>

      <div className="mt-4 rounded-lg bg-blue-50 border border-blue-200 p-4">
        <p className="text-xs text-blue-800">
          <strong>How it works:</strong> VendorCheck will extract vendor details,
          bank information, and risk signals from the text. You&apos;ll see a
          verdict (Safe / Verify / Blocked) and can make a decision to approve,
          hold, or reject the request.
        </p>
      </div>
    </div>
  );
}
