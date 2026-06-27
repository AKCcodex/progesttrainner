"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Goal } from "@/lib/types";

export default function GoalsPage() {
  const { user } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    if (!user) return;
    try {
      setGoals(await api<Goal[]>("/goals"));
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "failed");
    }
  }

  useEffect(() => {
    refresh();
  }, [user]);

  if (!user) {
    return <p>Please log in.</p>;
  }

  async function archive(id: string) {
    if (!confirm("Archive this goal?")) return;
    await api(`/goals/${id}`, { method: "DELETE" });
    refresh();
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Your goals</h1>
        <Link
          href="/goals/new"
          className="bg-accent-600 hover:bg-accent-500 text-white rounded px-4 py-2 text-sm"
        >
          + New goal
        </Link>
      </div>
      {err && <p className="text-red-400">{err}</p>}
      {goals.length === 0 ? (
        <p className="text-ink-300">No goals yet. Create one to start learning.</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {goals.map((g) => (
            <div key={g.id} className="bg-ink-800 border border-ink-700 rounded-lg p-4">
              <Link href={`/goals/${g.id}`} className="text-white font-semibold hover:underline">
                {g.title}
              </Link>
              {g.description && <p className="text-ink-300 text-sm mt-1">{g.description}</p>}
              <div className="text-xs text-ink-300 mt-3 flex justify-between">
                <span>{g.daily_minutes} min/day</span>
                <span>{g.status}</span>
              </div>
              {g.status !== "archived" && (
                <button
                  onClick={() => archive(g.id)}
                  className="text-xs text-red-400 hover:text-red-300 mt-3"
                >
                  Archive
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}