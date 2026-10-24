import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type TodayResponse } from "../lib/api";
import { ScoreBar } from "../components/ui/ScoreBar";

export function TodayPage() {
  const [data, setData] = useState<TodayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getToday().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return <p className="text-caption text-[var(--color-error)]">{error}</p>;
  }

  if (!data) {
    return <p className="text-caption text-[var(--color-text-tertiary)]">Loading briefing…</p>;
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_240px]">
      <div className="space-y-6">
        <header>
          <h1 className="text-display">Today</h1>
          <p className="mt-2 text-[var(--color-text-secondary)]">{data.headline}</p>
        </header>

        {data.sources_degraded.length > 0 && (
          <div className="rounded-[var(--radius-md)] border border-[var(--color-warning)] bg-[var(--color-warning-bg)] p-3 text-caption">
            {data.sources_degraded.map((s) => <p key={s}>{s}</p>)}
          </div>
        )}

        <section>
          <h2 className="text-subheading mb-3">Worth your attention</h2>
          {data.attention.length === 0 ? (
            <p className="text-caption text-[var(--color-text-secondary)]">
              No matches yet. <Link to="/profile" className="text-[var(--color-brand)]">Upload your resume</Link> or{" "}
              <Link to="/discover" className="text-[var(--color-brand)]">browse Discover</Link>.
            </p>
          ) : (
            <ul className="divide-y divide-[var(--color-border-subtle)] border border-[var(--color-border-subtle)] rounded-[var(--radius-md)] bg-[var(--color-surface)]">
              {data.attention.map((row) => (
                <li key={row.job_id} className="flex items-center gap-4 px-3 py-2">
                  <ScoreBar score={row.score} />
                  <div className="min-w-0 flex-1">
                    <Link to={`/discover?job=${row.job_id}`} className="text-label font-medium hover:underline">
                      {row.title}
                    </Link>
                    <p className="text-caption text-[var(--color-text-secondary)] truncate">
                      {row.company_name}
                      {row.top_reason ? ` · ${row.top_reason}` : ""}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h2 className="text-subheading mb-2">What changed</h2>
          <ul className="space-y-1 text-caption text-[var(--color-text-secondary)]">
            {data.changelog.length === 0 ? <li>No recent listing events.</li> : null}
            {data.changelog.map((c, i) => (
              <li key={i}>{c.message}</li>
            ))}
          </ul>
        </section>
      </div>

      <aside className="space-y-4">
        <div className="rounded-[var(--radius-md)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-3">
          <h3 className="text-label font-medium mb-2">Tracker</h3>
          <ul className="space-y-1 text-caption">
            {Object.entries(data.tracker_counts).map(([stage, count]) => (
              <li key={stage} className="flex justify-between">
                <span className="capitalize">{stage}</span>
                <span className="font-mono font-tabular">{count}</span>
              </li>
            ))}
          </ul>
          <Link to="/tracker" className="mt-2 inline-block text-caption text-[var(--color-brand)]">Open tracker</Link>
        </div>
        <div className="rounded-[var(--radius-md)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-3">
          <h3 className="text-label font-medium mb-2">Deadlines</h3>
          <ul className="space-y-2 text-caption">
            {data.upcoming_deadlines.length === 0 ? <li className="text-[var(--color-text-tertiary)]">None upcoming</li> : null}
            {data.upcoming_deadlines.map((d) => (
              <li key={d.job_id}>
                <p className="font-medium truncate">{d.title}</p>
                <p className="text-[var(--color-text-tertiary)]">{d.deadline_at ? new Date(d.deadline_at).toLocaleDateString() : ""}</p>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
