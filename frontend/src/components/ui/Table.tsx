import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

export function Table({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={cn("overflow-auto border border-[var(--color-border-subtle)] rounded-[var(--radius-md)]", className)}>
      <table className="w-full border-collapse text-label">{children}</table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="sticky top-0 bg-[var(--color-sunken)] text-[var(--color-text-secondary)]">
      {children}
    </thead>
  );
}

export function Th({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <th className={cn("h-9 px-3 text-left font-medium border-b border-[var(--color-border-subtle)]", className)}>
      {children}
    </th>
  );
}

export function TBody({ children }: { children: React.ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function Tr({
  active,
  onClick,
  children,
  ...rest
}: {
  active?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
} & HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      onClick={onClick}
      {...rest}
      className={cn(
        "h-11 border-b border-[var(--color-border-subtle)] cursor-pointer",
        active ? "bg-[var(--color-brand-tint)]" : "hover:bg-[var(--color-sunken)]",
      )}
    >
      {children}
    </tr>
  );
}

export function Td({ className, children }: { className?: string; children: React.ReactNode }) {
  return <td className={cn("px-3 align-middle", className)}>{children}</td>;
}
