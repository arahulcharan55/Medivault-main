import React, { useState } from 'react';

export default function AISummary() {
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);

  const generateSummary = async () => {
    setLoading(true);
    setTimeout(() => {
      setSummary("AI Summary: Patient vitals are stable. Recent blood test indicates normal sugar levels. Recommended follow-up in 3 months.");
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border border-blue-100 my-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-blue-900">✨ AI Medical Records Summary</h3>
        <button
          onClick={generateSummary}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Generate Summary'}
        </button>
      </div>
      {summary && (
        <p className="mt-3 text-sm text-gray-700 bg-white p-3 rounded-lg border border-blue-200">
          {summary}
        </p>
      )}
    </div>
  );
}