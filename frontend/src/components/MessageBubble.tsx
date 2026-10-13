import { Message } from '../types/api';
import SourceCitation from './SourceCitation';
import EmergencyBanner from './EmergencyBanner';

export default function MessageBubble({ 
  message, 
  onFeedback 
}: { 
  message: Message; 
  onFeedback?: (id: string, rating: 'up' | 'down') => void;
}) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex flex-col w-full ${isUser ? 'items-end' : 'items-start'} mb-6`}>
      {message.emergency && !isUser && (
        <div className="max-w-[85%] w-full mb-2">
          <EmergencyBanner />
        </div>
      )}
      
      <div 
        className={`max-w-[85%] rounded-2xl px-5 py-4 ${
          isUser 
            ? 'bg-medical-600 text-white rounded-tr-sm shadow-md' 
            : 'bg-white text-slate-800 border border-slate-200 rounded-tl-sm shadow-sm'
        }`}
      >
        <div className={`markdown-body ${isUser ? 'text-white' : 'text-slate-800'}`}>
          {message.content.split('\\n').map((line, i) => (
            <p key={i} className="mb-2 last:mb-0 min-h-[1rem]">
              {line}
            </p>
          ))}
          {!message.content && !isUser && <span className="animate-pulse">...</span>}
        </div>
        
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Sources</h4>
            <div className="flex flex-col gap-1">
              {message.sources.map((src, i) => (
                <SourceCitation key={i} source={src} />
              ))}
            </div>
          </div>
        )}
      </div>

      {!isUser && onFeedback && message.content && (
        <div className="flex items-center gap-2 mt-2 ml-2">
          <button 
            onClick={() => onFeedback(message.id, 'up')}
            className="p-1 text-slate-400 hover:text-medical-600 hover:bg-medical-50 rounded transition-colors"
            title="Helpful"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
          </button>
          <button 
            onClick={() => onFeedback(message.id, 'down')}
            className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="Not helpful"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
