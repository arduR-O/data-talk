"use client"
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Inference from "./components/inference";
import UploadCard from "./components/Upload";

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
    // Check if user is logged in
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing user data:', error);
        // Clear invalid data
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
    router.push('/landing');
  };

  return (
    <main className="bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 min-h-screen flex flex-col items-center py-8 sm:py-12 px-4 sm:px-8 md:px-16 relative overflow-hidden">
      
      {/* User Dropdown Menu */}
      <div className="absolute top-6 right-6 z-50">
        {user ? (
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl px-4 py-2 hover:bg-white/15 transition-all duration-300"
            >
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <span className="text-white text-sm font-medium hidden sm:block">
                {user.firstName} {user.lastName}
              </span>
              <svg 
                className={`w-4 h-4 text-white transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {isDropdownOpen && (
              <div className="absolute top-full right-0 mt-2 w-48 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-2xl overflow-hidden">
                <div className="p-4 border-b border-white/10">
                  <p className="text-white font-medium text-sm">{user.firstName} {user.lastName}</p>
                  <p className="text-gray-300 text-xs truncate">{user.email}</p>
                </div>
                
                <div className="p-2">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-3 py-2 text-red-300 hover:bg-red-500/20 rounded-xl transition-all duration-300 text-sm font-medium"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/login')}
              className="bg-white/10 backdrop-blur-md border border-white/20 text-white px-4 py-2 rounded-2xl hover:bg-white/15 transition-all duration-300 text-sm font-medium"
            >
              Login
            </button>
            <button
              onClick={() => router.push('/signup')}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-2xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 text-sm font-medium"
            >
              Sign Up
            </button>
          </div>
        )}
      </div>

      {/* Close dropdown when clicking outside */}
      {isDropdownOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsDropdownOpen(false)}
        />
      )}

      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '4s'}}></div>
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-blue-400/20 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`
            }}
          />
        ))}
      </div>

      {/* Title with enhanced animation */}
      <div className="text-center mb-8 sm:mb-16 relative z-10 animate-fade-in">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 mb-6">
          <div className="relative animate-bounce-slow">
            <div className="w-24 h-24 sm:w-32 sm:h-32 md:w-40 md:h-40 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-2xl animate-glow">
              <svg className="w-12 h-12 sm:w-16 sm:h-16 md:w-20 md:h-20 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-400 rounded-full border-4 border-slate-900 shadow-lg animate-ping-slow"></div>
          </div>
          
          <h1 className="font-mono text-white text-4xl sm:text-5xl md:text-6xl font-bold animate-typewriter">
            DataTalk
          </h1>
        </div>
        
        <p className="text-gray-400 text-lg sm:text-xl md:text-2xl max-w-2xl mx-auto px-4 animate-slide-up" style={{animationDelay: '0.5s'}}>
          Your AI Data Scientist - Upload documents, connect data sources, and have intelligent conversations
        </p>
        
        {/* Decorative line */}
        <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mx-auto mt-6 shadow-lg animate-expand" style={{animationDelay: '1s'}}></div>
      </div>
      
      {/* Cards container */}
      <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 w-full max-w-7xl justify-center items-stretch relative z-10">
        {/* Upload Card */}
        <div className="w-full lg:w-auto flex justify-center animate-slide-in-left">
          <UploadCard />
        </div>
        
        {/* Inference Card */}
        <div className="w-full lg:w-auto flex justify-center animate-slide-in-right" style={{animationDelay: '0.3s'}}>
          <Inference />
        </div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-10px) rotate(5deg); }
        }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
          50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.8), 0 0 60px rgba(147, 51, 234, 0.6); }
        }
        @keyframes ping-slow {
          0% { transform: scale(1); opacity: 1; }
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        @keyframes typewriter {
          from { width: 0; }
          to { width: 100%; }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slide-up {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes slide-in-left {
          from { transform: translateX(-50px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slide-in-right {
          from { transform: translateX(50px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes expand {
          from { width: 0; opacity: 0; }
          to { width: 96px; opacity: 1; }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        .animate-bounce-slow {
          animation: bounce-slow 3s ease-in-out infinite;
        }
        .animate-glow {
          animation: glow 2s ease-in-out infinite;
        }
        .animate-ping-slow {
          animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        .animate-typewriter {
          overflow: hidden;
          border-right: 2px solid;
          white-space: nowrap;
          animation: typewriter 2s steps(8, end), blink-caret 0.75s step-end infinite;
        }
        .animate-fade-in {
          animation: fade-in 1s ease-out;
        }
        .animate-slide-up {
          animation: slide-up 0.8s ease-out;
        }
        .animate-slide-in-left {
          animation: slide-in-left 0.8s ease-out;
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.8s ease-out;
        }
        .animate-expand {
          animation: expand 1s ease-out;
        }
        @keyframes blink-caret {
          from, to { border-color: transparent; }
          50% { border-color: white; }
        }
      `}</style>
    </main>
  )
}