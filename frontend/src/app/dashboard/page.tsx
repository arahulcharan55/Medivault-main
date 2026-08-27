"use client";

import { api, DocumentItem, getProfile, HealthSummary, TimelineItem, UserProfile } from "@/lib/api";
import Link from "next/link";
import { useEffect, useState } from "react";

function interpretationClass(flag?: string | null) {
  if (flag === "high") return "text-red-700 bg-red-50";
  if (flag === "low") return "text-amber-800 bg-amber-50";
  if (flag === "normal") return "text-emerald-800 bg-emerald-50";
  return "text-slate-600 bg-slate-50";
}

export default function DashboardPage() {
  const [profile] = useState<UserProfile | null>(() => getProfile<UserProfile>());
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [summary, setSummary] = useState<HealthSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<DocumentItem[]>("/documents"),
      api<{ items: TimelineItem[] }>("/records/timeline"),
      api<HealthSummary>("/records/summary"),
    ])
      .then(([docs, tl, sum]) => {
        setDocuments(docs);
        setTimeline(tl.items.slice(0, 6));
        setSummary(sum);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, []);

  async function exportFhir() {
    const bundle = await api<Record<string, unknown>>("/records/fhir");
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/fhir+json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "medivault-fhir-bundle.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  const counts = summary?.counts;

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h1 className="text-2xl font-semibold">Welcome, {profile?.name || "Patient"}</h1>
        <p className="mt-2 text-slate-600">Upload reports, review extracted facts, and control who can see them.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/upload" className="btn-primary">
            Upload Document
          </Link>
          <Link href="/consents" className="btn-secondary">
            Manage Consents
          </Link>
          <button onClick={exportFhir} className="btn-secondary">
            Export FHIR
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Documents", counts?.documents ?? documents.length],
          ["Observations", counts?.observations ?? "—"],
          ["Medications", counts?.medications ?? "—"],
          ["Allergies", counts?.allergies ?? "—"],
        ].map(([label, value]) => (
          <div key={label} className="card p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
            <div className="mt-1 text-2xl font-semibold text-teal-800">{value}</div>
          </div>
        ))}
      </div>

      {summary?.abnormal_observations?.length ? (
        <section className="card p-6">
          <h2 className="font-semibold">Flagged values</h2>
          <p className="text-xs text-slate-500">Prototype reference ranges only — not clinical decision support.</p>
          <ul className="mt-3 grid gap-2 md:grid-cols-2">
            {summary.abnormal_observations.map((obs) => (
              <li key={obs.id} className={`rounded-lg px-3 py-2 text-sm ${interpretationClass(obs.interpretation)}`}>
                <span className="font-medium">{obs.display_name}</span> {obs.value}
                {obs.unit ? ` ${obs.unit}` : ""} · {obs.interpretation}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        <section className="card p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Recent Documents</h2>
            <Link href="/documents" className="text-sm text-teal-700">
              View all
            </Link>
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {documents.slice(0, 5).map((d) => (
              <li key={d.id} className="flex justify-between border-b py-2">
                <span>{d.filename}</span>
                <span className="capitalize text-slate-500">{d.processing_status.replace("_", " ")}</span>
              </li>
            ))}
            {documents.length === 0 && <li className="text-slate-500">No documents yet.</li>}
          </ul>
        </section>
        <section className="card p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Recent Timeline</h2>
            <Link href="/timeline" className="text-sm text-teal-700">
              View all
            </Link>
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {timeline.map((t) => (
              <li key={t.id} className="border-b py-2">
                <div className="font-medium">{t.display_name}</div>
                <div className="text-slate-500">
                  {t.type}
                  {t.value ? ` · ${t.value}${t.unit ? ` ${t.unit}` : ""}` : ""}
                </div>
              </li>
            ))}
            {timeline.length === 0 && <li className="text-slate-500">No structured records yet.</li>}
          </ul>
        </section>
      </div>
    </div>
  );
}
