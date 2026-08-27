"use client";

import { api, RECORD_TYPES, TimelineItem } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";

export default function TimelinePage() {
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (type !== "all") params.append("record_type", type);
    api<{ items: TimelineItem[] }>(`/records/timeline?${params.toString()}`)
      .then((r) => setItems(r.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load timeline"));
  }, [query, type]);

  const grouped = useMemo(() => {
    const map = new Map<string, TimelineItem[]>();
    for (const item of items) {
      const key = item.effective_time || "Undated";
      map.set(key, [...(map.get(key) || []), item]);
    }
    return Array.from(map.entries());
  }, [items]);

  return (
    <div className="card p-6">
      <h1 className="text-2xl font-semibold">Medical Timeline</h1>
      <p className="mt-2 text-sm text-slate-600">Structured records extracted from your documents, grouped by document date.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <input
          className="rounded-lg border px-3 py-2 text-sm"
          placeholder="Search labs, meds, conditions..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select className="rounded-lg border px-3 py-2 text-sm" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="all">All types</option>
          {RECORD_TYPES.map((rt) => (
            <option key={rt.id} value={rt.id}>
              {rt.label}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      <div className="mt-6 space-y-6">
        {grouped.map(([date, group]) => (
          <section key={date}>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{date}</h2>
            <div className="mt-2 space-y-3">
              {group.map((item) => (
                <div key={item.id} className="rounded-xl border p-4">
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-teal-100 px-2 py-0.5 text-xs uppercase text-teal-800">{item.type}</span>
                    {item.interpretation && (
                      <span className="text-xs capitalize text-slate-500">{item.interpretation}</span>
                    )}
                  </div>
                  <div className="mt-2 font-medium">{item.display_name}</div>
                  {item.value && (
                    <div className="text-sm text-slate-600">
                      {item.value}
                      {item.unit ? ` ${item.unit}` : ""}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        ))}
        {items.length === 0 && <p className="text-slate-500">No timeline records yet. Upload a document first.</p>}
      </div>
    </div>
  );
}
