"use client";

import { api, AuditItem } from "@/lib/api";
import { useEffect, useState } from "react";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<AuditItem[]>("/audit/logs")
      .then(setLogs)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load audit logs"));
  }, []);

  return (
    <div className="card p-6">
      <h1 className="text-2xl font-semibold">Access Logs</h1>
      <p className="mt-2 text-sm text-slate-600">Append-only trail of sensitive actions on your records.</p>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2">Time</th>
              <th>Action</th>
              <th>Outcome</th>
              <th>Actor</th>
              <th>Resource</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-b">
                <td className="py-2">{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.action}</td>
                <td className={log.outcome === "failure" ? "text-red-700" : "text-emerald-700"}>{log.outcome}</td>
                <td>{log.actor_role}</td>
                <td>{log.resource_type || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {logs.length === 0 && <p className="mt-4 text-slate-500">No audit events yet.</p>}
    </div>
  );
}
