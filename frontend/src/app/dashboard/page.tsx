"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import type { Dashboard } from "@/lib/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [d, setD] = useState<Dashboard | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api<Dashboard>("/dashboard")
      .then(setD)
      .catch((e) => setErr(String(e)));
  }, [user]);

  if (!user) {
    return (
      <p>
        Please <Link href="/login" className="text-accent-500 underline">log in</Link> to see your dashboard.
      </p>
    );
  }

  if (err) return <p className="text-red-400">{err}</p>;
  if (!d) return <p>Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">Welcome, {user.full_name || user.email}</h1>
      <p className="text-ink-300 text-sm mb-6">Last updated {d.last_updated}</p>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        <StatCard label="Streak" value={`${d.current_streak_days}d`} />
        <StatCard label="Completion (30d)" value={`${Math.round(d.completion_pct_30d * 100)}%`} />
        <StatCard label="Lessons done" value={d.lessons_completed_total} />
        <StatCard label="Study (30d)" value={`${d.study_hours_30d}h`} />
        <StatCard label="Quiz avg" value={`${Math.round(d.quiz_average_pct * 100)}%`} />
      </div>

      <h2 className="text-xl font-semibold text-white mb-3">Your goals</h2>
      {d.goals.length === 0 ? (
        <p className="text-ink-300">
          No goals yet. <Link href="/goals/new" className="text-accent-500 underline">Create one</Link>.
        </p>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {d.goals.map((g) => (
            <Link
              key={g.id}
              href={`/goals/${g.id}`}
              className="block bg-ink-800 border border-ink-700 rounded-lg p-4 hover:border-accent-500"
            >
              <div className="flex justify-between items-baseline">
                <span className="font-semibold text-white">{g.title}</span>
                <span className="text-xs text-ink-300">{g.status}</span>
              </div>
              <div className="mt-2 h-2 bg-ink-700 rounded">
                <div
                  className="h-2 bg-accent-500 rounded"
                  style={{ width: `${Math.round(g.progress_pct * 100)}%` }}
                />
              </div>
              <div className="mt-3 flex gap-4 text-xs text-ink-300">
                <span>Due today: {g.due_today}</span>
                <span>Reviews due: {g.due_reviews}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}