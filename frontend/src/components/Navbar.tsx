import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-slate-200 py-3 px-6 flex items-center justify-between shadow-sm sticky top-0 z-50">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-medical-600 flex items-center justify-center text-white font-bold text-lg">
          M
        </div>
        <span className="font-bold text-xl text-slate-800 tracking-tight">MedLex</span>
      </Link>
      <div className="flex items-center gap-6 text-sm font-medium text-slate-600">
        <Link href="/" className="hover:text-medical-600 transition-colors">Chat</Link>
        <Link href="/upload" className="hover:text-medical-600 transition-colors">Upload PDF</Link>
        <Link href="/history" className="hover:text-medical-600 transition-colors">History</Link>
        <Link href="/about" className="hover:text-medical-600 transition-colors">About</Link>
      </div>
    </nav>
  );
}
