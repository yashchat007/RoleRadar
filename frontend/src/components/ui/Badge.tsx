import { cn } from "../../lib/cn";
import type { ReactNode } from "react";

type Tone = "neutral" | "brand" | "success" | "warning" | "error" | "info" | "ochre";

const tones: Record<Tone, string> = {
  neutral: "bg-[var(--color-sunken)] text-[var(--color-text-secondary)]",
  brand: "bg-[var(--color-brand-tint)] text-[var(--color-brand)]",
  success: "bg-[var(--color-success-bg)] text-[var(--color-success)]",
  warning: "bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
  error: "bg-[var(--color-error-bg)] text-[var(--color-error)]",
  info: "bg-[var(--color-info-bg)] text-[var(--color-info)]",
  ochre: "bg-[var(--color-ochre-tint)] text-[var(--color-ochre)]",
};

export function Badge({
  children,
  tone = "neutral",
  icon,
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center gap-1 rounded-[var(--radius-sm)] px-2 text-caption font-medium",
        tones[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
