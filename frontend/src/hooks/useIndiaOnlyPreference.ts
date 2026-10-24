import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

function readIndiaOnlyFromProfile(preferences: Record<string, unknown> | undefined): boolean {
  return preferences?.india_only !== false;
}

/** Persisted India-only discovery preference (default on). */
export function useIndiaOnlyPreference(urlOverride: string | null) {
  const [indiaOnly, setIndiaOnlyState] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getProfile()
      .then((profile) => {
        if (cancelled) return;
        if (urlOverride === "false") setIndiaOnlyState(false);
        else if (urlOverride === "true") setIndiaOnlyState(true);
        else setIndiaOnlyState(readIndiaOnlyFromProfile(profile.preferences));
      })
      .catch(() => {
        if (!cancelled) setIndiaOnlyState(true);
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [urlOverride]);

  const persistIndiaOnly = useCallback(async (enabled: boolean) => {
    setError(null);
    setIndiaOnlyState(enabled);
    try {
      const profile = await api.getProfile();
      await api.patchProfile({
        preferences: { ...profile.preferences, india_only: enabled },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save India-only preference");
      throw e;
    }
  }, []);

  const setIndiaOnly = useCallback(
    async (enabled: boolean, options?: { persist?: boolean }) => {
      if (options?.persist === false) {
        setIndiaOnlyState(enabled);
        return;
      }
      await persistIndiaOnly(enabled);
    },
    [persistIndiaOnly],
  );

  return { indiaOnly, setIndiaOnly, persistIndiaOnly, loaded, error };
}
