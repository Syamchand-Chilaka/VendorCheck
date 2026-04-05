import { type ButtonHTMLAttributes } from "react";

const variants = {
  primary:
    "bg-accent text-white hover:bg-accent-hover disabled:opacity-50",
  secondary:
    "bg-white text-navy-900 border border-gray-300 hover:bg-gray-50 disabled:opacity-50",
  danger:
    "bg-blocked text-white hover:bg-red-600 disabled:opacity-50",
  ghost:
    "text-navy-700 hover:bg-gray-100 disabled:opacity-50",
} as const;

const sizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
} as const;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

export default function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent/50 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    />
  );
}
