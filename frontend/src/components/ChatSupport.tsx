import React, { useState } from 'react';

export default function ChatSupport() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! How can I help you with your health records today?' }
  ]);
  const [input, setInput] = useState('');

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    setInput('');

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: 'I am your AI health assistant. You can upload reports, check summaries, or search for hospitals using voice.' }
      ]);
    }, 1000);
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {!isOpen ? (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition"
        >
          💬 Chat Support
        </button>
      ) : (
        <div className="bg-white w-80 h-96 rounded-2xl shadow-2xl border flex flex-col overflow-hidden">
          <div className="bg-blue-600 text-white p-3 flex justify-between items-center">
            <h4 className="font-semibold text-sm">MediVault Support</h4>
            <button onClick={() => setIsOpen(false)} className="text-white font-bold">&times;</button>
          </div>
          <div className="flex-1 p-3 overflow-y-auto space-y-2 text-sm">
            {messages.map((m, i) => (
              <div key={i} className={`p-2 rounded-lg max-w-[80%] ${m.sender === 'user' ? 'bg-blue-100 ml-auto text-blue-900' : 'bg-gray-100 text-gray-800'}`}>
                {m.text}
              </div>
            ))}
          </div>
          <form onSubmit={sendMessage} className="p-2 border-t flex">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 border rounded-l-lg px-3 py-1.5 text-sm focus:outline-none"
            />
            <button type="submit" className="bg-blue-600 text-white px-4 rounded-r-lg text-sm">Send</button>
          </form>
        </div>
      )}
    </div>
  );
}