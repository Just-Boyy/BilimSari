import type { HTMLAttributes } from "react";

type BadgeVariant = "warning" | "success" | "neutral";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  warning: "bg-warning/15 text-warning",
  success: "bg-success/15 text-success",
  neutral: "bg-neutral-border text-neutral-text dark:bg-dark-card dark:text-white",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ variant = "neutral", className = "", ...props }: BadgeProps) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
}
