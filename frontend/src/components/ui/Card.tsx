import type { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl bg-neutral-white p-4 shadow-sm dark:bg-dark-card ${className}`}
      {...props}
    />
  );
}
