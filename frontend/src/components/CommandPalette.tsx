import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/30"
      role="presentation"
      onClick={() => setOpen(false)}
    >
      <Command
        className="w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] shadow-[var(--shadow-dialog)] overflow-hidden"
        label="Command menu"
        onClick={(e) => e.stopPropagation()}
      >
        <Command.Input
          placeholder="Go to…"
          className="w-full border-b border-[var(--color-border-subtle)] px-3 py-2 text-label outline-none bg-[var(--color-surface)]"
        />
        <Command.List className="max-h-64 overflow-auto p-1">
          <Command.Empty className="px-3 py-2 text-caption text-[var(--color-text-tertiary)]">No results</Command.Empty>
          {[
            { label: "Discover", to: "/" },
            { label: "Saved", to: "/saved" },
            { label: "Profile", to: "/profile" },
            { label: "Settings", to: "/settings" },
          ].map((item) => (
            <Command.Item
              key={item.to}
              value={item.label}
              onSelect={() => {
                navigate(item.to);
                setOpen(false);
              }}
              className="cursor-pointer rounded-[var(--radius-sm)] px-3 py-2 text-label aria-selected:bg-[var(--color-brand-tint)]"
            >
              {item.label}
            </Command.Item>
          ))}
        </Command.List>
      </Command>
    </div>
  );
}
