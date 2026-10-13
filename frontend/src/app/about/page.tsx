export default function AboutPage() {
  return (
    <div className="p-8 max-w-3xl mx-auto w-full mt-8 bg-white rounded-xl shadow-sm border border-slate-200">
      <h1 className="text-3xl font-bold text-slate-800 mb-6">About MedLex</h1>
      
      <div className="prose prose-slate max-w-none">
        <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-4 border-b pb-2">Medical Disclaimer</h2>
        <p className="text-slate-700 mb-4 bg-red-50 p-4 rounded border-l-4 border-red-500">
          <strong>MedLex provides information for educational purposes only and should not be considered medical advice, diagnosis, or treatment.</strong> 
          Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. 
          Never disregard professional medical advice or delay in seeking it because of something you have read on this application.
        </p>

        <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-4 border-b pb-2">How it Works</h2>
        <p className="text-slate-700 mb-4">
          MedLex uses Retrieval-Augmented Generation (RAG) to provide grounded answers to medical questions. 
          When you ask a question, the system searches through an ingested database of medical literature and guidelines to find relevant excerpts. 
          It then uses a Large Language Model (LLM) to synthesize these excerpts into a coherent answer.
        </p>
        <p className="text-slate-700 mb-4">
          Every claim made by the assistant is backed by source citations, allowing you to trace information back to its origin.
        </p>

        <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-4 border-b pb-2">Limitations</h2>
        <ul className="list-disc pl-5 text-slate-700 space-y-2 mb-6">
          <li>The underlying AI model can hallucinate or misinterpret medical literature.</li>
          <li>The database may not contain the most up-to-date medical guidelines.</li>
          <li>The system cannot account for your personal medical history, allergies, or specific context.</li>
          <li>The system is not equipped to handle medical emergencies.</li>
        </ul>
      </div>
    </div>
  );
}
