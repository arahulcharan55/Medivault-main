"use client";

import { api, DocumentItem, ExtractionJob } from "@/lib/api";
import { useEffect, useState } from "react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<DocumentItem | null>(null);
  const [job, setJob] = useState<ExtractionJob | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setDocuments(await api<DocumentItem[]>("/documents"));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load documents"));
  }, []);

  async function openDoc(doc: DocumentItem) {
    setSelected(doc);
    setError("");
    try {
      setJob(await api<ExtractionJob>(`/documents/${doc.id}/extraction`));
    } catch {
      setJob(null);
    }
  }

  async function review(action: "confirm" | "reject") {
    if (!selected) return;
    const updated = await api<ExtractionJob>(`/documents/${selected.id}/review`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    setJob(updated);
    await load();
  }

  async function reprocess() {
    if (!selected) return;
    const updated = await api<ExtractionJob>(`/documents/${selected.id}/process`, { method: "POST" });
    setJob(updated);
    await load();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="card p-6">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <p className="mt-2 text-sm text-slate-600">Original files remain the source of truth. Extraction is assistive.</p>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <ul className="mt-4 space-y-2">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => openDoc(doc)}
                className={`w-full rounded-xl border px-4 py-3 text-left text-sm ${selected?.id === doc.id ? "border-teal-600 bg-teal-50" : ""}`}
              >
                <div className="font-medium">{doc.filename}</div>
                <div className="text-xs text-slate-500">
                  {doc.processing_status.replace("_", " ")} · {new Date(doc.uploaded_at).toLocaleString()}
                </div>
              </button>
            </li>
          ))}
          {documents.length === 0 && <li className="text-slate-500">No documents uploaded.</li>}
        </ul>
      </section>
      <section className="card p-6">
        <h2 className="font-semibold">Extraction review</h2>
        {!selected && <p className="mt-3 text-sm text-slate-500">Select a document to inspect extracted JSON and provenance text.</p>}
        {selected && (
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <button className="btn-secondary" onClick={reprocess}>
                Re-run extraction
              </button>
              {selected.processing_status === "human_review" && (
                <>
                  <button className="btn-primary" onClick={() => review("confirm")}>
                    Confirm facts
                  </button>
                  <button className="rounded-lg bg-red-100 px-3 py-2 text-red-700" onClick={() => review("reject")}>
                    Reject
                  </button>
                </>
              )}
            </div>
            {job?.error_message && <p className="text-red-600">{job.error_message}</p>}
            {job?.extracted_json && (
              <pre className="max-h-80 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify(job.extracted_json, null, 2)}
              </pre>
            )}
            {job?.raw_ocr_text && (
              <div>
                <div className="text-xs uppercase text-slate-500">Source text</div>
                <p className="mt-1 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs">{job.raw_ocr_text}</p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
