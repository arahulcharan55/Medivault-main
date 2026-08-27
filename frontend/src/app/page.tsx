'use client';
import { useState } from 'react';
import Link from 'next/link';
import LanguageSelector from '@/components/LanguageSelector';
import VoiceAssistant from '@/components/VoiceAssistant';
import AISummary from '@/components/AISummary';
import ChatSupport from '@/components/ChatSupport';

export default function Dashboard() {
  const [currentLang, setCurrentLang] = useState('en');

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      {/* Top Header & Language Selector */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Welcome, ram</h1>
          <p className="text-sm text-gray-500">Upload reports, review extracted facts, and control who can see them.</p>
        </div>
        <LanguageSelector currentLang={currentLang} onLanguageChange={setCurrentLang} />
      </div>

      {/* Action Navigation Buttons (Upload, Consents, FHIR, Login) */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Link href="/upload" className="bg-teal-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-teal-800 shadow-sm">
          Upload Document
        </Link>
        <Link href="/consents" className="bg-white border text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 shadow-sm">
          Manage Consents
        </Link>
        <Link href="/documents" className="bg-white border text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 shadow-sm">
          View Documents
        </Link>
        <Link href="/login" className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-300 ml-auto">
          Login / Account
        </Link>
      </div>

      {/* NEW: AI Voice Assistant (Microphone & Hospital Map Search) */}
      <VoiceAssistant />

      {/* NEW: AI Medical Records Summary */}
      <AISummary />

      {/* Original MediVault Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 my-6">
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <span className="text-xs text-gray-500 uppercase font-semibold">Documents</span>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">1</h2>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <span className="text-xs text-gray-500 uppercase font-semibold">Observations</span>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">0</h2>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <span className="text-xs text-gray-500 uppercase font-semibold">Medications</span>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">0</h2>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <span className="text-xs text-gray-500 uppercase font-semibold">Allergies</span>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">0</h2>
        </div>
      </div>

      {/* Original MediVault Recent Documents & Timeline Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-800">Recent Documents</h3>
            <Link href="/documents" className="text-sm text-teal-600 hover:underline">View all</Link>
          </div>
          <div className="text-sm text-gray-600 border-b pb-2 flex justify-between items-center">
            <span>WhatsApp Image 2026-08-26 at 22.38.14.jpeg</span>
            <span className="text-red-500 text-xs font-semibold bg-red-50 px-2 py-0.5 rounded">Failed</span>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-800">Recent Timeline</h3>
            <Link href="/documents" className="text-sm text-teal-600 hover:underline">View all</Link>
          </div>
          <p className="text-sm text-gray-400">No structured records yet.</p>
        </div>
      </div>

      {/* NEW: Floating Chat Support Widget */}
      <ChatSupport />
    </main>
  );
}