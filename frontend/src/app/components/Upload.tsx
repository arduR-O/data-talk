"use client";
import React, { useState } from 'react';

export default function UploadCard() {
  const [dbUrl, setDbUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  
  // Initialize with proper typing by providing initial values
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
    <div className="bg-[#FAF9F6] rounded-2xl shadow-lg border border-gray-200 w-full max-w-lg mx-auto p-6 space-y-6">
      <style jsx>{`
        .upload-icon {
          width: 32px;
          height: 32px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .database-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .key-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .file-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .check-circle-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .alert-circle-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .plus-icon {
          width: 24px;
          height: 24px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M12 4v16m8-8H4' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .x-icon {
          width: 16px;
          height: 16px;
          background: currentColor;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M6 18L18 6M6 6l12 12' /%3E%3C/svg%3E") no-repeat;
          mask-size: contain;
        }
        
        .connection-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        
        .connection-dot.connected {
          background-color: #10b981;
        }
        
        .connection-dot.disconnected {
          background-color: #ef4444;
        }
      `}</style>

      {/* Header */}
      <div className="text-center">
        <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-3">
          <div className="plus-icon text-white"></div>
        </div>
        <h2 className="text-xl font-semibold text-gray-900">Connect Sources</h2>
        <p className="text-sm text-gray-500 mt-1">Upload documents and connect data sources</p>
      </div>

      {/* Document Upload Section */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-900 flex items-center gap-2">
          <div className="file-icon text-gray-700"></div>
          Documents
        </h3>
        
        {/* Upload Area */}
        <div className="border-2 border-dashed border-black rounded-xl p-6 text-center hover:border-blue-300 transition-colors cursor-pointer group">
          <div className="upload-icon text-gray-400 mx-auto mb-3 group-hover:text-blue-500 transition-colors"></div>
          <p className="text-sm text-gray-600 mb-2">Drop PDF files here or click to browse</p>
          <button 
            onClick={handleFileUpload}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors"
          >
            Browse Files
          </button>
        </div>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 font-medium">Uploaded Files</p>
            {uploadedFiles.map((file) => (
              <div key={file.id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-3">
                  <div className="check-circle-icon text-green-600"></div>
                  <div>
                    <p className="text-sm text-green-800 font-medium">{file.name}</p>
                    <p className="text-xs text-green-600">{file.size}</p>
                  </div>
                </div>
                <button 
                  onClick={() => removeFile(file.id)}
                  className="text-green-600 hover:text-red-600 transition-colors"
                >
                  <div className="x-icon"></div>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Database Connection Section */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-900 flex items-center gap-2">
          <div className="database-icon text-gray-700"></div>
          Data Sources
        </h3>
        
        <div className="space-y-3">
          <div className="relative">
            <div className="database-icon text-gray-400 absolute left-3 top-3.5"></div>
            <input
              type="text"
              placeholder="Database URL"
              value={dbUrl}
              onChange={(e) => setDbUrl(e.target.value)}
              className="text-black w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm hover:border-gray-300 transition-colors"
            />
          </div>
          
          <div className="relative">
            <div className="key-icon text-gray-400 absolute left-3 top-3.5"></div>
            <input
              type="password"
              placeholder="API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="text-black w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm hover:border-gray-300 transition-colors"
            />
          </div>
          
          <button
            onClick={handleConnect}
            disabled={!dbUrl || !apiKey}
            className="w-full bg-blue-600 text-white py-3 rounded-xl hover:bg-blue-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium shadow-sm hover:shadow-md"
          >
            Connect Source
          </button>
        </div>
      </div>

      {/* Connected Sources */}
      {connections.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900">Active Connections</h3>
          <div className="space-y-2">
            {connections.map((connection) => (
              <div key={connection.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className={`connection-dot ${connection.status === 'connected' ? 'connected' : 'disconnected'}`}></div>
                  <div>
                    <p className="text-sm text-gray-900 font-medium">{connection.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{connection.type} connection</p>
                  </div>
                </div>
                <button 
                  onClick={() => removeConnection(connection.id)}
                  className="text-gray-400 hover:text-red-600 transition-colors"
                >
                  <div className="x-icon"></div>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      <div className="flex items-center justify-center gap-2 text-sm text-gray-500 pt-2 border-t border-gray-100">
        {connections.length > 0 ? (
          <>
            <div className="check-circle-icon text-green-500"></div>
            Connected to {connections.length} source{connections.length !== 1 ? 's' : ''}
          </>
        ) : (
          <>
            <div className="alert-circle-icon text-amber-500"></div>
            No sources connected
          </>
        )}
      </div>
    </div>
  );
}