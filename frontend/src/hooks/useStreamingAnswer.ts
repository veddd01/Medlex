import { useState, useCallback } from 'react';
import { Message } from '../types/api';

export function useStreamingAnswer(sessionId: string, onUpdate: (messages: Message[]) => void, messages: Message[]) {
  const [isStreaming, setIsStreaming] = useState(false);

  const streamMessage = useCallback(async (question: string) => {
    if (!question.trim()) return;

    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    const newMessages = [
      ...messages,
      { id: userMsgId, role: 'user' as const, content: question, timestamp: Date.now() },
    ];
    onUpdate(newMessages);
    setIsStreaming(true);

    try {
      const res = await fetch('/api/flask/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
      });

      if (!res.ok) throw new Error('Failed to fetch streaming response');
      if (!res.body) throw new Error('No readable stream available');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      // Add empty assistant message to update
      let assistantMsg: Message = { id: assistantMsgId, role: 'assistant', content: '', timestamp: Date.now() };
      let currentMessages = [...newMessages, assistantMsg];
      onUpdate(currentMessages);

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.token) {
                  assistantMsg.content += data.token;
                  currentMessages = [...newMessages, { ...assistantMsg }];
                  onUpdate(currentMessages);
                } else if (data.done) {
                  assistantMsg.sources = data.sources;
                  assistantMsg.emergency = data.emergency;
                  currentMessages = [...newMessages, { ...assistantMsg }];
                  onUpdate(currentMessages);
                }
              } catch (e) {
                console.error("Error parsing stream chunk", e);
              }
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsStreaming(false);
    }
  }, [messages, sessionId, onUpdate]);

  return { streamMessage, isStreaming };
}
