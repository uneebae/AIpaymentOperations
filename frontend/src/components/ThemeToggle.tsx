import type { ThemePreference } from "../hooks/useTheme";

const OPTIONS: { value: ThemePreference; label: string; icon: string }[] = [
  { value: "light", label: "Light", icon: "☀" },
  { value: "dark", label: "Dark", icon: "☾" },
  { value: "system", label: "System", icon: "◐" },
];

export function ThemeToggle({
  theme,
  onChange,
}: {
  theme: ThemePreference;
  onChange: (theme: ThemePreference) => void;
}) {
  return (
    <div className="theme-toggle" role="group" aria-label="Colour theme">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`theme-toggle-btn${theme === opt.value ? " active" : ""}`}
          aria-pressed={theme === opt.value}
          title={`${opt.label} theme`}
          onClick={() => onChange(opt.value)}
        >
          <span aria-hidden="true">{opt.icon}</span>
          <span className="theme-toggle-label">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
