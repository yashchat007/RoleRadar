import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type TrackerBoard } from "../lib/api";
import { ScoreBar } from "../components/ui/ScoreBar";
import { cn } from "../lib/cn";

const STAGES = ["new", "shortlisted", "applied", "oa", "interview", "offer", "rejected"] as const;

export function TrackerPage() {
  const [board, setBoard] = useState<TrackerBoard | null>(null);
  const [view, setView] = useState<"board" | "list">("board");
  const [collapsedRejected, setCollapsedRejected] = useState(true);

  useEffect(() => {
    api.getTracker().then(setBoard);
  }, []);

  if (!board) {
    return <p className="text-caption text-[var(--color-text-tertiary)]">Loading tracker…</p>;
  }

  const byStage = STAGES.map((stage) => ({
    stage,
    items: board.items.filter((i) => i.stage === stage),
  }));

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-display">Tracker</h1>
        <div className="flex gap-2 text-caption">
          <button type="button" className={view === "board" ? "font-medium" : ""} onClick={() => setView("board")}>Board</button>
          <button type="button" className={view === "list" ? "font-medium" : ""} onClick={() => setView("list")}>List</button>
        </div>
      </header>

      {view === "list" ? (
        <ul className="divide-y divide-[var(--color-border-subtle)] border border-[var(--color-border-subtle)] rounded-[var(--radius-md)] bg-[var(--color-surface)]">
          {board.items.map((item) => (
            <li key={item.id} className="flex items-center gap-3 px-3 py-2 text-label">
              <span className="capitalize w-24 text-caption text-[var(--color-text-secondary)]">{item.stage}</span>
              <Link to={`/discover?job=${item.job_id}`} className="flex-1 hover:underline">{item.title}</Link>
              <span className="text-caption text-[var(--color-text-tertiary)]">{item.company_name}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {byStage.map(({ stage, items }) => {
            if (stage === "rejected" && collapsedRejected && items.length > 3) {
              return (
                <Column key={stage} title={`Rejected (${items.length})`}>
                  <button type="button" className="text-caption text-[var(--color-brand)]" onClick={() => setCollapsedRejected(false)}>
                    Show all
                  </button>
                  {items.slice(0, 2).map((item) => <Card key={item.id} item={item} />)}
                </Column>
              );
            }
            return (
              <Column key={stage} title={`${cap(stage)} (${items.length})`}>
                {items.map((item) => <Card key={item.id} item={item} />)}
              </Column>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Column({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="w-52 shrink-0 rounded-[var(--radius-md)] border border-[var(--color-border-subtle)] bg-[var(--color-sunken)] p-2">
      <h3 className="text-caption font-medium mb-2 px-1">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Card({ item }: { item: TrackerBoard["items"][0] }) {
  return (
    <div className={cn("rounded-[var(--radius-sm)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-2 text-caption")}>
      <Link to={`/discover?job=${item.job_id}`} className="text-label font-medium line-clamp-2 hover:underline">{item.title}</Link>
      <p className="text-[var(--color-text-tertiary)] mt-1">{item.company_name}</p>
      {item.score != null && <div className="mt-2"><ScoreBar score={item.score} /></div>}
    </div>
  );
}

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
