"use client";

import { api, setProfile, setToken, UserProfile } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(token.access_token);
      const profile = await api<UserProfile>("/auth/me");
      setProfile(profile);
      router.push(profile.role === "doctor" ? "/doctor" : "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md card p-8">
      <h1 className="text-2xl font-semibold">Login</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full py-2" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <div className="mt-4 flex gap-2 text-xs">
        <button className="btn-secondary" type="button" onClick={() => { setEmail("patient@demo.medivault"); setPassword("password123"); }}>
          Demo patient
        </button>
        <button className="btn-secondary" type="button" onClick={() => { setEmail("doctor@demo.medivault"); setPassword("password123"); }}>
          Demo doctor
        </button>
      </div>
      <p className="mt-4 text-sm text-slate-600">
        No account? <Link href="/register" className="text-teal-700">Register</Link>
      </p>
    </div>
  );
}
