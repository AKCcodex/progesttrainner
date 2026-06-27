"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Quiz, QuizAttempt, QuizQuestion } from "@/lib/types";

interface Props {
  quiz: Quiz;
  attempt?: QuizAttempt;
  onClose: () => void;
  onSubmitted: (attempt: QuizAttempt) => void;
}

export function QuizRunner({ quiz, attempt, onClose, onSubmitted }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (attempt) {
    return (
      <Modal onClose={onClose} title={`Quiz results: ${Math.round(attempt.score * 100)}%`}>
        <pre className="text-xs text-ink-300 whitespace-pre-wrap max-h-96 overflow-auto">
          {JSON.stringify(attempt.feedback, null, 2)}
        </pre>
      </Modal>
    );
  }

  async function submit() {
    setBusy(true);
    setErr(null);
    try {
      const payload = Object.entries(answers).map(([qid, ans]) => ({
        question_id: qid,
        answer: ans,
      }));
      const att = await api<QuizAttempt>(`/quizzes/${quiz.id}/submit`, {
        method: "POST",
        json: { answers: payload },
      });
      onSubmitted(att);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "submit failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal onClose={onClose} title={quiz.title || "Quiz"}>
      <ol className="space-y-4">
        {quiz.questions.map((q, idx) => (
          <li key={q.id} className="bg-ink-800 border border-ink-700 rounded p-3">
            <div className="text-white">
              <span className="text-ink-300 mr-2">{idx + 1}.</span>
              {q.question}
            </div>
            <QuestionInput q={q} value={answers[q.id] || ""} onChange={(v) => setAnswers({ ...answers, [q.id]: v })} />
          </li>
        ))}
      </ol>
      {err && <p className="text-red-400 text-sm mt-3">{err}</p>}
      <button
        onClick={submit}
        disabled={busy}
        className="mt-4 w-full bg-accent-600 hover:bg-accent-500 text-white rounded py-2 disabled:opacity-50"
      >
        {busy ? "Scoring…" : "Submit"}
      </button>
    </Modal>
  );
}

function QuestionInput({ q, value, onChange }: { q: QuizQuestion; value: string; onChange: (v: string) => void }) {
  if (q.kind === "mcq" && q.options?.length) {
    return (
      <div className="mt-2 space-y-1">
        {q.options.map((opt, i) => (
          <label key={i} className="flex items-center gap-2 text-sm text-ink-300">
            <input
              type="radio"
              name={q.id}
              value={opt}
              checked={value === opt}
              onChange={() => onChange(opt)}
            />
            {opt}
          </label>
        ))}
      </div>
    );
  }
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-2 w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white h-20"
    />
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
      <div className="bg-ink-900 border border-ink-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-ink-300 hover:text-white">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}