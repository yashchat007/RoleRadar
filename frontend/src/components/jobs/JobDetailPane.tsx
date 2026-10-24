import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type JobDetail, type MatchDetail } from "../../lib/api";
import { Badge } from "../ui/Badge";
import { eligibilityTone } from "../../lib/eligibility";
import { Button } from "../ui/Button";

export function JobDetailPane({
  jobId,
  onBookmark,
}: {
  jobId: string | null;
  onBookmark?: () => void;
}) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setMatch(null);
      return;
    }
    setJob(null);
    setMatch(null);
    setError(null);
    const requestedId = jobId;
    Promise.all([api.getJob(requestedId), api.getJobMatch(requestedId).catch(() => null)])
      .then(([j, m]) => {
        if (j.id !== requestedId) return;
        setJob(j);
        setMatch(m);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load job");
      });
  }, [jobId]);

  if (!jobId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-[var(--color-text-tertiary)] p-6">
        Select a role to see details
      </div>
    );
  }

  if (error) return <p className="p-4 text-sm text-[var(--color-error)]">{error}</p>;
  if (!job) return <p className="p-4 text-sm text-[var(--color-text-tertiary)]">Loading…</p>;

  const summary =
    job.description_sections && typeof job.description_sections.summary === "string"
      ? job.description_sections.summary
      : null;

  const verified = job.last_verified_at
    ? new Date(job.last_verified_at).toLocaleString()
    : null;

  return (
    <div className="flex h-full flex-col overflow-auto p-5 gap-5" data-testid="job-detail-pane">
      <div>
        <h2 className="text-xl font-medium leading-snug">{job.title}</h2>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          {[job.company_name, job.location].filter(Boolean).join(" · ")}
        </p>
        {job.requisition_id && (
          <p className="mt-1 text-caption text-[var(--color-text-tertiary)]">
            Requisition {job.requisition_id}
          </p>
        )}
        {verified && (
          <p className="mt-1 text-caption text-[var(--color-text-tertiary)]">
            Last verified on official source: {verified}
            {job.lifecycle_status === "possibly_closed" ? " · Possibly closed — re-check listing" : ""}
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => window.open(job.apply_url, "_blank", "noopener")}>
          <span className="inline-flex items-center gap-1.5 text-sm">
            Apply on official site <ExternalLink size={15} strokeWidth={1.5} />
          </span>
        </Button>
        <Button variant="secondary" onClick={onBookmark}>Bookmark</Button>
        <Button variant="secondary" onClick={() => window.open(job.listing_url, "_blank", "noopener")}>
          View listing
        </Button>
      </div>

      {match && (
        <section className="space-y-3 border-t border-[var(--color-border-subtle)] pt-4">
          {match.resume_match_available && match.score != null ? (
            <p className="text-sm">
              Resume match: <span className="font-mono font-medium">{match.score}</span>
              {match.role_family ? ` · ${match.role_family}` : ""}
            </p>
          ) : (
            <p className="text-sm text-[var(--color-text-secondary)]">
              Upload a resume to calculate your match
              {match.preference_score != null ? (
                <>
                  {" "}
                  · Preference match: <span className="font-mono">{match.preference_score}</span>
                  <span className="text-caption text-[var(--color-text-tertiary)]">
                    {" "}
                    (role family & location preferences only)
                  </span>
                </>
              ) : null}
            </p>
          )}
          {match.eligible === false ? (
            <Badge tone="warning">
              Potential eligibility issue: {match.eligibility_reasons[0] ?? "See requirements"}
            </Badge>
          ) : (
            <Badge
              tone={eligibilityTone(
                match.requirements.some((r) => r.status === "missing" || r.status === "unclear" || r.status === "partial")
                  ? "Eligibility unclear"
                  : "Eligible",
              )}
            >
              {match.requirements.some((r) => r.status === "missing" || r.status === "unclear" || r.status === "partial")
                ? "Eligibility unclear"
                : "Eligible"}
            </Badge>
          )}
          {match.top_reasons.length > 0 && (
            <ul className="text-sm text-[var(--color-text-secondary)] list-disc pl-5 space-y-1">
              {match.top_reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
          <h3 className="text-label font-medium pt-1">Requirements</h3>
          {match.requirements.length === 0 ? (
            <p className="text-sm text-[var(--color-text-tertiary)]">
              Requirement details are not available from the official listing yet.
            </p>
          ) : (
            <ul className="space-y-2 text-sm">
              {match.requirements.slice(0, 10).map((r) => (
                <li key={`${r.text}-${r.status}`} className="border-l-2 border-[var(--color-border-subtle)] pl-3">
                  <Badge tone={reqTone(r.status)}>{r.status}</Badge>
                  <span className="ml-2">{r.text}</span>
                  {r.evidence ? (
                    <p className="text-[var(--color-text-tertiary)] mt-1 text-caption">{r.evidence}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {summary && (
        <section className="border-t border-[var(--color-border-subtle)] pt-4 text-sm text-[var(--color-text-secondary)]">
          {summary}
        </section>
      )}
    </div>
  );
}

function reqTone(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "met") return "success";
  if (status === "partial") return "warning";
  if (status === "missing") return "error";
  return "neutral";
}
