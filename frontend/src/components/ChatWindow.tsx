'use client';
import { useState, useRef, useEffect } from 'react';
import { Message } from '../types/api';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import SuggestionChips from './SuggestionChips';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (msg: string) => void;
  onClear: () => void;
  onFeedback: (id: string, rating: 'up'|'down') => void;
}

export default function ChatWindow({ messages, isLoading, onSendMessage, onClear, onFeedback }: ChatWindowProps) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 w-full max-w-4xl mx-auto rounded-xl shadow-sm border border-slate-200 overflow-hidden my-4">
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200">
        <h2 className="font-semibold text-slate-800">Medical Consultation</h2>
        {messages.length > 0 && (
          <button onClick={onClear} className="text-sm text-slate-500 hover:text-red-500 transition-colors">
            Clear Chat
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-16 h-16 bg-medical-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-3xl text-medical-600">🩺</span>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">Welcome to MedLex</h3>
            <p className="text-slate-500 max-w-md mx-auto mb-6">
              I am your AI medical assistant. Ask me questions about symptoms, conditions, or treatments.
            </p>
            <SuggestionChips onSelect={onSendMessage} />
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} onFeedback={onFeedback} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Type your medical question here..."
            className="flex-1 resize-none bg-slate-50 border border-slate-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-transparent max-h-32 min-h-[52px]"
            rows={1}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-medical-600 text-white rounded-lg px-5 font-medium hover:bg-medical-700 focus:outline-none focus:ring-2 focus:ring-medical-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center h-[52px]"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
        <p className="text-center text-xs text-slate-400 mt-2">
          MedLex can make mistakes. Verify important information with a doctor.
        </p>
      </div>
    </div>
  );
}
