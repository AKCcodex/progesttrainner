"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Resource } from "@/lib/types";

export default function ResourcesPage() {
  const { user } = useAuth();
  const [resources, setResources] = useState<Resource[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api<Resource[]>("/resources")
      .then(setResources)
      .catch((e) => setErr(String(e)));
  }, [user]);

  if (!user) return <p>Please log in.</p>;
  if (err) return <p className="text-red-400">{err}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-4">Resources</h1>
      {resources.length === 0 ? (
        <p className="text-ink-300">
          No resources yet. Open a goal and add videos, articles, PDFs, or notes.
        </p>
      ) : (
        <ul className="space-y-2">
          {resources.map((r) => (
            <li key={r.id} className="bg-ink-800 border border-ink-700 rounded p-3">
              <Link href={r.url || "#"} target="_blank" className="font-semibold text-white hover:underline">
                {r.title}
              </Link>
              <div className="text-xs text-ink-300 mt-1">
                {r.kind}
                {r.url ? ` · ${r.url}` : ""}
                {r.goal_id ? ` · linked to a goal` : " · unlinked"}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}