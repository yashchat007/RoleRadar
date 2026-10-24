import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type JobWithMatch } from "../lib/api";
import { ScoreBar } from "../components/ui/ScoreBar";
import { Table, TBody, Td, THead, Th, Tr } from "../components/ui/Table";

export function SavedPage() {
  const [items, setItems] = useState<JobWithMatch[]>([]);

  useEffect(() => {
    api.getSaved().then(setItems);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-display">Saved</h1>
      <Table>
        <THead>
          <tr>
            <Th>Score</Th>
            <Th>Role</Th>
            <Th>Company</Th>
          </tr>
        </THead>
        <TBody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={3} className="p-4 text-caption text-[var(--color-text-tertiary)]">
                No bookmarks yet. Press S on Discover or use Bookmark in the detail pane.
              </td>
            </tr>
          ) : (
            items.map((job) => (
              <Tr key={job.id} onClick={() => {}}>
                <Td>{job.score != null ? <ScoreBar score={job.score} /> : "—"}</Td>
                <Td>
                  <Link to={`/discover?job=${job.id}`} className="font-medium hover:underline">{job.title}</Link>
                </Td>
                <Td className="text-[var(--color-text-secondary)]">{job.company_name}</Td>
              </Tr>
            ))
          )}
        </TBody>
      </Table>
    </div>
  );
}
