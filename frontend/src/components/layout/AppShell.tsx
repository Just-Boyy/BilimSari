import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

interface AppShellProps {
  title?: string;
  onBack?: () => void;
  children: ReactNode;
}

export function AppShell({ title, onBack, children }: AppShellProps) {
  const navigate = useNavigate();
  const handleBack = onBack ?? (() => navigate(-1));

  return (
    <div className="mx-auto min-h-screen max-w-md px-4 pb-8 pt-4">
      {title && (
        <header className="mb-4 flex items-center gap-3">
          <button
            onClick={handleBack}
            aria-label="Orqaga"
            className="rounded-full p-1 text-xl leading-none text-neutral-text/70 dark:text-white/70"
          >
            ←
          </button>
          <h1 className="text-lg font-semibold">{title}</h1>
        </header>
      )}
      {children}
    </div>
  );
}
