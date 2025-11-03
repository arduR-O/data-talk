"use client";
import React, { useState } from 'react';

export default function UploadCard() {
  const [dbUrl, setDbUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  
  const [uploadedFiles, setUploadedFiles] = useState([
    // Empty array with proper type inference from initial dummy object
  ].filter(() => false) as Array<{
    id: number;
    name: string;
    size: string;
    status: string;
  }>);
  
  const [connections, setConnections] = useState([
    { id: 1, name: 'Sample Database', type: 'database', status: 'connected' },
    { id: 2, name: 'API Integration', type: 'api', status: 'connected' }
  ]);

  const handleConnect = () => {
    if (dbUrl && apiKey) {
      const newConnection = {
        id: Date.now(),
        name: `Database ${connections.length + 1}`,
        type: 'database',
        status: 'connected'
      };
      setConnections([...connections, newConnection]);
      setDbUrl('');
      setApiKey('');
    }
  };

  const removeConnection = (id: number) => {
    setConnections(connections.filter(conn => conn.id !== id));
  };

  const handleFileUpload = () => {
    // Simulate file upload
    const newFile = {
      id: Date.now(),
      name: `document_${uploadedFiles.length + 1}.pdf`,
      size: '2.4 MB',
      status: 'uploaded'
    };
    setUploadedFiles([...uploadedFiles, newFile]);
  };

  const removeFile = (id: number) => {
    setUploadedFiles(uploadedFiles.filter(file => file.id !== id));
  };

  return (
    <div className="bg-gradient-to-br from-white to-blue-50/30 rounded-3xl shadow-2xl border border-slate-200/60 w-full max-w-lg mx-auto p-8 space-y-8 backdrop-blur-sm">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
          Connect Sources
        </h2>
        <p className="text-slate-500 mt-2 font-medium">Upload documents and connect data sources</p>
      </div>

      {/* Document Upload Section */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Documents
        </h3>
        
        {/* Upload Area */}
        <div 
          onClick={handleFileUpload}
          className="border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-blue-400 transition-all duration-300 cursor-pointer group bg-white/50 backdrop-blur-sm hover:bg-blue-50/30"
        >
          <svg className="w-12 h-12 text-slate-400 mx-auto mb-4 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-sm text-slate-600 mb-3 font-medium">Drop PDF files here or click to browse</p>
          <button className="text-sm bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-2 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl">
            Browse Files
          </button>
        </div>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Uploaded Files</p>
            {uploadedFiles.map((file) => (
              <div key={file.id} className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200/60 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-green-800">{file.name}</p>
                    <p className="text-xs text-green-600 font-medium">{file.size}</p>
                  </div>
                </div>
                <button 
                  onClick={() => removeFile(file.id)}
                  className="w-8 h-8 bg-white border border-slate-200 rounded-lg flex items-center justify-center hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-all duration-200 shadow-sm"
                >
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" stroke-linejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Database Connection Section */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          Data Sources
        </h3>
        
        <div className="space-y-4">
          <div className="relative">
            <svg className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
            <input
              type="text"
              placeholder="Database URL"
              value={dbUrl}
              onChange={(e) => setDbUrl(e.target.value)}
              className="text-slate-800 w-full pl-12 pr-4 py-4 border border-slate-300/80 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 text-sm bg-white/80 backdrop-blur-sm placeholder-slate-500 hover:border-slate-400 transition-all duration-300 shadow-sm"
            />
          </div>
          
          <div className="relative">
            <svg className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            <input
              type="password"
              placeholder="API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="text-slate-800 w-full pl-12 pr-4 py-4 border border-slate-300/80 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 text-sm bg-white/80 backdrop-blur-sm placeholder-slate-500 hover:border-slate-400 transition-all duration-300 shadow-sm"
            />
          </div>
          
          <button
            onClick={handleConnect}
            disabled={!dbUrl || !apiKey}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-4 rounded-2xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed text-sm font-semibold shadow-lg hover:shadow-xl disabled:shadow-md"
          >
            Connect Source
          </button>
        </div>
      </div>

      {/* Connected Sources */}
      {connections.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-800">Active Connections</h3>
          <div className="space-y-3">
            {connections.map((connection) => (
              <div key={connection.id} className="flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/60 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className={`w-3 h-3 rounded-full ${connection.status === 'connected' ? 'bg-green-500' : 'bg-red-500'} shadow-sm`}></div>
                    <div className={`absolute inset-0 rounded-full ${connection.status === 'connected' ? 'bg-green-500' : 'bg-red-500'} animate-ping`}></div>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{connection.name}</p>
                    <p className="text-xs text-slate-500 font-medium capitalize">{connection.type} connection</p>
                  </div>
                </div>
                <button 
                  onClick={() => removeConnection(connection.id)}
                  className="w-8 h-8 bg-white border border-slate-200 rounded-lg flex items-center justify-center hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-all duration-200 shadow-sm"
                >
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" stroke-linejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      <div className="flex items-center justify-center gap-3 text-sm font-medium pt-4 border-t border-slate-200/60">
        {connections.length > 0 ? (
          <>
            <div className="w-3 h-3 bg-green-500 rounded-full shadow-sm"></div>
            <span className="text-green-700">Connected to {connections.length} source{connections.length !== 1 ? 's' : ''}</span>
          </>
        ) : (
          <>
            <div className="w-3 h-3 bg-amber-500 rounded-full shadow-sm"></div>
            <span className="text-amber-700">No sources connected</span>
          </>
        )}
      </div>
    </div>
  );
}