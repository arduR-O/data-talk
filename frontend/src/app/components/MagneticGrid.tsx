"use client";
import { useEffect, useRef } from "react";

interface DotNode {
  x: number;
  y: number;
  homeX: number;
  homeY: number;
  vx: number;
  vy: number;
}

export default function MagneticGrid() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mousePos = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    let animFrameId: number;
    let dots: DotNode[] = [];
    
    // Magnetic Grid Physics constants
    const spacing = 32; 
    const baseMouseRadius = 420; 
    const repulsionStrength = 5.0; 
    const springStiffness = 0.08;
    const damping = 0.82;

    const resize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const dpr = window.devicePixelRatio || 1;
      
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      ctx.scale(dpr, dpr);
      
      dots = [];
      const cols = Math.ceil(width / spacing) + 1;
      const rows = Math.ceil(height / spacing) + 1;
      
      const offsetX = (width - (cols - 1) * spacing) / 2;
      const offsetY = (height - (rows - 1) * spacing) / 2;

      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          const homeX = offsetX + i * spacing;
          const homeY = offsetY + j * spacing;
          dots.push({ x: homeX, y: homeY, homeX, homeY, vx: 0, vy: 0 });
        }
      }
    };

    window.addEventListener("resize", resize);
    resize();

    const handleMouseMove = (e: MouseEvent) => {
      mousePos.current = { x: e.clientX, y: e.clientY };
    };
    const handleMouseLeave = () => {
      mousePos.current = { x: -1000, y: -1000 };
    };
    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);

    const draw = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      ctx.fillStyle = "#030712"; // matches bg-[#030712] background
      ctx.fillRect(0, 0, width, height);
      
      const mx = mousePos.current.x;
      const my = mousePos.current.y;
      const time = performance.now() / 1000;
      
      for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];
        
        const dx = dot.x - mx;
        const dy = dot.y - my;
        const distSq = dx * dx + dy * dy;
        const dist = Math.sqrt(distSq);
        const angle = Math.atan2(dy, dx);
        
        const blobDistortion = Math.sin(angle * 4 + time * 0.8) * 45 + Math.cos(angle * 7 - time * 0.5) * 30;
        const effectiveRadius = baseMouseRadius + blobDistortion;
        
        if (dist < effectiveRadius) {
          const force = (effectiveRadius - dist) / effectiveRadius;
          dot.vx += Math.cos(angle) * force * repulsionStrength;
          dot.vy += Math.sin(angle) * force * repulsionStrength;
        }
        
        dot.vx += (dot.homeX - dot.x) * springStiffness;
        dot.vy += (dot.homeY - dot.y) * springStiffness;
        
        dot.vx *= damping;
        dot.vy *= damping;
        
        dot.x += dot.vx;
        dot.y += dot.vy;
        
        const displacementX = dot.x - dot.homeX;
        const displacementY = dot.y - dot.homeY;
        const displacementSq = displacementX * displacementX + displacementY * displacementY;
        
        let radius = 0.3;
        let r = 255, g = 255, b = 255, a = 0.05; 
        
        if (dist < effectiveRadius) {
          const normDist = dist / effectiveRadius; 
          
          if (normDist < 0.08) {
            a = 0; 
          } else {
            const wave = Math.sin(normDist * Math.PI * 2 * 3 - time * 3); 
            let factor = (wave + 1) / 2; 
            
            const holeFade = Math.min((normDist - 0.08) * 6, 1);
            const edgeFade = Math.min((1 - normDist) * 3, 1);
            
            const displacement = Math.sqrt(displacementSq);
            const dispFactor = Math.min(displacement / 25, 1);
            
            factor = Math.max(factor * holeFade * edgeFade, dispFactor * edgeFade);
            
            radius = 0.3 + factor * 1.0; 
            r = Math.round(255 - (255 - 168) * factor); 
            g = Math.round(255 - (255 - 85) * factor); 
            b = Math.round(255 - (255 - 247) * factor);
            a = 0.05 + factor * 0.55; 
          }
        } else if (displacementSq > 0.1) {
          const displacement = Math.sqrt(displacementSq);
          const factor = Math.min(displacement / 25, 1);
          radius = 0.3 + factor * 1.0;
          r = Math.round(255 - (255 - 168) * factor);
          g = Math.round(255 - (255 - 85) * factor); 
          b = Math.round(255 - (255 - 247) * factor);
          a = 0.05 + factor * 0.55;
        }
        
        if (a > 0) {
          ctx.beginPath();
          ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`;
          ctx.fill();
        }
      }
      
      animFrameId = requestAnimationFrame(draw);
    };
    
    animFrameId = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 z-0" />;
}
