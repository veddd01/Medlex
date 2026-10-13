import { useState } from 'react';
import { Source } from '../types/api';

export default function SourceCitation({ source }: { source: Source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-hidden text-sm my-2 shadow-sm">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-3 py-2 bg-slate-50 hover:bg-slate-100 flex items-center justify-between transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="bg-medical-100 text-medical-800 text-xs font-semibold px-2 py-0.5 rounded-full">
            Page {source.page}
          </span>
          <span className="text-slate-600 truncate max-w-[200px]" title={source.source}>
            {source.source.split(/[\\/\\\\]/).pop()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden" title={`Relevance: ${Math.round(source.score * 100)}%`}>
            <div 
              className="h-full bg-medical-500" 
              style={{ width: `${Math.max(0, Math.min(100, source.score * 100))}%` }}
            />
          </div>
          <svg className={`w-4 h-4 text-slate-400 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      
      {expanded && (
        <div className="p-3 bg-white border-t border-slate-100 text-slate-700 italic">
          "{source.excerpt}"
        </div>
      )}
    </div>
  );
}
