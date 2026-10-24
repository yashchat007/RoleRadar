import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("frontend/src/components/ui/Button.tsx", """import { cn } from "../../lib/cn";
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
""")

w("frontend/src/components/ui/Badge.tsx", """import { cn } from "../../lib/cn";
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
""")

w("frontend/src/components/ui/ScoreBar.tsx", """import { cn } from "../../lib/cn";

export function ScoreBar({ score, className }: { score: number; className?: string }) {
  const clamped = Math.max(0, Math.min(100, score));
  const filled = Math.round(clamped / 20);
  return (
    <div className={cn("flex items-center gap-2", className)} aria-label={`Match ${clamped} out of 100`}>
      <span className="font-mono text-label font-tabular w-8 text-right">{clamped}</span>
      <div className="flex gap-0.5" role="img" aria-hidden="true">
        {Array.from({ length: 5 }).map((_, i) => (
          <span
            key={i}
            className={cn(
              "h-2 w-3 rounded-[2px]",
              i < filled ? (i >= 3 ? "bg-[var(--color-brand)]" : "bg-[var(--color-text-primary)]") : "bg-[var(--color-border-subtle)]",
            )}
          />
        ))}
      </div>
    </div>
  );
}
""")

w("frontend/src/components/ui/Input.tsx", """import { cn } from "../../lib/cn";
import type { InputHTMLAttributes } from "react";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-9 w-full rounded-[var(--radius-sm)] border border-[var(--color-border-strong)] bg-[var(--color-sunken)] px-3 text-body text-[var(--color-text-primary)]",
        className,
      )}
      {...props}
    />
  );
}

export function Field({ label, help, error, children }: { label: string; help?: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-label text-[var(--color-text-primary)]">{label}</label>
      {children}
      {help && <p className="text-caption text-[var(--color-text-tertiary)]">{help}</p>}
      {error && <p className="text-caption text-[var(--color-error)]">{error}</p>}
    </div>
  );
}
""")

print("ui components ok")
