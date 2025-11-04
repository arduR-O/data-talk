"use client";

import React, { useEffect, useState } from 'react';
import axios from "axios";

export default function Inference() {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState([
    {
      type: 'system',
      content: 'Welcome to your AI Research Assistant. I\'m ready to analyze your documents and answer your questions with intelligent, contextual responses.',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Minimal markdown formatter: supports **bold** and escapes HTML
  const renderMarkdownToHtml = (text: string) => {
    if (!text) return '';
    const escapeHtml = (s: string) =>
      s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    const escaped = escapeHtml(text);
   
    const withBold = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>');
    return withBold;
  };

  const handleSendQuery = async () => {
  if (!query.trim() || isLoading) return;
  
  const userMessage = {
    type: 'user',
    content: query,
    timestamp: new Date().toLocaleTimeString()
  };
  
  setResponses(prev => [...prev, userMessage]);
  const currentQuery = query;
  setQuery('');
  setIsLoading(true);

  try {
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await axios.post(
      'http://localhost:8000/api/chat',
      {
        question: currentQuery,
      },
      {
        headers,
      }
    );
    
    const aiResponse = {
      type: 'assistant',
      content: response.data.response,
      timestamp: new Date().toLocaleTimeString()
    };
    setResponses(prev => [...prev, aiResponse]);
    
  } catch (error: any) {
    const errorMessage = {
      type: 'assistant',
      content: 'There was an error processing your request. Please try again.',
      timestamp: new Date().toLocaleTimeString()
    };
    setResponses(prev => [...prev, errorMessage]);
  } finally {
    setIsLoading(false);
  }
};

  return (
    <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-3xl shadow-2xl border border-slate-200/60 w-full max-w-4xl mx-auto flex flex-col h-[700px] backdrop-blur-sm">
      {/* Header */}
      <div className="border-b border-slate-200/60 px-8 py-6 bg-white/80 backdrop-blur-sm rounded-t-3xl">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
              AI Research Assistant
            </h2>
            <p className="text-slate-500 text-sm font-medium">Intelligent conversation with your documents</p>
          </div>
        </div>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 p-8 overflow-y-auto bg-gradient-to-b from-white/50 to-blue-50/30">
        <div className="space-y-6 max-w-4xl mx-auto">
          {responses.map((message, index) => (
            <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] flex gap-4 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${
                  message.type === 'user' 
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                    : message.type === 'system'
                    ? 'bg-gradient-to-br from-amber-400 to-orange-500'
                    : 'bg-gradient-to-br from-slate-600 to-slate-700'
                }`}>
                  {message.type === 'user' ? (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  ) : message.type === 'system' ? (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  )}
                </div>
                
                {/* Message Content */}
                <div className={`rounded-3xl px-6 py-4 backdrop-blur-sm shadow-lg ${
                  message.type === 'user' 
                    ? 'bg-gradient-to-br from-blue-500 to-purple-500 text-white' 
                    : message.type === 'system'
                    ? 'bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 text-amber-800'
                    : 'bg-white/90 border border-slate-200/60 text-slate-800'
                }`}>
                  {(() => {
                    // Extract <think>...</think> content from assistant messages
                    const extractThink = (text: string) => {
                      if (!text) return { visible: '', think: '' };
                      // Look for <think>...</think> tags - both opening and closing use "think"
                      const regex = /<think>([\s\S]*?)<\/think>/g;
                      const matches = Array.from(text.matchAll(regex));
                      const thinkText = matches
                        .map(match => match[1]?.trim())
                        .filter(Boolean)
                        .join('\n\n');
                      const visible = text.replace(regex, '').trim();
                      return { visible, think: thinkText };
                    };
                    const parsed = message.type === 'assistant' ? extractThink(message.content as any) : { visible: message.content, think: '' };
                    return (
                      <>
                        {message.type === 'assistant' ? (
                          <div
                            className="text-sm leading-relaxed whitespace-pre-wrap space-y-2"
                            dangerouslySetInnerHTML={{ __html: renderMarkdownToHtml(parsed.visible) }}
                          />
                        ) : (
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{parsed.visible}</p>
                        )}
                        {parsed.think && message.type === 'assistant' && (
                          <details className="mt-3 group">
                            <summary className="text-xs cursor-pointer select-none text-slate-500 hover:text-slate-700 transition-colors font-medium">
                              🤔 View Reasoning
                            </summary>
                            <div className="mt-2 text-xs text-slate-600 bg-slate-50/80 border border-slate-200 rounded-xl p-3 whitespace-pre-wrap backdrop-blur-sm">
                              {parsed.think}
                            </div>
                          </details>
                        )}
                      </>
                    );
                  })()}
                  {isClient && <p className={`text-xs mt-3 font-medium ${
                    message.type === 'user' 
                      ? 'text-blue-100' 
                      : message.type === 'system'
                      ? 'text-amber-600'
                      : 'text-slate-500'
                  }`}>
                    {message.timestamp}
                  </p>}
                </div>
              </div>
            </div>
          ))}
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[85%] flex gap-4 flex-row">
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg bg-gradient-to-br from-slate-600 to-slate-700">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="rounded-3xl px-6 py-4 backdrop-blur-sm shadow-lg bg-white/90 border border-slate-200/60 text-slate-800">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm text-slate-600">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200/60 p-8 bg-white/60 backdrop-blur-sm rounded-b-3xl">
        <div className="flex gap-4 flex-wrap">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSendQuery()}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              className="w-full px-6 py-4 border border-slate-300/80 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 text-sm bg-white/90 text-slate-900 placeholder-slate-500 hover:border-slate-400 transition-all duration-300 shadow-lg backdrop-blur-sm pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-400 text-sm">
              ⏎ Enter
            </div>
          </div>
          <button
            onClick={handleSendQuery}
            disabled={!query.trim() || isLoading}
            className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-4 rounded-2xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed flex items-center gap-3 font-semibold shadow-lg hover:shadow-xl disabled:shadow-md min-w-[120px] justify-center"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
                <span>Send</span>
              </>
            )}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-4 text-center font-medium">
          💡 Responses are generated based on your uploaded documents and data sources
        </p>
      </div>
    </div>
  );
}