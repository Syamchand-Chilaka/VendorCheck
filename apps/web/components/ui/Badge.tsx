import { type ReactNode } from "react";

const variants = {
  safe: "bg-safe-bg text-green-800 border border-safe-border",
  verify: "bg-verify-bg text-yellow-800 border border-verify-border",
  blocked: "bg-blocked-bg text-red-800 border border-blocked-border",
  neutral: "bg-gray-100 text-gray-700 border border-gray-200",
  info: "bg-blue-50 text-blue-800 border border-blue-200",
} as const;

interface BadgeProps {
  variant?: keyof typeof variants;
  children: ReactNode;
  className?: string;
}

export default function Badge({
  variant = "neutral",
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
