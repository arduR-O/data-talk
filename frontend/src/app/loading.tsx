"use client";

import React from 'react';

export default function Loading() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Loading Spin animation */}
      <div className="relative z-10 flex flex-col items-center gap-4">
        <div className="relative w-16 h-16">
          {/* Inner circle */}
          <div className="absolute inset-0 border-4 border-white/5 rounded-full"></div>
          {/* Outer active circle */}
          <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="font-mono text-xs tracking-widest text-blue-400 font-bold uppercase">DataTalk</span>
          <span className="text-[10px] text-slate-500">Loading workspace components...</span>
        </div>
      </div>
    </div>
  );
}
