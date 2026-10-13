import { useState, useCallback } from 'react';
import { Message, Source } from '../types/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState<string>(() => crypto.randomUUID());

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim()) return;

    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    const newMessages = [
      ...messages,
      { id: userMsgId, role: 'user' as const, content: question, timestamp: Date.now() },
    ];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/flask/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
      });

      if (!res.ok) throw new Error('Failed to fetch response');
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          emergency: data.emergency,
          timestamp: Date.now(),
        },
      ]);
    } catch (err: any) {
      setError(err.message || 'Error communicating with server');
    } finally {
      setIsLoading(false);
    }
  }, [messages, sessionId]);

  const clearMessages = () => setMessages([]);

  const sendFeedback = async (messageId: string, rating: 'up' | 'down') => {
    // We would need the original question and answer for feedback.
    // Finding them from state:
    const assistantMsgIdx = messages.findIndex(m => m.id === messageId);
    if (assistantMsgIdx <= 0) return;
    const assistantMsg = messages[assistantMsgIdx];
    const userMsg = messages[assistantMsgIdx - 1];
    
    try {
      await fetch('/api/flask/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMsg.content,
          answer: assistantMsg.content,
          rating,
          session_id: sessionId
        })
      });
    } catch (err) {
      console.error("Failed to send feedback", err);
    }
  };

  return { messages, setMessages, isLoading, setIsLoading, error, sessionId, sendMessage, clearMessages, sendFeedback };
}
