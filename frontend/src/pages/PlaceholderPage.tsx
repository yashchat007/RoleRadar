export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-heading">{title}</h1>
      <p className="mt-2 text-[var(--color-text-secondary)]">Coming in the next implementation phase.</p>
    </div>
  );
}
