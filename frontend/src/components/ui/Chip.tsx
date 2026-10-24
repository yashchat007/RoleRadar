import { X } from "lucide-react";
import { cn } from "../../lib/cn";

export function Chip({
  label,
  onRemove,
  active,
  onClick,
}: {
  label: string;
  onRemove?: () => void;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-7 items-center gap-1 rounded-[var(--radius-sm)] border px-2 text-caption",
        active
          ? "border-[var(--color-brand)] bg-[var(--color-brand-tint)] text-[var(--color-brand)]"
          : "border-[var(--color-border-strong)] bg-[var(--color-surface)] text-[var(--color-text-secondary)]",
      )}
    >
      <button type="button" onClick={onClick} className="hover:text-[var(--color-text-primary)]">
        {label}
      </button>
      {onRemove && (
        <button type="button" aria-label={`Remove ${label}`} onClick={onRemove}>
          <X size={12} strokeWidth={1.5} />
        </button>
      )}
    </span>
  );
}
