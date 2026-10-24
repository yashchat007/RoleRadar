import { cn } from "../../lib/cn";

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
