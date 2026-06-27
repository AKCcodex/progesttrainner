"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export function Navbar() {
  const { user, logout } = useAuth();
  return (
    <header className="bg-ink-800 border-b border-ink-700">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="font-bold text-white">
          🎓 Learning Coach
        </Link>
        {user ? (
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/dashboard" className="hover:text-white">Dashboard</Link>
            <Link href="/goals" className="hover:text-white">Goals</Link>
            <Link href="/resources" className="hover:text-white">Resources</Link>
            <Link href="/reviews" className="hover:text-white">Reviews</Link>
            <span className="text-ink-300">| {user.email}</span>
            <button onClick={logout} className="text-ink-300 hover:text-white">
              Logout
            </button>
          </nav>
        ) : (
          <nav className="flex gap-3 text-sm">
            <Link href="/login" className="hover:text-white">Login</Link>
            <Link href="/register" className="hover:text-white">Register</Link>
          </nav>
        )}
      </div>
    </header>
  );
}