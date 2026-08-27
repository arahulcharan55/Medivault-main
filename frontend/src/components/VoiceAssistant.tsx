import React, { useState } from 'react';

export default function VoiceAssistant() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [mapQuery, setMapQuery] = useState('');

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Try Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);

      if (text.toLowerCase().includes('hospital') || text.toLowerCase().includes('doctor') || text.toLowerCase().includes('hospital எங்க இருக்கு')) {
        const query = encodeURIComponent('hospitals near me');
        setMapQuery(`https://www.google.com/maps/search/${query}`);
      }
    };

    recognition.start();
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-md border my-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-700">AI Voice Assistant</h3>
        <button
          onClick={startListening}
          className={`flex items-center px-4 py-2 rounded-full text-white font-medium transition ${
            isListening ? 'bg-red-500 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          🎤 {isListening ? 'Listening...' : 'Speak to Assistant'}
        </button>
      </div>

      {transcript && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
          <p><strong>You asked:</strong> "{transcript}"</p>
        </div>
      )}

      {mapQuery && (
        <div className="mt-3">
          <a
            href={mapQuery}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-green-700"
          >
            📍 View Hospital Locations on Google Maps
          </a>
        </div>
      )}
    </div>
  );
}