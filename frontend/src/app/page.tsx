'use client';
import { useState } from 'react';
import ChatWindow from '@/components/ChatWindow';
import { useStreamingAnswer } from '@/hooks/useStreamingAnswer';
import { useChat } from '@/hooks/useChat';
import { Message } from '@/types/api';

export default function Home() {
  const { messages, setMessages, error, sessionId, clearMessages, sendFeedback } = useChat();
  const { streamMessage, isStreaming } = useStreamingAnswer(sessionId, setMessages, messages);

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6 bg-slate-50 h-[calc(100vh-140px)]">
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm text-center max-w-4xl mx-auto w-full">
          {error}
        </div>
      )}
      <ChatWindow 
        messages={messages} 
        isLoading={isStreaming} 
        onSendMessage={streamMessage} 
        onClear={clearMessages}
        onFeedback={sendFeedback}
      />
    </div>
  );
}
