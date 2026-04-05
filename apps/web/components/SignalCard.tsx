import type { Signal } from "@/lib/types";
import Badge from "@/components/ui/Badge";

const SEVERITY_VARIANT: Record<string, "safe" | "verify" | "blocked" | "info"> = {
  low: "info",
  medium: "verify",
  high: "blocked",
  critical: "blocked",
};

export default function SignalCard({ signal }: { signal: Signal }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-gray-200 p-4">
      <Badge variant={SEVERITY_VARIANT[signal.severity] ?? "neutral"}>
        {signal.severity}
      </Badge>
      <div className="min-w-0">
        <p className="text-sm font-medium text-navy-900">{signal.title}</p>
        <p className="text-sm text-gray-600 mt-0.5">{signal.description}</p>
      </div>
    </div>
  );
}
