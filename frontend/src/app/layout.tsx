import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "MedLex - Medical AI Chatbot",
  description: "Your trusted medical AI assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-medical-50 text-slate-800 antialiased min-h-screen flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
        <footer className="bg-white border-t border-slate-200 py-4 text-center px-4">
          <p className="text-xs text-slate-500 max-w-3xl mx-auto">
            <strong>Disclaimer:</strong> MedLex provides information for educational purposes only and should not be considered medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. If you think you may have a medical emergency, call your doctor, go to the emergency department, or call 911 immediately.
          </p>
        </footer>
      </body>
    </html>
  );
}
