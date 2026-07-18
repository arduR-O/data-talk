"use client";

import React, { useEffect, useState, useRef } from 'react';
import axios from "axios";
import { Sparkles, Trash2, Send, Brain, Terminal, ChevronDown, Bot, X, Plus } from "lucide-react";
import { API_BASE } from '../lib/api';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const TableRenderer = ({ tableLines }: { tableLines: string[] }) => {
  const parsedRows = tableLines.map(line => 
    line.split('|')
      .map(cell => cell.trim())
      .filter((_, i, arr) => i > 0 && i < arr.length - 1)
  );

  const rows = parsedRows.filter(row => !row.every(cell => cell.startsWith('-') || cell.startsWith(':')));

  if (rows.length === 0) return null;
  const headers = rows[0];
  const bodyRows = rows.slice(1);

  const exportTableToCSV = () => {
    const csvRows = rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(","));
    const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(csvRows.join("\n"));
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", "table_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="my-4 p-4 bg-slate-950/40 border border-white/5 rounded-2xl overflow-hidden backdrop-blur-sm">
      <div className="flex justify-between items-center mb-3">
        <span className="text-[10px] font-mono text-slate-400 font-semibold uppercase tracking-wider">Query Results</span>
        <button
          onClick={exportTableToCSV}
          className="px-2.5 py-1 text-[10px] bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 font-semibold rounded-lg flex items-center gap-1 transition-colors border border-white/5"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] text-slate-300 text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.02]">
              {headers.map((header, i) => (
                <th key={i} className="px-3 py-2 font-semibold text-white">{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bodyRows.map((row, rIdx) => (
              <tr key={rIdx} className="border-b border-white/5 hover:bg-white/[0.01] transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3 py-2 text-slate-300 font-mono">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ChartRenderer = ({ jsonStr }: { jsonStr: string }) => {
  try {
    const chartConfig = JSON.parse(jsonStr);
    const { type, title, data } = chartConfig;

    if (!data || !Array.isArray(data)) return null;

    const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444'];

    const exportToCSV = () => {
      const csvRows = [
        "Name,Value",
        ...data.map(e => `"${String(e.name).replace(/"/g, '""')}",${e.value}`)
      ];
      const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(csvRows.join("\n"));
      const link = document.createElement("a");
      link.setAttribute("href", csvContent);
      link.setAttribute("download", `${title || "chart_data"}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const renderChart = () => {
      switch (type) {
        case 'line':
          return (
            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
              <Tooltip 
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                labelStyle={{ color: '#fff', fontSize: '10px' }}
                itemStyle={{ color: '#60a5fa', fontSize: '10px' }}
              />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
            </LineChart>
          );
        case 'pie':
          return (
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={4}
                dataKey="value"
              >
                {data.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                itemStyle={{ color: '#fff', fontSize: '10px' }}
              />
            </PieChart>
          );
        case 'bar':
        default:
          return (
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
              <Tooltip 
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                labelStyle={{ color: '#fff', fontSize: '10px' }}
                itemStyle={{ color: '#60a5fa', fontSize: '10px' }}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                {data.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          );
      }
    };

    return (
      <div className="my-4 p-4 bg-slate-950/40 border border-white/5 rounded-2xl backdrop-blur-sm max-w-full">
        <div className="flex justify-between items-center mb-3">
          {title && <h4 className="text-xs font-semibold text-slate-200 tracking-wide">{title}</h4>}
          <button
            onClick={exportToCSV}
            className="px-2.5 py-1 text-[10px] bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 font-semibold rounded-lg flex items-center gap-1 transition-colors border border-white/5"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
        </div>
        <div className="w-full h-48">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </div>
    );
  } catch (e) {
    console.error('Failed to render chart:', e);
    return (
      <pre className="my-3 p-3 bg-red-950/20 border border-red-500/10 rounded-xl font-mono text-[10px] text-red-400 overflow-x-auto">
        Failed to render chart data: {jsonStr}
      </pre>
    );
  }
};

const MarkdownText = ({ content }: { content: string }) => {
  if (!content) return null;
  const lines = content.split('\n');
  const renderedElements: React.ReactNode[] = [];
  
  let currentList: React.ReactNode[] = [];
  let inList = false;

  const parseInline = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-[11px] font-mono border border-white/5 text-cyan-400">{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];
    
    // Markdown table block detection
    if (line.trim().startsWith('|')) {
      const tableLines: string[] = [];
      let tableIdx = idx;
      while (tableIdx < lines.length && lines[tableIdx].trim().startsWith('|')) {
        tableLines.push(lines[tableIdx]);
        tableIdx++;
      }
      idx = tableIdx - 1;
      renderedElements.push(<TableRenderer key={`table-${idx}`} tableLines={tableLines} />);
      continue;
    }

    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      inList = true;
      currentList.push(<li key={`li-${idx}`} className="list-disc ml-5 mb-1 text-slate-300">{parseInline(line.replace(/^[\s\-\*]+/, ''))}</li>);
      continue;
    }
    
    if (inList && !line.trim().startsWith('- ') && !line.trim().startsWith('* ')) {
      renderedElements.push(<ul key={`ul-${idx}`} className="my-2">{currentList}</ul>);
      currentList = [];
      inList = false;
    }

    if (line.startsWith('### ')) {
      renderedElements.push(<h3 key={idx} className="text-sm font-bold text-white mt-4 mb-2">{parseInline(line.slice(4))}</h3>);
      continue;
    }
    if (line.startsWith('## ')) {
      renderedElements.push(<h2 key={idx} className="text-base font-bold text-white mt-5 mb-2">{parseInline(line.slice(3))}</h2>);
      continue;
    }
    if (line.startsWith('# ')) {
      renderedElements.push(<h1 key={idx} className="text-lg font-bold text-white mt-6 mb-3">{parseInline(line.slice(2))}</h1>);
      continue;
    }

    if (line.startsWith('```chart')) {
      const chartJsonLines: string[] = [];
      let chartIdx = idx + 1;
      while (chartIdx < lines.length && !lines[chartIdx].startsWith('```')) {
        chartJsonLines.push(lines[chartIdx]);
        chartIdx++;
      }
      idx = chartIdx;
      renderedElements.push(<ChartRenderer key={`chart-${idx}`} jsonStr={chartJsonLines.join('\n')} />);
      continue;
    }

    if (line.startsWith('```')) {
      const codeLines: string[] = [];
      let codeIdx = idx + 1;
      while (codeIdx < lines.length && !lines[codeIdx].startsWith('```')) {
        codeLines.push(lines[codeIdx]);
        codeIdx++;
      }
      idx = codeIdx;
      renderedElements.push(
        <pre key={idx} className="my-3 p-3 bg-slate-950 border border-white/5 rounded-xl font-mono text-[11px] text-blue-200 overflow-x-auto">
          {codeLines.join('\n')}
        </pre>
      );
      continue;
    }

    if (line.trim() !== '') {
      renderedElements.push(<p key={idx} className="mb-2 text-slate-300 leading-relaxed text-xs">{parseInline(line)}</p>);
    }
  }

  if (inList && currentList.length > 0) {
    renderedElements.push(<ul key="ul-final" className="my-2">{currentList}</ul>);
  }

  return <div>{renderedElements}</div>;
};

interface Message {
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  routing?: string;
  debug_logs?: Array<{
    timestamp: string;
    level: string;
    message: string;
    data?: Record<string, any>;
  }>;
}

export default function Inference() {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState<Message[]>([
    {
      type: 'system',
      content: "Welcome to DataTalk workspace. I am your agentic assistant, ready to write SQL queries against your databases and retrieve insights from your text/PDF documents.",
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [isClient, setIsClient] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isClearing, setIsClearing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Session management states
  const [sessions, setSessions] = useState<Array<{ session_id: string, title: string, timestamp: string }>>([
    { session_id: 'default', title: 'Default Thread', timestamp: new Date().toISOString() }
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string>('default');

  const getAuthToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString();
      }
    } catch (e) {}
    return timestamp;
  };

  useEffect(() => {
    setIsClient(true);
    loadSessions();
    loadChatHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload history when active session changes
  useEffect(() => {
    if (isClient) {
      loadChatHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSessionId]);

  const loadSessions = async () => {
    const token = getAuthToken();
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/chat/sessions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.sessions && data.sessions.length > 0) {
          setSessions(data.sessions);
        } else {
          setSessions([{ session_id: 'default', title: 'Default Thread', timestamp: new Date().toISOString() }]);
        }
      }
    } catch (e) {
      console.error('Failed to load chat sessions:', e);
    }
  };

  const loadChatHistory = async () => {
    const token = getAuthToken();
    if (!token) {
      setIsLoadingHistory(false);
      return;
    }

    setIsLoadingHistory(true);
    try {
      const response = await axios.get(`${API_BASE}/api/chat/history?session_id=${activeSessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.messages && response.data.messages.length > 0) {
        const formattedMessages: Message[] = response.data.messages.map((msg: any) => ({
          type: msg.type as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: formatTimestamp(msg.timestamp)
        }));

        setResponses(formattedMessages);
      } else {
        setResponses([
          {
            type: 'system',
            content: "Welcome to DataTalk workspace. I am your agentic assistant, ready to write SQL queries against your databases and retrieve insights from your text/PDF documents.",
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (error: any) {
      console.error('Failed to load chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const confirmClearHistory = async () => {
    setShowClearConfirm(false);
    const token = getAuthToken();
    if (!token) {
      setError('Please log in to clear chat history');
      return;
    }

    setIsClearing(true);
    try {
      await axios.delete(`${API_BASE}/api/chat/history?session_id=${activeSessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setResponses([
        {
          type: 'system',
          content: "Welcome to DataTalk workspace. I am your agentic assistant, ready to write SQL queries against your databases and retrieve insights from your text/PDF documents.",
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      loadSessions();
    } catch (error: any) {
      console.error('Failed to clear chat history:', error);
      setError('Failed to clear chat history. Please try again.');
    } finally {
      setIsClearing(false);
    }
  };

  const startNewSession = () => {
    const newSessionId = `session-${Math.random().toString(36).substring(2, 15)}`;
    setActiveSessionId(newSessionId);
    setResponses([
      {
        type: 'system',
        content: "Welcome to DataTalk workspace. I am your agentic assistant, ready to write SQL queries against your databases and retrieve insights from your text/PDF documents.",
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  };

  const switchSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
  };

  const deleteSession = async (sessionId: string) => {
    const token = getAuthToken();
    if (!token) return;

    try {
      await axios.delete(`${API_BASE}/api/chat/history?session_id=${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (activeSessionId === sessionId) {
        setActiveSessionId('default');
      }
      loadSessions();
    } catch (e) {
      console.error('Failed to delete session:', e);
    }
  };

  const handleSendQuery = async () => {
    if (!query.trim() || isLoading) return;
    
    const token = getAuthToken();
    if (!token) {
      setError('Please log in to send messages');
      return;
    }

    const userMessage: Message = {
      type: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setResponses(prev => [...prev, userMessage]);
    const currentQuery = query;
    setQuery('');
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          question: currentQuery,
          session_id: activeSessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Chat failed with status ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body returned from server');
      }

      // Add a placeholder message for the assistant response
      const assistantPlaceholder: Message = {
        type: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString(),
        routing: 'general',
        debug_logs: []
      };

      setResponses(prev => [...prev, assistantPlaceholder]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || "";

        for (const line of lines) {
          const cleanedLine = line.trim();
          if (!cleanedLine.startsWith('data: ')) continue;

          try {
            const dataStr = cleanedLine.slice(6);
            const parsedData = JSON.parse(dataStr);

            if (parsedData.error) {
              setError(parsedData.error);
              continue;
            }

            if (parsedData.done) {
              setResponses(prev => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].type === 'assistant') {
                  updated[lastIdx].routing = parsedData.routing || updated[lastIdx].routing;
                  updated[lastIdx].debug_logs = parsedData.debug_logs || updated[lastIdx].debug_logs;
                }
                return updated;
              });
              loadSessions();
              break;
            }

            if (parsedData.token) {
              setResponses(prev => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].type === 'assistant') {
                  updated[lastIdx].content += parsedData.token;
                }
                return updated;
              });
            }
          } catch (jsonErr) {
            console.error('Error parsing SSE chunk:', jsonErr);
          }
        }
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMessage: Message = {
        type: 'assistant',
        content: err.message || 'There was an error processing your request. Please try again.',
        timestamp: new Date().toLocaleTimeString()
      };
      setResponses(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/40 border border-white/5 rounded-2xl shadow-2xl flex h-full w-full backdrop-blur-md overflow-hidden relative">
      
      {/* Sidebar for chat sessions */}
      <div className="w-48 bg-slate-950/40 border-r border-white/5 flex flex-col h-full flex-shrink-0">
        <div className="p-3 border-b border-white/5">
          <button
            onClick={startNewSession}
            className="w-full py-2 px-3 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(s => (
            <div
              key={s.session_id}
              className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-all text-[11px] ${
                activeSessionId === s.session_id
                  ? 'bg-blue-600/10 text-white font-medium border border-blue-500/10'
                  : 'text-slate-400 hover:bg-white/[0.02] hover:text-slate-200'
              }`}
              onClick={() => switchSession(s.session_id)}
            >
              <span className="truncate pr-2">{s.title || 'New Chat'}</span>
              {s.session_id !== 'default' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(s.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 hover:text-red-400 transition-opacity p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main chat window */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="border-b border-white/5 px-6 py-4 bg-slate-950/20 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-white flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-400" />
              AI Workspace Agent
            </h2>
            <p className="text-[10px] text-slate-400 mt-0.5">Observe reasoning steps & dynamic table querying</p>
          </div>
          
          {showClearConfirm ? (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-red-400 font-semibold">Clear history?</span>
              <button
                onClick={confirmClearHistory}
                className="px-2 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-[10px] font-bold transition-colors"
              >
                Yes
              </button>
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold transition-colors"
              >
                No
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowClearConfirm(true)}
              disabled={isClearing || isLoadingHistory || responses.length <= 1}
              className="p-1.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              title="Clear chat history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Messages Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-950/10">
          {isLoadingHistory ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex items-center gap-2.5 text-slate-400 text-xs">
                <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                <span>Loading workspace conversation...</span>
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-5xl mx-auto">
              {responses.map((message, index) => (
                <div key={message.timestamp + '-' + index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    
                    {/* Icon */}
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-lg ${
                      message.type === 'user' 
                        ? 'bg-blue-600' 
                        : message.type === 'system'
                        ? 'bg-amber-600/20 border border-amber-500/30'
                        : 'bg-slate-800 border border-white/5'
                    }`}>
                      {message.type === 'user' ? (
                        <div className="text-white text-xs font-bold">U</div>
                      ) : message.type === 'system' ? (
                        <Terminal className="w-3.5 h-3.5 text-amber-400" />
                      ) : (
                        <Bot className="w-4 h-4 text-blue-400" />
                      )}
                    </div>
                    
                    {/* Bubble */}
                    <div className={`rounded-2xl px-4 py-3 shadow-md ${
                      message.type === 'user' 
                        ? 'bg-blue-600/90 text-white font-medium' 
                        : message.type === 'system'
                        ? 'bg-amber-950/10 border border-amber-500/20 text-amber-300/90'
                        : 'bg-white/[0.03] border border-white/5 text-slate-200'
                    }`}>
                      {(() => {
                        const extractThink = (text: string) => {
                          if (!text) return { visible: '', think: '' };
                          const regex = /<think>([\s\S]*?)<\/think>/g;
                          const matches = Array.from(text.matchAll(regex));
                          const thinkText = matches
                            .map(match => match[1]?.trim())
                            .filter(Boolean)
                            .join('\n\n');
                          const visible = text.replace(regex, '').trim();
                          return { visible, think: thinkText };
                        };
                        const parsed = message.type === 'assistant' ? extractThink(message.content) : { visible: message.content, think: '' };
                        return (
                          <>
                            {message.type === 'assistant' ? (
                              <div className="text-xs leading-relaxed whitespace-pre-wrap space-y-2">
                                <MarkdownText content={parsed.visible} />
                              </div>
                            ) : (
                              <p className="text-xs leading-relaxed whitespace-pre-wrap">{parsed.visible}</p>
                            )}
                            {parsed.think && message.type === 'assistant' && (
                              <details className="mt-2.5 group">
                                <summary className="text-[10px] cursor-pointer select-none text-slate-400 hover:text-slate-200 transition-colors font-semibold flex items-center gap-1">
                                  <Brain className="w-3 h-3 text-purple-400" /> View Agent Thoughts
                                </summary>
                                <div className="mt-1.5 text-[10px] text-purple-300 bg-purple-950/10 border border-purple-500/10 rounded-xl p-2.5 whitespace-pre-wrap font-mono leading-relaxed">
                                  {parsed.think}
                                </div>
                              </details>
                            )}
                          </>
                        );
                      })()}
                      
                      {/* Execution Logs Drawer inside assistant bubbles */}
                      {message.type === 'assistant' && message.debug_logs && message.debug_logs.length > 0 && (
                        <details className="mt-3 group border border-white/5 rounded-xl bg-slate-950/20 overflow-hidden">
                          <summary className="text-[10px] cursor-pointer select-none text-slate-400 hover:text-slate-200 transition-colors font-semibold px-3 py-2 flex items-center justify-between">
                            <span className="flex items-center gap-1.5"><Terminal className="w-3 h-3 text-cyan-400" /> View Execution Logs ({message.routing || 'agent'})</span>
                            <ChevronDown className="w-3 h-3 transform group-open:rotate-180 transition-transform duration-200 text-slate-500" />
                          </summary>
                          <div className="border-t border-white/5 p-3 space-y-2 font-mono text-[9px] leading-relaxed max-h-52 overflow-y-auto text-slate-300">
                            {message.debug_logs.map((log, lIdx) => (
                              <div key={lIdx} className="border-b border-white/5 last:border-0 pb-1.5 mb-1.5 last:pb-0 last:mb-0">
                                <div className="flex items-center gap-1.5 flex-wrap mb-1">
                                  <span className="text-slate-500">[{log.timestamp}]</span>
                                  <span className={`px-1 py-0.5 rounded font-bold uppercase text-[8px] ${
                                    log.level === 'TOOL' ? 'bg-purple-900/30 text-purple-300 border border-purple-800/30' :
                                    log.level === 'SQL' ? 'bg-cyan-900/30 text-cyan-300 border border-cyan-800/30' :
                                    log.level === 'RESULT' ? 'bg-emerald-900/30 text-emerald-300 border border-emerald-800/30' :
                                    log.level === 'ERROR' ? 'bg-red-900/30 text-red-300 border border-red-800/30' :
                                    'bg-slate-800 text-slate-300 border border-white/5'
                                  }`}>
                                    {log.level}
                                  </span>
                                  <span className="font-semibold text-slate-100">{log.message}</span>
                                </div>
                                {log.data && (
                                  <pre className="bg-slate-950 text-slate-400 rounded-lg p-2 mt-1 overflow-x-auto text-[8px] max-w-full whitespace-pre-wrap break-all border border-white/5">
                                    {JSON.stringify(log.data, null, 2)}
                                  </pre>
                                )}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      
                      {isClient && <p className={`text-[9px] mt-2 font-medium ${
                        message.type === 'user' ? 'text-blue-200/70' : 'text-slate-500'
                      }`}>
                        {message.timestamp}
                      </p>}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] flex gap-3 flex-row">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-lg bg-slate-800 border border-white/5">
                      <Bot className="w-4 h-4 text-blue-400 animate-pulse" />
                    </div>
                    <div className="rounded-2xl px-4 py-3 bg-white/[0.03] border border-white/5 text-slate-200">
                      <div className="flex items-center gap-2 text-xs">
                        <div className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-slate-400">Agent thinking...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mx-4 p-2 bg-red-950/40 border border-red-500/20 text-red-400 rounded-lg text-[11px] flex justify-between items-center max-w-5xl md:mx-auto mb-2">
            <span>{error}</span>
            <button onClick={() => setError('')} className="hover:text-white transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Input Field */}
        <div className="border-t border-white/5 p-4 bg-slate-950/20">
          <div className="flex gap-3 max-w-5xl mx-auto items-end">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (!isLoading && query.trim()) {
                    handleSendQuery();
                  }
                }
              }}
              placeholder="Ask a question about connected databases or uploaded documents..."
              disabled={isLoading}
              rows={1}
              style={{ minHeight: '44px', maxHeight: '150px' }}
              className="flex-1 px-4 py-3 bg-slate-950/60 border border-white/5 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 text-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed resize-none overflow-y-auto"
            />
            <button
              onClick={handleSendQuery}
              disabled={!query.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-xl transition-all disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed flex items-center gap-1.5 text-xs font-semibold shadow-lg shadow-blue-500/10 h-[44px]"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Ask</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}