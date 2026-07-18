"use client"
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Inference from "../components/inference";
import UploadCard from "../components/Upload";
import { Sparkles, LogOut, User as UserIcon, ChevronDown } from "lucide-react";
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';

interface User {
  firstName: string;
  lastName: string;
  email: string;
  user_id: string;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const userData = localStorage.getItem('user') || sessionStorage.getItem('user');
    
    if (!token || !userData) {
      router.push('/login');
      return;
    }
    
    try {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
    } catch (error) {
      console.error('Error parsing user data:', error);
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      sessionStorage.removeItem('user');
      sessionStorage.removeItem('token');
      router.push('/login');
    } finally {
      setLoading(false);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    setUser(null);
    setIsDropdownOpen(false);
    router.push('/');
  };

  if (loading) {
    return (
      <main className="bg-slate-950 min-h-screen flex flex-col items-center justify-center text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-mono">Verifying authentication...</span>
        </div>
      </main>
    );
  }

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
                  {user && user.firstName ? user.firstName[0].toUpperCase() : 'U'}
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

      {/* Main Split Screen Area with resizable panels */}
      <div className="flex-1 w-full max-w-[1600px] p-6 h-[calc(100vh-73px)] relative z-10 overflow-hidden">
        <PanelGroup direction="horizontal" orientation="horizontal" id="playground-group" className="h-full">
          <Panel id="workspace-panel" defaultSize="35%" minSize="20%" maxSize="60%">
            <div className="h-full overflow-y-auto scrollbar-hide pr-1">
              <UploadCard />
            </div>
          </Panel>
          <PanelResizeHandle id="resize-handle" className="w-2 flex items-center justify-center group hover:bg-white/5 rounded-lg transition-colors cursor-col-resize z-20">
            <div className="w-0.5 h-8 bg-white/20 rounded-full group-hover:bg-blue-400 group-active:bg-blue-500 transition-colors" />
          </PanelResizeHandle>
          <Panel id="chat-panel" defaultSize="65%" minSize="30%">
            <div className="h-full overflow-hidden">
              <Inference />
            </div>
          </Panel>
        </PanelGroup>
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