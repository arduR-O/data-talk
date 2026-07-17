"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { Database, FileText, Bot, ArrowRight, Shield, Zap, Sparkles } from "lucide-react";

interface DotNode {
  x: number;
  y: number;
  homeX: number;
  homeY: number;
  vx: number;
  vy: number;
}

export default function LandingPage() {
  const [isMounted, setIsMounted] = useState(false);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mousePos = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;

    const handleMouseMove = (e: MouseEvent) => {
      mousePos.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      mousePos.current = { x: -1000, y: -1000 };
    };

    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [isMounted]);

  useEffect(() => {
    if (!isMounted) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const dotSpacing = 16; // Increased density spacing
    const repulsionRadius = 80; // Tighter deflection radius
    const repulsionStrength = 6.0; // Responsive push force
    const springStiffness = 0.08; // Snappier elastic recall
    const damping = 0.78; // Increased friction to eliminate wobble
    
    let dots: DotNode[] = [];

    const initGrid = () => {
      dots = [];
      const cols = Math.ceil(width / dotSpacing);
      const rows = Math.ceil(height / dotSpacing);

      for (let c = 0; c < cols; c++) {
        for (let r = 0; r < rows; r++) {
          const x = c * dotSpacing;
          const y = r * dotSpacing;
          dots.push({
            x,
            y,
            homeX: x,
            homeY: y,
            vx: 0,
            vy: 0
          });
        }
      }
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initGrid();
    };

    window.addEventListener("resize", handleResize);
    initGrid();

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      const radSq = repulsionRadius * repulsionRadius;

      for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];
        
        // Physics update: calculate squared distance first to optimize performance
        const dx = dot.x - mousePos.current.x;
        const dy = dot.y - mousePos.current.y;
        const distSq = dx * dx + dy * dy;

        let radius = 0.8;
        let color = "rgba(156, 163, 175, 0.07)"; // Default dim gray dot

        if (distSq < radSq) {
          const dist = Math.sqrt(distSq);
          const force = (repulsionRadius - dist) / repulsionRadius;
          const angle = Math.atan2(dy, dx);
          const push = force * repulsionStrength;
          
          dot.vx += Math.cos(angle) * push;
          dot.vy += Math.sin(angle) * push;

          // Proximity visual feedback
          const factor = 1 - dist / repulsionRadius;
          radius = 0.8 + factor * 2.2; // Smoothly scale up dot size
          
          const rVal = Math.round(99 + factor * 130);
          const gVal = Math.round(102 + factor * 50);
          const bVal = Math.round(241 + factor * 14);
          const opacity = 0.07 + factor * 0.75;
          color = `rgba(${rVal}, ${gVal}, ${bVal}, ${opacity})`;
        }

        // Apply spring-back force to home coordinates
        const springX = (dot.homeX - dot.x) * springStiffness;
        const springY = (dot.homeY - dot.y) * springStiffness;

        dot.vx += springX;
        dot.vy += springY;

        // Apply damping
        dot.vx *= damping;
        dot.vy *= damping;

        // Apply positions
        dot.x += dot.vx;
        dot.y += dot.vy;

        ctx.beginPath();
        ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isMounted]);

  // SSR Skeleton Layout
  if (!isMounted) {
    return (
      <main className="min-h-screen bg-[#030712] text-white flex flex-col justify-between items-center py-24">
        <div className="flex-1 flex flex-col justify-center items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse flex items-center justify-center">
            <span className="font-mono text-xl font-bold">DT</span>
          </div>
          <h1 className="text-2xl font-bold font-mono tracking-wider bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
            DATATALK
          </h1>
        </div>
      </main>
    );
  }

  const cardGlows = [
    "from-blue-500/30 to-cyan-500/30 shadow-blue-500/20",
    "from-purple-500/30 to-pink-500/30 shadow-purple-500/20",
    "from-cyan-500/30 to-indigo-500/30 shadow-cyan-500/20"
  ];

  return (
    <main className="min-h-screen flex flex-col justify-between bg-[#030712] text-white px-4 overflow-hidden relative">
      
      {/* Elastic interactive grid canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none z-0"
      />

      {/* Ambient color gradient blur meshes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[10%] left-[20%] w-[500px] h-[500px] bg-gradient-to-r from-blue-600/10 to-indigo-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
        <div className="absolute bottom-[20%] right-[10%] w-[600px] h-[600px] bg-gradient-to-r from-purple-600/10 to-pink-500/10 rounded-full blur-[140px] animate-pulse-slow" style={{ animationDelay: "3s" }}></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[300px] bg-cyan-500/5 rounded-full blur-[160px] rotate-12"></div>
      </div>

      {/* Header bar */}
      <header className="w-full max-w-7xl mx-auto flex items-center justify-between py-6 relative z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="font-mono text-xl font-bold tracking-tight bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent">
            DataTalk
          </span>
        </div>
        <div className="flex gap-4">
          <Link
            href="/login"
            className="px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 transition-all duration-300 text-sm font-semibold backdrop-blur-md"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Main hero section */}
      <div className="flex-1 flex flex-col justify-center items-center text-center relative z-10 max-w-5xl mx-auto py-12 md:py-20">
        
        {/* Sparkle badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold mb-8 backdrop-blur-md shadow-inner"
        >
          <Zap className="w-3.5 h-3.5" />
          Next-Gen AI Data Assistant
        </motion.div>

        {/* Hero Title */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl md:text-7xl font-bold tracking-tight mb-8"
        >
          Your Data has a Voice. <br />
          <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-glow">
            Let&apos;s Talk to It.
          </span>
        </motion.h1>

        {/* Hero Description */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base md:text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          Connect relational databases, drop in document folders, or upload spreadsheets. Ask questions in plain English and observe live agent reasoning.
        </motion.p>

        {/* Primary Call to Action Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mb-20"
        >
          <Link
            href="/login"
            className="group relative inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-2xl font-bold shadow-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-blue-500/35 text-center cursor-pointer"
          >
            <span>Get Started Free</span>
            <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-md -z-10"></div>
          </Link>
        </motion.div>

        {/* Interactive Feature Cards */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left"
        >
          {[
            {
              icon: <Database className="w-6 h-6 text-blue-400" />,
              title: "Structured SQL Agents",
              desc: "Ask queries and commands. The agent writes SQL, executes it, self-corrects on errors, and returns insights."
            },
            {
              icon: <FileText className="w-6 h-6 text-purple-400" />,
              title: "Smart Multi-Format RAG",
              desc: "Upload PDFs, Markdown files, or text sheets. Vector search answers context queries with source citations."
            },
            {
              icon: <Bot className="w-6 h-6 text-pink-400" />,
              title: "Interactive Log Trace",
              desc: "Watch the agentic ReAct loop. View reasoning steps, tool parameters, and SQL blocks compiled in real-time."
            }
          ].map((feature, idx) => (
            <div
              key={idx}
              onMouseEnter={() => setHoveredCard(idx)}
              onMouseLeave={() => setHoveredCard(null)}
              className="relative rounded-3xl p-8 bg-white/[0.02] border border-white/5 overflow-hidden transition-all duration-300 cursor-default"
            >
              {/* Inner ambient light glow */}
              <div
                className={`absolute inset-0 bg-gradient-to-br transition-opacity duration-500 blur-2xl -z-10 opacity-0 ${
                  hoveredCard === idx ? "opacity-100" : ""
                } ${cardGlows[idx]}`}
              ></div>
              
              {/* Card border glow helper */}
              <div
                className={`absolute inset-0 border border-transparent rounded-3xl transition-colors duration-500 -z-10 ${
                  hoveredCard === idx ? "border-white/10" : ""
                }`}
              ></div>

              <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mb-6 border border-white/10">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-3 text-white">{feature.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="w-full max-w-7xl mx-auto py-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 relative z-20 mt-12">
        <p>© 2026 DataTalk Inc. All rights reserved.</p>
        <div className="flex gap-6 mt-4 sm:mt-0 font-medium">
          <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> Secure SQLite fallbacks</span>
          <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> Fast LangGraph orchestration</span>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes pulse-slow {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.1); opacity: 1; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 8s ease-in-out infinite;
        }
      `}</style>
    </main>
  );
}