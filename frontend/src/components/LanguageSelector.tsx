// frontend/components/LanguageSelector.tsx
import React from 'react';

interface LanguageSelectorProps {
  currentLang: string;
  onLanguageChange: (lang: string) => void;
}

export const languages = [
  { code: 'en', name: 'English' },
  { code: 'ta', name: 'தமிழ் (Tamil)' },
  { code: 'kn', name: 'ಕನ್ನಡ (Kannada)' },
  { code: 'te', name: 'తెలుగు (Telugu)' },
  { code: 'hi', name: 'हिन्दी (Hindi)' },
];

export default function LanguageSelector({ currentLang, onLanguageChange }: LanguageSelectorProps) {
  return (
    <div className="flex items-center space-x-2 bg-white p-2 rounded-lg shadow-sm border">
      <span className="text-sm font-medium text-gray-600">Language:</span>
      <select
        value={currentLang}
        onChange={(e) => onLanguageChange(e.target.value)}
        className="bg-transparent text-sm font-semibold text-gray-800 focus:outline-none cursor-pointer"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
}