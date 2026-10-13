export default function EmergencyBanner() {
  return (
    <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded shadow-sm flex items-start gap-3">
      <svg className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h3 className="text-red-800 font-bold">Medical Emergency Alert</h3>
        <p className="text-red-700 mt-1 text-sm">
          Your message indicates a potential medical emergency. MedLex cannot provide emergency assistance.
        </p>
        <p className="text-red-700 mt-2 text-sm font-semibold">
          Please immediately call 911 (US) or your local emergency number, or go to the nearest emergency room.
        </p>
      </div>
    </div>
  );
}
