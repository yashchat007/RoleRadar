import { useEffect, useState } from "react";
import { api, type Watch } from "../lib/api";
import { useTheme } from "../contexts/ThemeContext";
import { useIndiaOnlyPreference } from "../hooks/useIndiaOnlyPreference";
import { Button } from "../components/ui/Button";

function parseApiError(err: unknown): string {
  if (err instanceof Error) {
    try {
      const parsed = JSON.parse(err.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      /* plain text */
    }
    return err.message;
  }
  return "Something went wrong";
}

export function SettingsPage() {
  const { theme, setTheme, themeError } = useTheme();
  const { indiaOnly, setIndiaOnly, error: indiaError } = useIndiaOnlyPreference(null);
  const [digest, setDigest] = useState(true);
  const [digestLoading, setDigestLoading] = useState(true);
  const [digestError, setDigestError] = useState<string | null>(null);
  const [watches, setWatches] = useState<Watch[]>([]);
  const [watchError, setWatchError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [statusIsError, setStatusIsError] = useState(false);

  useEffect(() => {
    api
      .getSettings()
      .then((s) => setDigest(s.email_digest_enabled))
      .catch((e) => setDigestError(parseApiError(e)))
      .finally(() => setDigestLoading(false));
    api
      .getWatches()
      .then(setWatches)
      .catch((e) => setWatchError(parseApiError(e)));
  }, []);

  async function onIndiaChange(enabled: boolean) {
    try {
      await setIndiaOnly(enabled);
    } catch {
      /* error surfaced via indiaError */
    }
  }

  async function saveDigest(enabled: boolean) {
    setDigestError(null);
    setDigest(enabled);
    try {
      const s = await api.patchSettings({ email_digest_enabled: enabled });
      setDigest(s.email_digest_enabled);
    } catch (e) {
      setDigestError(parseApiError(e));
      setDigest(!enabled);
    }
  }

  async function testDigest() {
    setStatus("Sending…");
    setStatusIsError(false);
    try {
      const res = await api.sendDigest();
      if (res.digest_sent) {
        setStatus(res.digest_detail ?? "Digest email sent.");
      } else {
        setStatus(res.digest_detail ?? `Digest not sent (${res.digest_status}).`);
      }
      if (res.watch_emails > 0) {
        setStatus((prev) => `${prev ?? ""} Watch alerts: ${res.watch_emails} email(s).`);
      }
    } catch (e) {
      setStatusIsError(true);
      setStatus(parseApiError(e));
    }
  }

  async function removeWatch(id: string) {
    setWatchError(null);
    try {
      await api.deleteWatch(id);
      setWatches((ws) => ws.filter((x) => x.id !== id));
    } catch (e) {
      setWatchError(parseApiError(e));
    }
  }

  return (
    <div className="max-w-lg space-y-8">
      <header>
        <h1 className="text-display">Settings</h1>
      </header>

      <section className="space-y-3">
        <h2 className="text-subheading">Discovery</h2>
        <label className="flex items-center gap-2 text-label">
          <input
            type="checkbox"
            checked={indiaOnly}
            onChange={(e) => onIndiaChange(e.target.checked)}
          />
          India-only roles (default)
        </label>
        {indiaError && (
          <p className="text-caption text-[var(--color-error)]" role="alert">{indiaError}</p>
        )}
        <p className="text-caption text-[var(--color-text-tertiary)]">
          Shows India-based and verified India-eligible remote roles. Unknown locations are hidden.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-subheading">Appearance</h2>
        <div className="flex gap-2">
          {(["light", "dark", "system"] as const).map((t) => (
            <Button
              key={t}
              variant={theme === t ? "primary" : "secondary"}
              onClick={() => setTheme(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </Button>
          ))}
        </div>
        {themeError && (
          <p className="text-caption text-[var(--color-error)]" role="alert">{themeError}</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-subheading">Email digest</h2>
        <label className="flex items-center gap-2 text-label">
          <input
            type="checkbox"
            checked={digest}
            disabled={digestLoading}
            onChange={(e) => saveDigest(e.target.checked)}
          />
          Daily briefing email (Mailpit in dev)
        </label>
        {digestError && (
          <p className="text-caption text-[var(--color-error)]" role="alert">{digestError}</p>
        )}
        <Button variant="secondary" onClick={testDigest}>Send test digest now</Button>
        {status && (
          <p
            className={`text-caption ${statusIsError ? "text-[var(--color-error)]" : "text-[var(--color-text-secondary)]"}`}
            role={statusIsError ? "alert" : "status"}
          >
            {status}
          </p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-subheading">Saved watches</h2>
        {watchError && (
          <p className="text-caption text-[var(--color-error)]" role="alert">{watchError}</p>
        )}
        {watches.length === 0 ? (
          <p className="text-caption text-[var(--color-text-tertiary)]">Create watches from Discover filters.</p>
        ) : (
          <ul className="divide-y divide-[var(--color-border-subtle)] border border-[var(--color-border-subtle)] rounded-[var(--radius-md)]">
            {watches.map((w) => (
              <li key={w.id} className="flex items-center justify-between gap-2 px-3 py-2 text-label">
                <span className="min-w-0 truncate">{w.name}</span>
                <button
                  type="button"
                  className="text-caption text-[var(--color-error)] shrink-0"
                  onClick={() => removeWatch(w.id)}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
