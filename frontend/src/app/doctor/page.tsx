"use client";

import { api, DocumentItem, HealthSummary, TimelineItem } from "@/lib/api";
import { useEffect, useState } from "react";

type GrantedPatient = {
  patient_id: string;
  patient_name?: string | null;
  grant_id: string;
  expires_at: string;
  scope?: { record_types?: string[] };
};

export default function DoctorPortalPage() {
  const [patients, setPatients] = useState<GrantedPatient[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [summary, setSummary] = useState<HealthSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<GrantedPatient[]>("/doctor/patients")
      .then(setPatients)
      .catch((e) => setError(e.message));
  }, []);

  async function loadPatient(patientId: string) {
    setSelected(patientId);
    setError("");
    try {
      const [tl, docs, sum] = await Promise.all([
        api<{ items: TimelineItem[] }>(`/doctor/patients/${patientId}/timeline`),
        api<DocumentItem[]>(`/doctor/patients/${patientId}/documents`),
        api<HealthSummary>(`/doctor/patients/${patientId}/summary`),
      ]);
      setTimeline(tl.items);
      setDocuments(docs);
      setSummary(sum);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Access denied");
      setTimeline([]);
      setDocuments([]);
      setSummary(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h1 className="text-2xl font-semibold">Doctor Portal</h1>
        <p className="mt-2 text-sm text-slate-600">Only records covered by an active, unrevoked patient grant are visible.</p>
      </div>

      <section className="card p-6">
        <h2 className="font-semibold">Patients With Active Grants</h2>
        <div className="mt-4 space-y-2">
          {patients.map((p) => (
            <button
              key={p.grant_id}
              onClick={() => loadPatient(p.patient_id)}
              className={`block w-full rounded-xl border px-4 py-3 text-left ${selected === p.patient_id ? "border-teal-600 bg-teal-50" : ""}`}
            >
              <div className="font-medium">{p.patient_name || p.patient_id}</div>
              <div className="text-xs text-slate-500">Expires {new Date(p.expires_at).toLocaleString()}</div>
            </button>
          ))}
          {patients.length === 0 && <p className="text-slate-500">No active patient grants.</p>}
        </div>
      </section>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {summary && (
        <section className="grid gap-3 sm:grid-cols-3">
          <div className="card p-4 text-sm">
            <div className="text-slate-500">Observations</div>
            <div className="text-xl font-semibold">{summary.counts.observations}</div>
          </div>
          <div className="card p-4 text-sm">
            <div className="text-slate-500">Medications</div>
            <div className="text-xl font-semibold">{summary.counts.medications}</div>
          </div>
          <div className="card p-4 text-sm">
            <div className="text-slate-500">Allergies</div>
            <div className="text-xl font-semibold">{summary.counts.allergies}</div>
          </div>
        </section>
      )}

      {documents.length > 0 && (
        <section className="card p-6">
          <h2 className="font-semibold">Shared Documents</h2>
          <ul className="mt-3 text-sm">
            {documents.map((d) => (
              <li key={d.id} className="flex justify-between border-b py-2">
                <span>{d.filename}</span>
                <span className="text-slate-500">{d.processing_status}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {timeline.length > 0 && (
        <section className="card p-6">
          <h2 className="font-semibold">Shared Timeline</h2>
          <div className="mt-4 space-y-3">
            {timeline.map((item) => (
              <div key={item.id} className="rounded-xl border p-3 text-sm">
                <div className="text-xs uppercase text-teal-700">{item.type}</div>
                <div className="font-medium">{item.display_name}</div>
                <div className="text-slate-500">
                  {item.value ? `${item.value}${item.unit ? ` ${item.unit}` : ""}` : ""}
                  {item.interpretation ? ` · ${item.interpretation}` : ""}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {selected && timeline.length === 0 && !error && (
        <p className="text-sm text-slate-500">Grant is active, but there are no shared records in scope yet.</p>
      )}
    </div>
  );
}
