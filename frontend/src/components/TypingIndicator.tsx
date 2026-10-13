export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm p-2">
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
      </div>
      <span>MedLex is thinking...</span>
    </div>
  );
}
