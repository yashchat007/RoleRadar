import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CompanyDiscoverStrip } from "../components/discover/CompanyDiscoverStrip";
import { JobDetailPane } from "../components/jobs/JobDetailPane";
import { Button } from "../components/ui/Button";
import { Chip } from "../components/ui/Chip";
import { Input } from "../components/ui/Input";
import { DiscoverJobRow } from "../components/discover/DiscoverJobRow";
import { Table, TBody, THead, Th } from "../components/ui/Table";
import { api, type JobWithMatch } from "../lib/api";
import { useDebouncedValue } from "../lib/useDebouncedValue";
import { useIndiaOnlyPreference } from "../hooks/useIndiaOnlyPreference";

const PAGE_SIZES = [10, 15, 20] as const;
type SortMode = "auto" | "resume_match" | "preference_match" | "newest" | "title";

export function DiscoverPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState<JobWithMatch[]>([]);
  const [query, setQuery] = useState("");
  const [hasResume, setHasResume] = useState(false);
  const [sortLabel, setSortLabel] = useState<string | null>(null);
  const [sort, setSort] = useState<SortMode>("auto");
  const indiaUrlOverride = searchParams.get("india_only");
  const { indiaOnly, persistIndiaOnly, loaded: indiaPrefLoaded } =
    useIndiaOnlyPreference(indiaUrlOverride);
  const [minScore, setMinScore] = useState<number | null>(null);
  const [companyId, setCompanyId] = useState<string | null>(searchParams.get("company"));
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [matchingTotal, setMatchingTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get("job"));
  const [toast, setToast] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const debouncedQ = useDebouncedValue(query, 200);

  useEffect(() => {
    setPage(1);
  }, [debouncedQ, minScore, companyId, pageSize, indiaOnly, sort]);

  const load = useCallback(() => {
    api
      .getJobs({
        q: debouncedQ || undefined,
        hide_ineligible: true,
        min_score: minScore ?? undefined,
        company_id: companyId ?? undefined,
        page,
        page_size: pageSize,
        india_only: indiaOnly,
        internships_only: true,
        sort,
      })
      .then((res) => {
        setJobs(res.items);
        setMatchingTotal(res.meta.matching_total ?? res.items.length);
        setTotalPages(res.meta.total_pages ?? 1);
        setHasResume(Boolean(res.meta.has_resume));
        setSortLabel(res.meta.sort_label ?? null);
      })
      .catch(() => setJobs([]));
  }, [debouncedQ, minScore, companyId, page, pageSize, indiaOnly, sort]);

  useEffect(() => {
    if (!indiaPrefLoaded) return;
    load();
  }, [load, indiaPrefLoaded]);

  useEffect(() => {
    if (!selectedId) return;
    if (matchingTotal === 0 || !jobs.some((j) => j.id === selectedId)) {
      setSelectedId(null);
      const next = new URLSearchParams(searchParams);
      next.delete("job");
      setSearchParams(next, { replace: true });
    }
  }, [jobs, matchingTotal, selectedId, searchParams, setSearchParams]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        searchRef.current?.focus();
      }
      if (!selectedId || jobs.length === 0) return;
      const idx = jobs.findIndex((j) => j.id === selectedId);
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = jobs[Math.min(idx + 1, jobs.length - 1)];
        selectJob(next.id);
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        const next = jobs[Math.max(idx - 1, 0)];
        selectJob(next.id);
      }
      if (e.key.toLowerCase() === "s" && selectedId) {
        bookmark(selectedId);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [jobs, selectedId]);

  function selectJob(id: string) {
    setSelectedId(id);
    const next = new URLSearchParams(searchParams);
    next.set("job", id);
    if (companyId) next.set("company", companyId);
    setSearchParams(next);
  }

  function selectCompany(id: string | null) {
    setCompanyId(id);
    const next = new URLSearchParams(searchParams);
    if (id) next.set("company", id);
    else next.delete("company");
    setSearchParams(next);
  }

  function bookmark(jobId: string) {
    api.bookmark(jobId).then(() => {
      setToast("Saved to Shortlisted");
      window.setTimeout(() => setToast(null), 4000);
    });
  }

  return (
    <div className="space-y-4">
      <h1 className="text-display mb-4">Discover</h1>

      {!hasResume && (
        <p className="text-caption text-[var(--color-text-secondary)]">
          Upload a resume in Profile to rank Discover by resume match. Until then, results use your preference settings.
        </p>
      )}
      {hasResume && sortLabel && (
        <p className="text-caption text-[var(--color-text-tertiary)]">{sortLabel}</p>
      )}

      <CompanyDiscoverStrip selectedCompanyId={companyId} onSelectCompany={selectCompany} />

      <div className="flex flex-wrap gap-2 items-center">
        <Input
          ref={searchRef}
          className="max-w-xs"
          placeholder="Role, company, skill"
          aria-label="Search jobs"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Chip
          label="India only"
          active={indiaOnly}
          onClick={() => {
            const next = !indiaOnly;
            const nextParams = new URLSearchParams(searchParams);
            nextParams.delete("india_only");
            setSearchParams(nextParams);
            persistIndiaOnly(next).catch(() => {
              setToast("Could not save India-only preference");
              window.setTimeout(() => setToast(null), 4000);
            });
          }}
        />
        <select
          className="h-9 rounded-[var(--radius-sm)] border border-[var(--color-border-strong)] bg-[var(--color-sunken)] px-2 text-caption"
          aria-label="Sort jobs"
          value={sort}
          onChange={(e) => setSort(e.target.value as SortMode)}
        >
          <option value="auto">{hasResume ? "Best resume match" : "Best preference match"}</option>
          <option value="resume_match">Resume match</option>
          <option value="preference_match">Preference match</option>
          <option value="newest">Newest</option>
          <option value="title">Title A–Z</option>
        </select>
        <Chip
          label="Resume score ≥ 70"
          active={minScore === 70}
          onClick={() => setMinScore((s) => (s === 70 ? null : 70))}
        />
        <select
          className="h-9 rounded-[var(--radius-sm)] border border-[var(--color-border-strong)] bg-[var(--color-sunken)] px-2 text-caption"
          aria-label="Results per page"
          value={pageSize}
          onChange={(e) => setPageSize(Number(e.target.value))}
        >
          {PAGE_SIZES.map((n) => (
            <option key={n} value={n}>{n} per page</option>
          ))}
        </select>
        <Button
          variant="secondary"
          onClick={() => {
            const name = query.trim() || "All matches";
            api
              .createWatch(name, {
                q: query || undefined,
                min_score: minScore,
                hide_ineligible: true,
                india_only: indiaOnly,
                company_id: companyId ?? undefined,
              })
              .then(() => {
                setToast("Watch saved for email alerts");
                window.setTimeout(() => setToast(null), 4000);
              })
              .catch((e) => {
                const msg = e instanceof Error ? e.message : "Could not save watch";
                setToast(msg.includes("409") ? "Watch already exists for these filters" : msg);
                window.setTimeout(() => setToast(null), 5000);
              });
          }}
        >
          Save watch
        </Button>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 min-h-[480px]">
        <div className="flex-1 min-w-0">
          <Table>
            <THead>
              <tr>
                <Th>Role</Th>
                <Th className="w-28">Match</Th>
                <Th className="w-12"><span className="sr-only">Bookmark</span></Th>
              </tr>
            </THead>
            <TBody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={3} className="p-6 text-center text-caption text-[var(--color-text-tertiary)]">
                    {matchingTotal === 0
                      ? "No jobs found. Run discovery validation or adjust filters."
                      : "No jobs on this page."}
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <DiscoverJobRow
                    key={job.id}
                    job={job}
                    active={job.id === selectedId}
                    onSelect={() => selectJob(job.id)}
                    onBookmark={() => bookmark(job.id)}
                  />
                ))
              )}
            </TBody>
          </Table>

          <nav className="mt-3 flex items-center justify-between gap-2" aria-label="Pagination">
            <Button
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="text-caption text-[var(--color-text-secondary)]">
              Page {page} of {totalPages || 1} · {matchingTotal} matching
            </span>
            <Button
              variant="secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </nav>
        </div>
        <div className="w-full lg:w-[var(--detail-pane-width)] shrink-0 border border-[var(--color-border-subtle)] rounded-[var(--radius-md)] bg-[var(--color-surface)] min-h-[320px]">
          <JobDetailPane jobId={selectedId} onBookmark={() => selectedId && bookmark(selectedId)} />
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 rounded-[var(--radius-md)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-2 text-caption shadow-[var(--shadow-popover)]">
          {toast}
        </div>
      )}
    </div>
  );
}
