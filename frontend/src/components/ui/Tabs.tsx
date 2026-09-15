interface Tab {
  key: string;
  label: string;
  locked?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 rounded-xl bg-neutral-border p-1 dark:bg-dark-card">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`flex-1 rounded-lg px-2 py-2 text-sm font-semibold transition ${
            active === tab.key
              ? "bg-neutral-white text-primary shadow-sm dark:bg-dark-bg"
              : "text-neutral-text/70 dark:text-white/70"
          }`}
        >
          {tab.label}
          {tab.locked && <span className="ml-1">🔒</span>}
        </button>
      ))}
    </div>
  );
}
