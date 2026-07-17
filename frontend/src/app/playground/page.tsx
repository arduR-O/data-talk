"use client"
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Inference from "../components/inference";
import UploadCard from "../components/Upload";
import { Sparkles, LogOut, User as UserIcon, ChevronDown } from "lucide-react";

interface User {
  firstName: string;
  lastName: string;
  email: string;
  user_id: string;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    setUser(null);
    setIsDropdownOpen(false);
    router.push('/');
  };

  return (
    <main className="bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/20 min-h-screen flex flex-col items-center relative overflow-hidden">
      
      {/* Top navigation bar */}
      <header className="w-full border-b border-white/5 bg-slate-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between relative z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-mono text-lg font-bold tracking-tight text-white">
            DataTalk Workspace
          </span>
        </div>
        
        {/* User Account Controls */}
        <div>
          {user ? (
            <div className="relative">
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 hover:bg-white/10 transition-all duration-300"
              >
                <div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-xs font-bold">
                  {user.firstName[0]}
                </div>
                <span className="text-white text-xs font-semibold hidden sm:block">
                  {user.firstName} {user.lastName}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {isDropdownOpen && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-slate-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                  <div className="p-3 border-b border-white/5">
                    <p className="text-white font-semibold text-xs">{user.firstName} {user.lastName}</p>
                    <p className="text-slate-400 text-[10px] truncate">{user.email}</p>
                  </div>
                  <div className="p-1">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-300 text-xs font-medium"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => router.push('/login')}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-xl transition-all text-xs font-semibold"
            >
              Sign In
            </button>
          )}
        </div>
      </header>

      {isDropdownOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsDropdownOpen(false)}
        />
      )}

      {/* Main Split Screen Area (NotebookLM Style) */}
      <div className="flex-1 w-full max-w-[1600px] flex flex-col md:flex-row gap-6 p-6 h-[calc(100vh-73px)] relative z-10 overflow-hidden">
        {/* Left Panel: Sources / Connections Panel */}
        <div className="w-full md:w-[380px] lg:w-[420px] flex-shrink-0 flex flex-col h-full overflow-y-auto animate-slide-in-left pr-1 md:pr-0">
          <UploadCard />
        </div>
        
        {/* Right Panel: Chat Assistant Panel */}
        <div className="flex-1 flex flex-col h-full animate-slide-in-right" style={{ animationDelay: '0.2s' }}>
          <Inference />
        </div>
      </div>

      {/* Background ambient lighting */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl"></div>
      </div>

      <style jsx global>{`
        @keyframes slide-in-left {
          from { transform: translateX(-30px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slide-in-right {
          from { transform: translateX(30px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        .animate-slide-in-left {
          animation: slide-in-left 0.5s ease-out forwards;
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.5s ease-out forwards;
        }
      `}</style>
    </main>
  );
}