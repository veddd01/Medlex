'use client';
import { useState } from 'react';

export default function HistoryPage() {
  const [sessionId, setSessionId] = useState('');
  const [history, setHistory] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHistory = async () => {
    if (!sessionId.trim()) return;
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch(`/api/flask/history/${sessionId}`);
      if (!res.ok) {
        throw new Error('History not found');
      }
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch history');
      setHistory(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto w-full mt-8">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Conversation History</h1>
      
      <div className="flex gap-4 mb-8">
        <input 
          type="text" 
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Enter Session ID..."
          className="flex-1 bg-white border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-medical-500"
        />
        <button 
          onClick={fetchHistory}
          disabled={loading || !sessionId.trim()}
          className="bg-medical-600 text-white rounded-lg px-6 font-semibold hover:bg-medical-700 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Load History'}
        </button>
      </div>

      {error && <div className="text-red-600 bg-red-50 p-4 rounded-md mb-6">{error}</div>}

      {history && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {history.length === 0 ? (
            <div className="p-8 text-center text-slate-500">No messages in this session.</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {history.map((turn, idx) => (
                <div key={idx} className="p-6">
                  <div className="mb-4">
                    <span className="font-semibold text-slate-800 mb-1 block">Question:</span>
                    <p className="text-slate-700 bg-slate-50 p-3 rounded">{turn.question}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800 mb-1 block">Answer:</span>
                    <p className="text-slate-700 whitespace-pre-wrap">{turn.answer}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
