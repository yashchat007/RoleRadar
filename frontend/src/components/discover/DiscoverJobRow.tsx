import { Bookmark } from "lucide-react";
import { CompanyLogo } from "./CompanyLogo";
import { Badge } from "../ui/Badge";
import type { JobWithMatch } from "../../lib/api";

export function DiscoverJobRow({
  job,
  active,
  onSelect,
  onBookmark,
}: {
  job: JobWithMatch;
  active: boolean;
  onSelect: () => void;
  onBookmark: () => void;
}) {
  const location = job.location_display || job.location || "Location unknown";

  return (
    <tr
      className={`cursor-pointer border-b border-[var(--color-border-subtle)] ${
        active ? "bg-[var(--color-sunken)]" : "hover:bg-[var(--color-sunken)]/60"
      }`}
      onClick={onSelect}
      data-testid={`job-row-${job.id}`}
    >
      <td className="py-3.5 px-3 align-middle">
        <div className="flex items-center gap-3 min-w-0">
          <CompanyLogo companyName={job.company_name ?? "Company"} logoUrl={job.company_logo_url} size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-medium leading-snug truncate">{job.title}</p>
            <p className="text-sm text-[var(--color-text-secondary)] truncate mt-0.5">
              {job.company_name} · {location}
            </p>
            {job.career_level_label && (
              <Badge tone="neutral" className="mt-1.5">{job.career_level_label}</Badge>
            )}
          </div>
        </div>
      </td>
      <td className="py-3.5 px-3 align-middle w-28 text-right">
        {job.score != null ? (
          <span className="font-mono text-base font-tabular font-medium">{job.score}</span>
        ) : job.preference_score != null ? (
          <span className="text-caption text-[var(--color-text-secondary)]" title="Preference match (not resume)">
            Pref {job.preference_score}
          </span>
        ) : (
          <span className="text-caption text-[var(--color-text-tertiary)]">Upload resume</span>
        )}
      </td>
      <td className="py-3.5 px-2 align-middle w-11">
        <button
          type="button"
          className="p-2 rounded-[var(--radius-sm)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]"
          aria-label={`Bookmark ${job.title}`}
          onClick={(e) => {
            e.stopPropagation();
            onBookmark();
          }}
        >
          <Bookmark size={18} strokeWidth={1.5} />
        </button>
      </td>
    </tr>
  );
}
