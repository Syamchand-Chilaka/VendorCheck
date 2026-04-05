import Badge from "@/components/ui/Badge";

const VERDICT_MAP: Record<string, { variant: "safe" | "verify" | "blocked"; label: string }> = {
  safe: { variant: "safe", label: "Safe" },
  verify: { variant: "verify", label: "Verify" },
  blocked: { variant: "blocked", label: "Blocked" },
};

export default function VerdictBadge({
  verdict,
  className = "",
}: {
  verdict: string | null;
  className?: string;
}) {
  if (!verdict) return <Badge variant="neutral" className={className}>Pending</Badge>;
  const cfg = VERDICT_MAP[verdict] ?? { variant: "neutral" as const, label: verdict };
  return (
    <Badge variant={cfg.variant} className={className}>
      {cfg.label}
    </Badge>
  );
}
