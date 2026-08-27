"use client";

import { api, ConsentItem, DoctorOption, RECORD_TYPES } from "@/lib/api";
import { useEffect, useState } from "react";

export default function ConsentsPage() {
  const [doctors, setDoctors] = useState<DoctorOption[]>([]);
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [doctorId, setDoctorId] = useState("");
  const [days, setDays] = useState(7);
  const [types, setTypes] = useState<string[]>(RECORD_TYPES.map((t) => t.id));
  const [error, setError] = useState("");

  async function load() {
    const [grants, list] = await Promise.all([
      api<ConsentItem[]>("/consents"),
      api<DoctorOption[]>("/doctors").catch(() => api<DoctorOption[]>("/audit/doctors")),
    ]);
    setConsents(grants);
    setDoctors(list);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load consents"));
  }, []);

  function toggleType(id: string) {
    setTypes((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  async function createGrant() {
    if (!doctorId || types.length === 0) return;
    setError("");
    const expires = new Date();
    expires.setDate(expires.getDate() + days);
    try {
      await api("/consents", {
        method: "POST",
        body: JSON.stringify({
          doctor_id: doctorId,
          scope: { record_types: types, include_timeline: true },
          permissions: ["read"],
          expires_at: expires.toISOString(),
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create grant");
    }
  }

  async function revoke(id: string) {
    await api(`/consents/${id}/revoke`, { method: "PATCH" });
    await load();
  }

  return (
    <div className="space-y-6">
      <section className="card p-6">
        <h1 className="text-2xl font-semibold">Consent Manager</h1>
        <p className="mt-2 text-sm text-slate-600">Grant scoped, time-bound access. Revocation is enforced independently of JWT expiry.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <select className="rounded-lg border px-3 py-2" value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
            <option value="">Select doctor</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
                {d.specialization ? ` · ${d.specialization}` : ""}
              </option>
            ))}
          </select>
          <select className="rounded-lg border px-3 py-2" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={1}>1 day</option>
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {RECORD_TYPES.map((rt) => (
            <label key={rt.id} className="flex items-center gap-2 rounded-full border px-3 py-1 text-sm">
              <input type="checkbox" checked={types.includes(rt.id)} onChange={() => toggleType(rt.id)} />
              {rt.label}
            </label>
          ))}
        </div>
        <button onClick={createGrant} className="btn-primary mt-4">
          Create grant
        </button>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </section>

      <section className="card p-6">
        <h2 className="font-semibold">Your Share Grants</h2>
        <div className="mt-4 space-y-3">
          {consents.map((c) => (
            <div key={c.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4 text-sm">
              <div>
                <div className="font-medium">{c.doctor_name || c.doctor_id}</div>
                <div className="text-slate-500">
                  Status: {c.status} · Expires: {new Date(c.expires_at).toLocaleString()}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Scope: {Array.isArray(c.scope.record_types) ? (c.scope.record_types as string[]).join(", ") : "all records"}
                </div>
              </div>
              {c.status === "active" && (
                <button onClick={() => revoke(c.id)} className="rounded-lg bg-red-100 px-3 py-1 text-red-700">
                  Revoke
                </button>
              )}
            </div>
          ))}
          {consents.length === 0 && <p className="text-slate-500">No grants yet.</p>}
        </div>
      </section>
    </div>
  );
}
