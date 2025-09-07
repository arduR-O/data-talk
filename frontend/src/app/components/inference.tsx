"use client";

import React, { useState } from 'react';

export default function Inference() {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState([
    {
      type: 'system',
      content: 'Welcome to your AI Research Assistant. I\'m ready to analyze your documents and answer your questions with intelligent, contextual responses.',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);

  const handleSendQuery = () => {
    if (!query.trim()) return;
    
    const newQuery = {
      type: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    };
    
    const aiResponse = {
      type: 'assistant',
      content: `I understand you're asking about "${query}". Based on your uploaded documents and connected data sources, I can provide detailed analysis and insights. This demonstrates the AI's capability to understand context and provide relevant, well-researched responses tailored to your specific query.`,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setResponses([...responses, newQuery, aiResponse]);
    setQuery('');
  };

  return (
    <div className="bg-[#FAF9F6] rounded-2xl shadow-lg border border-gray-200 w-full max-w-4xl mx-auto flex flex-col h-[600px]">
      <style jsx>{`
        .chat-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a9.863 9.863 0 01-4.906-1.298L3 21l2.298-5.094A9.863 9.863 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .user-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .sparkles-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M5 3l1.5 1.5L5 6 3.5 4.5 5 3zM12 12l1.5-1.5L12 9l-1.5 1.5L12 12zM19 21l-1.5-1.5L19 18l1.5 1.5L19 21zM3 12l1.5-1.5L3 9l-1.5 1.5L3 12z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .bot-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          border-radius: 2px;
          position: relative;
        }
        
        .bot-icon::before {
          content: '';
          position: absolute;
          width: 6px;
          height: 6px;
          background: currentColor;
          border-radius: 50%;
          top: 3px;
          left: 2px;
        }
        
        .bot-icon::after {
          content: '';
          position: absolute;
          width: 6px;
          height: 6px;
          background: currentColor;
          border-radius: 50%;
          top: 3px;
          right: 2px;
        }
        
        .send-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M12 19l9 2-9-18-9 18 9-2zm0 0v-8' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
      `}</style>

      {/* Header */}
      <div className="border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <div className="chat-icon text-white"></div>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">AI Research Assistant</h2>
            <p className="text-sm text-gray-500">Intelligent conversation with your documents</p>
          </div>
        </div>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 p-6 overflow-y-auto bg-[#FAF9F6]">
        <div className="space-y-4">
          {responses.map((message, index) => (
            <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.type === 'user' 
                    ? 'bg-blue-600' 
                    : message.type === 'system'
                    ? 'bg-amber-500'
                    : 'bg-gray-700'
                }`}>
                  {message.type === 'user' ? (
                    <div className="user-icon text-white"></div>
                  ) : message.type === 'system' ? (
                    <div className="sparkles-icon text-white"></div>
                  ) : (
                    <div className="bot-icon text-white"></div>
                  )}
                </div>
                
                {/* Message Content */}
                <div className={`rounded-2xl px-4 py-3 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : message.type === 'system'
                    ? 'bg-amber-50 border border-amber-200 text-amber-800'
                    : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
                }`}>
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={`text-xs mt-2 ${
                    message.type === 'user' 
                      ? 'text-blue-100' 
                      : message.type === 'system'
                      ? 'text-amber-600'
                      : 'text-gray-500'
                  }`}>
                    {message.timestamp}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-100 p-6 bg-[#FAF9F6] rounded-b-2xl">
        <div className="flex gap-3 flex-wrap">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendQuery()}
            placeholder="Ask a question about your documents..."
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white text-gray-900 placeholder-gray-500 hover:border-gray-300 transition-colors"
          />
          <button
            onClick={handleSendQuery}
            disabled={!query.trim()}
            className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-sm hover:shadow-md"
          >
            <div className="send-icon"></div>
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-3 text-center">
          Responses are generated based on your uploaded documents and data sources
        </p>
      </div>
    </div>
  );
}