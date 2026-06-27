"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Review } from "@/lib/types";

export default function ReviewsPage() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    if (!user) return;
    try {
      const from = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString();
      const to = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();
      setReviews(await api<Review[]>(`/reviews?from=${from}&to=${to}`));
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "failed");
    }
  }

  useEffect(() => {
    refresh();
  }, [user]);

  async function markDone(id: string) {
    await api(`/reviews/${id}/complete`, { method: "POST" });
    refresh();
  }

  if (!user) return <p>Please log in.</p>;
  if (err) return <p className="text-red-400">{err}</p>;

  const pending = reviews.filter((r) => r.status === "pending");
  const completed = reviews.filter((r) => r.status === "done");

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-4">Spaced repetition reviews</h1>

      <h2 className="text-lg font-semibold text-white mt-4 mb-2">Pending ({pending.length})</h2>
      {pending.length === 0 ? (
        <p className="text-ink-300 text-sm">No reviews pending. Nice work — keep the streak going.</p>
      ) : (
        <ul className="space-y-2">
          {pending.map((r) => (
            <li key={r.id} className="bg-ink-800 border border-ink-700 rounded p-3 flex justify-between items-center">
              <div>
                <div className="text-white">Repetition #{r.repetition_index + 1} · +{r.interval_days}d</div>
                <div className="text-xs text-ink-300">scheduled: {new Date(r.scheduled_for).toLocaleString()}</div>
              </div>
              <button
                onClick={() => markDone(r.id)}
                className="text-xs bg-accent-600 hover:bg-accent-500 text-white rounded px-3 py-1"
              >
                Mark done
              </button>
            </li>
          ))}
        </ul>
      )}

      <h2 className="text-lg font-semibold text-white mt-8 mb-2">Recently completed ({completed.length})</h2>
      <ul className="space-y-1 text-sm">
        {completed.slice(0, 10).map((r) => (
          <li key={r.id} className="bg-ink-800 border border-ink-700 rounded px-3 py-2 text-ink-300">
            repetition #{r.repetition_index + 1} · completed{" "}
            {r.completed_at ? new Date(r.completed_at).toLocaleString() : "—"}
          </li>
        ))}
      </ul>
    </div>
  );
}