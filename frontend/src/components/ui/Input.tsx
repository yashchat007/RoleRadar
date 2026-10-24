import { cn } from "../../lib/cn";
import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-[var(--radius-sm)] border border-[var(--color-border-strong)] bg-[var(--color-sunken)] px-3 text-body text-[var(--color-text-primary)]",
        className,
      )}
      {...props}
    />
  );
});

export function Field({ label, help, error, children }: { label: string; help?: string; error?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-label text-[var(--color-text-primary)]">{label}</label>
      {children}
      {help && <p className="text-caption text-[var(--color-text-tertiary)]">{help}</p>}
      {error && <p className="text-caption text-[var(--color-error)]">{error}</p>}
    </div>
  );
}
