import { api, type CompanyDiscoverCard } from "../../lib/api";
import { Badge } from "../ui/Badge";
import { useEffect, useState } from "react";
import { CompanyLogo } from "./CompanyLogo";

function statusTone(label: string, state: string): "success" | "warning" | "error" | "neutral" {
  if (label === "Partial scan") return "warning";
  if (label === "Scan OK" || state === "scan_ok") return "success";
  if (state === "pending_validation" || state === "validating" || state === "enabled_never_scanned") {
    return "warning";
  }
  if (state === "validation_failed" || state === "scan_failed" || label === "Scan failed") return "error";
  return "neutral";
}

function displayStatus(card: CompanyDiscoverCard) {
  if (card.status_label) return card.status_label;
  if (card.source_state === "scan_ok") return "Scan OK";
  return card.source_state.replace(/_/g, " ");
}

export function CompanyDiscoverStrip({
  selectedCompanyId,
  onSelectCompany,
}: {
  selectedCompanyId: string | null;
  onSelectCompany: (id: string | null) => void;
}) {
  const [cards, setCards] = useState<CompanyDiscoverCard[]>([]);

  useEffect(() => {
    api.getDiscoverCompanies().then(setCards).catch(() => setCards([]));
  }, []);

  if (cards.length === 0) return null;

  return (
    <section aria-label="Tracked companies" className="space-y-2">
      <h2 className="text-label text-[var(--color-text-secondary)]">Companies</h2>
      <div className="flex gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => onSelectCompany(null)}
          className={`shrink-0 rounded-[var(--radius-sm)] border px-3 py-2 text-caption ${
            selectedCompanyId === null
              ? "border-[var(--color-border-strong)] bg-[var(--color-sunken)]"
              : "border-[var(--color-border-subtle)] bg-[var(--color-surface)]"
          }`}
        >
          All companies
        </button>
        {cards.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => onSelectCompany(c.id)}
            className={`shrink-0 w-[168px] rounded-[var(--radius-sm)] border p-2 text-left ${
              selectedCompanyId === c.id
                ? "border-[var(--color-border-strong)] bg-[var(--color-sunken)]"
                : "border-[var(--color-border-subtle)] bg-[var(--color-surface)]"
            }`}
          >
            <div className="flex items-center gap-2">
              <CompanyLogo companyName={c.name} logoUrl={c.company_logo_url} size={32} />
              <span className="text-label truncate">{c.name}</span>
            </div>
            <div className="mt-2 flex items-center justify-between gap-1">
              <Badge tone={statusTone(displayStatus(c), c.source_state)}>{displayStatus(c)}</Badge>
              <span className="text-caption text-[var(--color-text-tertiary)]">
                {c.india_internship_count ?? 0} in feed
              </span>
            </div>
            {c.last_scan_at && (
              <p className="mt-1 text-[10px] leading-tight text-[var(--color-text-tertiary)]">
                Scanned {new Date(c.last_scan_at).toLocaleDateString()}
                {c.last_scan_jobs_seen != null ? ` · ${c.last_scan_jobs_seen} processed` : ""}
              </p>
            )}
            {c.coverage_note && (
              <p className="mt-0.5 text-[10px] leading-tight text-[var(--color-text-tertiary)] truncate" title={c.coverage_note}>
                {c.coverage_note}
              </p>
            )}
          </button>
        ))}
      </div>
    </section>
  );
}
