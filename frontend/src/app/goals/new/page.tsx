"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

export default function NewGoalPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    description: "",
    daily_minutes: 30,
  });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!user) return <p>Please log in.</p>;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const goal = await api<{ id: string }>("/goals", {
        method: "POST",
        json: form,
      });
      router.push(`/goals/${goal.id}`);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md mx-auto bg-ink-800 border border-ink-700 rounded-lg p-6">
      <h1 className="text-xl font-bold text-white mb-4">New goal</h1>
      <form onSubmit={submit} className="space-y-3">
        <input
          required
          placeholder="e.g. Learn Rust"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
        <textarea
          placeholder="What do you want to learn? (optional)"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white h-24"
        />
        <label className="block text-sm text-ink-300">
          Daily minutes available
          <input
            type="number"
            min={5}
            max={480}
            value={form.daily_minutes}
            onChange={(e) => setForm({ ...form, daily_minutes: parseInt(e.target.value, 10) || 30 })}
            className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white mt-1"
          />
        </label>
        {err && <p className="text-red-400 text-sm">{err}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-accent-600 hover:bg-accent-500 text-white rounded py-2 disabled:opacity-50"
        >
          {busy ? "Creating…" : "Create goal"}
        </button>
      </form>
    </div>
  );
}