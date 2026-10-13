export default function SuggestionChips({ onSelect }: { onSelect: (q: string) => void }) {
  const suggestions = [
    "What are the symptoms of type 2 diabetes?",
    "How is hypertension usually treated?",
    "Explain the side effects of ibuprofen",
    "What are early signs of a heart attack?"
  ];

  return (
    <div className="flex flex-wrap gap-2 justify-center mt-8">
      {suggestions.map((q, i) => (
        <button
          key={i}
          onClick={() => onSelect(q)}
          className="bg-white border border-medical-200 text-medical-700 px-4 py-2 rounded-full text-sm hover:bg-medical-50 hover:border-medical-300 transition-all shadow-sm"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
