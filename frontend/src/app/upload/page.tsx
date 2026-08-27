"use client";

import { api, DocumentItem, ExtractionJob, uploadDocument } from "@/lib/api";
import Link from "next/link";
import { useState } from "react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<DocumentItem | null>(null);
  const [job, setJob] = useState<ExtractionJob | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function poll(documentId: string) {
    for (let i = 0; i < 20; i += 1) {
      const doc = await api<DocumentItem>(`/documents/${documentId}`);
      setResult(doc);
      if (["validated", "failed", "human_review"].includes(doc.processing_status)) {
        try {
          setJob(await api<ExtractionJob>(`/documents/${documentId}/extraction`));
        } catch {
          /* job may still be writing */
        }
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    setJob(null);
    try {
      const doc = await uploadDocument(file);
      setResult(doc);
      await poll(doc.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl card p-6">
      <h1 className="text-2xl font-semibold">Upload Medical Document</h1>
      <p className="mt-2 text-sm text-slate-600">
        Supported: PDF, JPEG, PNG. Max 25MB. Text PDFs are extracted locally; image OCR is a production swap-in.
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button disabled={loading} className="btn-primary" type="submit">
          {loading ? "Uploading & extracting..." : "Upload & Process"}
        </button>
      </form>
      {result && (
        <div className="mt-6 rounded-xl border border-teal-100 bg-teal-50 p-4 text-sm">
          <p>
            <strong>Uploaded:</strong> {result.filename}
          </p>
          <p>
            <strong>Status:</strong> {result.processing_status.replace("_", " ")}
          </p>
          {job?.extracted_json ? (
            <p className="mt-2 text-slate-600">
              Extracted confidence {(job.extracted_json.confidence as number) ?? "—"}. Review facts on the{" "}
              <Link href="/timeline" className="text-teal-800 underline">
                timeline
              </Link>{" "}
              or{" "}
              <Link href="/documents" className="text-teal-800 underline">
                documents
              </Link>
              .
            </p>
          ) : (
            <p className="mt-2 text-slate-600">Check Timeline after extraction completes.</p>
          )}
        </div>
      )}
    </div>
  );
}
