"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", timezone: "UTC" });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await register(form.email, form.password, form.full_name, form.timezone);
      router.push("/dashboard");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-12 bg-ink-800 border border-ink-700 rounded-lg p-6">
      <h1 className="text-xl font-bold text-white mb-4">Create your account</h1>
      <form onSubmit={submit} className="space-y-3">
        <input
          required
          placeholder="full name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
        <input
          type="email"
          required
          placeholder="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="password (8+ chars)"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
        <input
          placeholder="timezone (e.g. UTC, America/New_York)"
          value={form.timezone}
          onChange={(e) => setForm({ ...form, timezone: e.target.value })}
          className="w-full bg-ink-900 border border-ink-700 rounded px-3 py-2 text-white"
        />
        {err && <p className="text-red-400 text-sm">{err}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-accent-600 hover:bg-accent-500 text-white rounded py-2 disabled:opacity-50"
        >
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="text-sm text-ink-300 mt-3">
        Already have one? <Link href="/login" className="text-accent-500 underline">Log in</Link>.
      </p>
    </div>
  );
}