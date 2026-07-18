"use client";

import React from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white relative overflow-hidden p-6">
      {/* Background radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-500/5 rounded-full blur-3xl pointer-events-none"></div>
      
      <div className="relative z-10 flex flex-col items-center gap-6 max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center shadow-lg shadow-red-500/5">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-bold tracking-tight text-white font-mono">Application Error</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            {error.message || "An unexpected error occurred while rendering the workspace."}
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => reset()}
            className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/10 transition-all duration-300"
          >
            Retry Loading
          </button>
          <button
            onClick={() => window.location.href = '/playground'}
            className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-5 py-2 rounded-xl text-xs font-semibold transition-all duration-300"
          >
            Go to Playground
          </button>
        </div>
      </div>
    </div>
  );
}
