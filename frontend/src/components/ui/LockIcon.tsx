import type { TopicStatus } from "../../types/api";

export function StatusIcon({ status }: { status: TopicStatus }) {
  if (status === "completed") {
    return <span className="text-success">✅</span>;
  }
  if (status === "locked") {
    return <span className="text-neutral-text/40 dark:text-white/40">🔒</span>;
  }
  return <span className="text-primary">▶️</span>;
}
