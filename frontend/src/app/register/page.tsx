"use client";

import { api, setProfile, setToken, UserProfile } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<"patient" | "doctor">("patient");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api<UserProfile>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          role,
          name,
          specialization: role === "doctor" ? specialization : undefined,
        }),
      });
      const token = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(token.access_token);
      const profile = await api<UserProfile>("/auth/me");
      setProfile(profile);
      router.push(profile.role === "doctor" ? "/doctor" : "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <div className="mx-auto max-w-md card p-8">
      <h1 className="text-2xl font-semibold">Register</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <select className="w-full rounded-lg border px-3 py-2" value={role} onChange={(e) => setRole(e.target.value as "patient" | "doctor")}>
          <option value="patient">Patient</option>
          <option value="doctor">Doctor</option>
        </select>
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Password (min 8 chars)" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
        {role === "doctor" && (
          <input className="w-full rounded-lg border px-3 py-2" placeholder="Specialization" value={specialization} onChange={(e) => setSpecialization(e.target.value)} />
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full py-2" type="submit">Create account</button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already registered? <Link href="/login" className="text-teal-700">Login</Link>
      </p>
    </div>
  );
}
