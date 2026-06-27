"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return (
    <div className="text-center mt-24">
      <h1 className="text-4xl font-bold text-white mb-2">🎓 Personal AI Learning Coach</h1>
      <p className="text-ink-300 max-w-md mx-auto mb-6">
        A disciplined learning coach that turns your goals + resources into a daily plan,
        quizzes you on the material, and adapts to your pace.
      </p>
      {loading ? (
        <p className="text-ink-300">Loading…</p>
      ) : (
        <div className="flex gap-3 justify-center">
          <a href="/login" className="bg-accent-600 hover:bg-accent-500 text-white rounded px-4 py-2">
            Log in
          </a>
          <a href="/register" className="bg-ink-700 hover:bg-ink-500 text-white rounded px-4 py-2">
            Create account
          </a>
        </div>
      )}
    </div>
  );
}