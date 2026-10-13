'use client';
import { useState } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus('Uploading and processing...');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/flask/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      if (res.ok) {
        setStatus(`Success: ${data.message}`);
        setFile(null);
      } else {
        setStatus(`Error: ${data.error || 'Upload failed'}`);
      }
    } catch (err) {
      setStatus('Error: Failed to communicate with server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto w-full mt-10 bg-white rounded-xl shadow-sm border border-slate-200">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Upload Medical Document</h1>
      <p className="text-slate-600 mb-8">
        Upload PDF documents (guidelines, medical textbooks, articles) to enrich MedLex's knowledge base.
      </p>
      
      <div className="border-2 border-dashed border-slate-300 rounded-lg p-10 text-center hover:bg-slate-50 transition-colors">
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileChange} 
          className="hidden" 
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
          <svg className="w-12 h-12 text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="text-medical-600 font-medium hover:underline">Click to select a PDF</span>
          <span className="text-slate-500 text-sm mt-1">or drag and drop</span>
        </label>
        
        {file && (
          <div className="mt-6 p-3 bg-medical-50 text-medical-800 rounded flex items-center justify-between">
            <span className="truncate max-w-[80%] font-medium">{file.name}</span>
            <span className="text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
          </div>
        )}
      </div>

      <div className="mt-8">
        <button 
          onClick={handleUpload} 
          disabled={!file || loading}
          className="w-full bg-medical-600 text-white rounded-lg py-3 font-semibold hover:bg-medical-700 disabled:opacity-50 transition-colors flex justify-center items-center"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : 'Upload Document'}
        </button>
      </div>
      
      {status && (
        <div className={`mt-6 p-4 rounded-md ${status.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {status}
        </div>
      )}
    </div>
  );
}
