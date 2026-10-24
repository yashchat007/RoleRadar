import { useEffect, useRef, useState } from "react";
import { api, type ResumeStatus } from "../lib/api";
import { Button } from "../components/ui/Button";

export function ProfilePage() {
  const [resume, setResume] = useState<ResumeStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getResumeStatus().then(setResume).catch(() => setResume({ has_resume: false }));
  }, []);

  async function onUpload(file: File) {
    setError(null);
    setMessage(null);
    try {
      await api.uploadResume(file);
      setMessage("Resume updated. Your matches will refresh shortly.");
      api.getResumeStatus().then(setResume);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    }
  }

  async function onRemoveResume() {
    setError(null);
    try {
      await api.deleteResume();
      setConfirmRemove(false);
      setMessage("Resume removed.");
      setResume({ has_resume: false });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not remove resume");
    }
  }

  const updated = resume?.uploaded_at
    ? new Date(resume.uploaded_at).toLocaleString()
    : null;

  return (
    <div className="max-w-lg space-y-6">
      <header>
        <h1 className="text-display">Profile</h1>
      </header>

      <section className="rounded-[var(--radius-md)] border border-[var(--color-border-subtle)] bg-[var(--color-surface)] p-5 space-y-4">
        <div>
          <p className="text-label text-[var(--color-text-secondary)]">Resume</p>
          <p className="text-body mt-1">
            {resume?.has_resume ? resume.filename : "No resume on file"}
          </p>
          {updated && (
            <p className="text-caption text-[var(--color-text-tertiary)] mt-1">Last updated {updated}</p>
          )}
        </div>

        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.target.value = "";
          }}
        />

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => fileRef.current?.click()}>
            {resume?.has_resume ? "Replace resume" : "Upload resume"}
          </Button>
          {resume?.has_resume && (
            <Button variant="secondary" onClick={() => setConfirmRemove(true)}>Remove resume</Button>
          )}
        </div>

        {message && <p className="text-caption text-[var(--color-success)]">{message}</p>}
        {error && <p className="text-caption text-[var(--color-error)]">{error}</p>}

        {confirmRemove && (
          <div className="rounded-[var(--radius-sm)] border border-[var(--color-border-strong)] p-4 space-y-3">
            <p className="text-label">Remove your resume and clear resume-derived match data?</p>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setConfirmRemove(false)}>Cancel</Button>
              <Button onClick={onRemoveResume}>Confirm</Button>
            </div>
          </div>
        )}
      </section>

      <p className="text-caption text-[var(--color-text-tertiary)]">
        Role preferences and India-only discovery are configured in Settings.
      </p>
    </div>
  );
}
