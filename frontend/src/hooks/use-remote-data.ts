import { useCallback, useEffect, useState } from "react";

export function useRemoteData<T>(load: () => Promise<T>, dependencies: readonly unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await load());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load data.");
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, loading, error, reload };
}
