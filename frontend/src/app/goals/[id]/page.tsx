"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Goal, Lesson, Quiz, QuizAttempt, Resource } from "@/lib/types";
import { QuizRunner } from "@/components/QuizRunner";

export default function GoalDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { user } = useAuth();
  const [goal, setGoal] = useState<Goal | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [activeQuiz, setActiveQuiz] = useState<{ quiz: Quiz; attempt?: QuizAttempt } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  const refresh = useCallback(async () => {
    if (!user || !id) return;
    try {
      const g = await api<Goal>(`/goals/${id}`);
      setGoal(g);
      const today = new Date().toISOString().slice(0, 10);
      setLessons(await api<Lesson[]>(`/lessons?goal_id=${id}&date=${today}`));
      setResources(await api<Resource[]>(`/resources?goal_id=${id}`));
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "failed");
    }
  }, [user, id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function complete(lessonId: string) {
    await api(`/lessons/${lessonId}/complete`, { method: "POST" });
    refresh();
  }
  async function skip(lessonId: string) {
    await api(`/lessons/${lessonId}/skip`, { method: "POST" });
    refresh();
  }
  async function startQuiz(lessonId: string) {
    try {
      const q = await api<Quiz>(`/lessons/${lessonId}/quiz`, { method: "POST" });
      setActiveQuiz({ quiz: q });
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "quiz failed");
    }
  }

  if (!user) return <p>Please log in.</p>;
  if (err) return <p className="text-red-400">{err}</p>;
  if (!goal) return <p>Loading…</p>;

  return (
    <div>
      <Link href="/goals" className="text-sm text-ink-300 hover:text-white">← All goals</Link>
      <h1 className="text-2xl font-bold text-white mt-1">{goal.title}</h1>
      {goal.description && <p className="text-ink-300 mt-1">{goal.description}</p>}
      <div className="text-xs text-ink-300 mt-1">
        {goal.daily_minutes} min/day · status: {goal.status}
      </div>

      <section className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-white">Today's lessons</h2>
          <button
            onClick={() => setShowAdd((v) => !v)}
            className="text-sm text-accent-500 hover:text-accent-600"
          >
            + Add resource
          </button>
        </div>
        {showAdd && <AddResourceForm goalId={goal.id} onAdded={refresh} />}
        {lessons.length === 0 ? (
          <p className="text-ink-300 text-sm">No lessons scheduled yet — they generate at 06:00 UTC.</p>
        ) : (
          <ul className="space-y-2">
            {lessons.map((l) => (
              <li key={l.id} className="bg-ink-800 border border-ink-700 rounded p-3">
                <div className="flex justify-between items-baseline">
                  <span className="font-semibold text-white">{l.title}</span>
                  <span className="text-xs text-ink-300">{l.duration_minutes}m</span>
                </div>
                {l.description && <p className="text-ink-300 text-sm mt-1">{l.description}</p>}
                <div className="text-xs mt-2">
                  <span
                    className={
                      l.status === "done"
                        ? "text-green-400"
                        : l.status === "skipped"
                        ? "text-yellow-400"
                        : "text-ink-300"
                    }
                  >
                    {l.status}
                  </span>
                </div>
                {l.status === "pending" && (
                  <div className="mt-2 flex gap-2">
                    <button
                      onClick={() => complete(l.id)}
                      className="text-xs bg-accent-600 hover:bg-accent-500 text-white rounded px-3 py-1"
                    >
                      Mark done
                    </button>
                    <button
                      onClick={() => skip(l.id)}
                      className="text-xs bg-ink-700 hover:bg-ink-500 text-white rounded px-3 py-1"
                    >
                      Skip
                    </button>
                    <button
                      onClick={() => startQuiz(l.id)}
                      className="text-xs bg-ink-700 hover:bg-ink-500 text-white rounded px-3 py-1"
                    >
                      Take quiz
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-white mb-2">Resources ({resources.length})</h2>
        <ul className="space-y-1 text-sm">
          {resources.map((r) => (
            <li key={r.id} className="bg-ink-800 border border-ink-700 rounded px-3 py-2">
              <span className="text-white">{r.title}</span>
              <span className="ml-2 text-xs text-ink-300">
                {r.kind}
                {r.url ? ` · ${r.url}` : ""}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {activeQuiz && (
        <QuizRunner
          quiz={activeQuiz.quiz}
          onClose={() => setActiveQuiz(null)}
          onSubmitted={(attempt) => setActiveQuiz({ quiz: activeQuiz.quiz, attempt })}
        />
      )}
    </div>
  );
}

function AddResourceForm({ goalId, onAdded }: { goalId: string; onAdded: () => void }) {
  const [kind, setKind] = useState<"youtube_video" | "youtube_playlist" | "article" | "note" | "pdf">(
    "youtube_video",
  );
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      if (kind === "pdf" && file) {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("goal_id", goalId);
        const token = window.localStorage.getItem("coach.token") || "";
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}/resources/upload-pdf`,
          { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd },
        );
        if (!res.ok) throw new Error(`upload failed (${res.status})`);
      } else {
        await api("/resources", {
          method: "POST",
          json: { goal_id: goalId, kind, url: url || undefined, text: text || undefined },
        });
      }
      setUrl("");
      setText("");
      setFile(null);
      onAdded();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "add failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="bg-ink-800 border border-ink-700 rounded p-3 space-y-2 mb-3">
      <div className="flex gap-2 flex-wrap">
        {(["youtube_video", "youtube_playlist", "article", "pdf", "note"] as const).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setKind(k)}
            className={
              "text-xs px-3 py-1 rounded " +
              (kind === k ? "bg-accent-600 text-white" : "bg-ink-700 text-ink-300")
            }
          >
            {k}
          </button>
        ))}
      </div>
      {(kind === "youtube_video" || kind === "youtube_playlist" || kind === "article") && (
        <input
          required
          type="url"
          placeholder="https://…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
      )}
      {kind === "note" && (
        <textarea
          required
          placeholder="paste your note here…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white h-24"
        />
      )}
      {kind === "pdf" && (
        <input
          required
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-white"
        />
      )}
      {err && <p className="text-red-400 text-sm">{err}</p>}
      <button
        type="submit"
        disabled={busy}
        className="bg-accent-600 hover:bg-accent-500 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
      >
        {busy ? "Adding…" : "Add"}
      </button>
    </form>
  );
}