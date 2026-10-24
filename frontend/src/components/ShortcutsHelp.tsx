import { useEffect, useState } from "react";
import { Button } from "./ui/Button";

const SHORTCUTS = [
  { keys: "Ctrl+K / ⌘K", action: "Command palette" },
  { keys: "?", action: "Keyboard shortcuts" },
  { keys: "/", action: "Focus search (Discover)" },
  { keys: "↑ / ↓", action: "Move between jobs (Discover)" },
  { keys: "S", action: "Bookmark job (Discover)" },
  { keys: "1–7", action: "Set tracker stage (detail pane)" },
];

export function ShortcutsHelp() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "?" && !e.ctrlKey && !e.metaKey && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-dialog)]"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="shortcuts-title" className="text-subheading">Keyboard shortcuts</h2>
        <ul className="mt-3 space-y-2">
          {SHORTCUTS.map((s) => (
            <li key={s.keys} className="flex justify-between gap-4 text-caption">
              <span className="font-mono text-label">{s.keys}</span>
              <span className="text-[var(--color-text-secondary)]">{s.action}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex justify-end">
          <Button variant="secondary" onClick={() => setOpen(false)}>Close</Button>
        </div>
      </div>
    </div>
  );
}
