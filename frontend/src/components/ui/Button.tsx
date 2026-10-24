import { cn } from "../../lib/cn";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "quiet" | "destructive";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--color-action)] text-[var(--color-action-text)] hover:bg-[var(--color-action-hover)] border border-transparent",
  secondary:
    "bg-[var(--color-surface)] text-[var(--color-text-primary)] border border-[var(--color-border-strong)] hover:bg-[var(--color-sunken)]",
  quiet:
    "bg-transparent text-[var(--color-text-primary)] hover:bg-[var(--color-sunken)] border border-transparent",
  destructive:
    "bg-[var(--color-surface)] text-[var(--color-error)] border border-[var(--color-border-strong)] hover:bg-[var(--color-error-bg)]",
};

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cn(
        "inline-flex h-8 items-center justify-center rounded-[var(--radius-sm)] px-3 text-label font-medium transition-colors duration-150 disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
