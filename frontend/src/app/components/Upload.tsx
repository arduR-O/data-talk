"use client";
import React, { useState, useRef } from 'react';

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  status: 'uploading' | 'uploaded' | 'error';
}

export default function UploadCard() {
  const [dbUrl, setDbUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [connections, setConnections] = useState<
    Array<{ id: number; name: string; type: string; status: string }>
  >([]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please log in to upload files');
      return;
    }

    setUploading(true);

    // Create FormData and append all files
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    // Add files to state with 'uploading' status
    const newFiles: UploadedFile[] = Array.from(files).map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      name: file.name,
      size: formatFileSize(file.size),
      status: 'uploading' as const,
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);

    try {
      const response = await fetch('http://localhost:8000/api/uploadfiles/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // Update file status to uploaded
        setUploadedFiles((prev) =>
          prev.map((file) =>
            newFiles.some((nf) => nf.id === file.id)
              ? { ...file, status: 'uploaded' as const }
              : file
          )
        );
        console.log('Files uploaded successfully:', data);
      } else {
        // Update file status to error
        setUploadedFiles((prev) =>
          prev.map((file) =>
            newFiles.some((nf) => nf.id === file.id)
              ? { ...file, status: 'error' as const }
              : file
          )
        );
        alert(data.detail || 'Failed to upload files');
      }
    } catch (error) {
      console.error('Upload error:', error);
      // Update file status to error
      setUploadedFiles((prev) =>
        prev.map((file) =>
          newFiles.some((nf) => nf.id === file.id)
            ? { ...file, status: 'error' as const }
            : file
        )
      );
      alert('Network error. Please check your connection and try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileUpload(e.target.files);
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleConnect = async () => {
    if (!dbUrl.trim()) {
      setConnectionError('Please enter a database URL');
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      setConnectionError('Please log in to connect a database');
      return;
    }

    setConnecting(true);
    setConnectionError('');

    try {
      const response = await fetch('http://localhost:8000/api/database-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          db_url: dbUrl.trim(),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Add connection to the list
        const newConnection = {
          id: Date.now(),
          name: dbUrl.trim(),
          type: 'database',
          status: 'connected'
        };
        setConnections([...connections, newConnection]);
        setDbUrl('');
        setApiKey('');
        setConnectionError('');
        console.log('Database URL saved successfully:', data);
      } else {
        setConnectionError(data.detail || 'Failed to connect database');
      }
    } catch (error) {
      console.error('Connection error:', error);
      setConnectionError('Network error. Please check your connection and try again.');
    } finally {
      setConnecting(false);
    }
  };

  const removeConnection = (id: number) => {
    setConnections(connections.filter(conn => conn.id !== id));
  };

  const removeFile = (id: string) => {
    setUploadedFiles(uploadedFiles.filter(file => file.id !== id));
  };

  const getFileStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return (
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
        );
      case 'uploaded':
        return (
          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
    }
  };

  const getFileStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'from-blue-50 to-blue-50 border-blue-200/60';
      case 'uploaded':
        return 'from-green-50 to-emerald-50 border-green-200/60';
      case 'error':
        return 'from-red-50 to-red-50 border-red-200/60';
    }
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
        
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileInputChange}
          className="hidden"
        />
        
        {/* Upload Area */}
        <div 
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 cursor-pointer group backdrop-blur-sm ${
            isDragging
              ? 'border-blue-500 bg-blue-100/50'
              : 'border-slate-300 hover:border-blue-400 bg-white/50 hover:bg-blue-50/30'
          } ${uploading ? 'pointer-events-none opacity-50' : ''}`}
        >
          <svg className={`w-12 h-12 mx-auto mb-4 transition-colors ${
            isDragging ? 'text-blue-500' : 'text-slate-400 group-hover:text-blue-500'
          }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-sm text-slate-600 mb-3 font-medium">
            {isDragging ? 'Drop files here' : 'Drop PDF files here or click to browse'}
          </p>
          <button 
            type="button"
            className="text-sm bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-2 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl"
          >
            {uploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </div>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Uploaded Files</p>
            {uploadedFiles.map((file) => (
              <div key={file.id} className={`flex items-center justify-between p-4 bg-gradient-to-r rounded-xl border shadow-sm ${getFileStatusColor(file.status)}`}>
                <div className="flex items-center gap-3">
                  {getFileStatusIcon(file.status)}
                  <div>
                    <p className={`text-sm font-semibold ${
                      file.status === 'uploaded' ? 'text-green-800' : 
                      file.status === 'error' ? 'text-red-800' : 
                      'text-blue-800'
                    }`}>
                      {file.name}
                    </p>
                    <p className={`text-xs font-medium ${
                      file.status === 'uploaded' ? 'text-green-600' : 
                      file.status === 'error' ? 'text-red-600' : 
                      'text-blue-600'
                    }`}>
                      {file.size} {file.status === 'uploading' && '• Uploading...'}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => removeFile(file.id)}
                  className="w-8 h-8 bg-white border border-slate-200 rounded-lg flex items-center justify-center hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-all duration-200 shadow-sm"
                  disabled={file.status === 'uploading'}
                >
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
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
              placeholder="API Key (Optional)"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="text-slate-800 w-full pl-12 pr-4 py-4 border border-slate-300/80 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 text-sm bg-white/80 backdrop-blur-sm placeholder-slate-500 hover:border-slate-400 transition-all duration-300 shadow-sm"
            />
          </div>
          
          {/* Error Message */}
          {connectionError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {connectionError}
              </div>
            </div>
          )}
          
          <button
            onClick={handleConnect}
            disabled={!dbUrl.trim() || connecting}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-4 rounded-2xl hover:from-blue-600 hover:to-purple-600 transition-all duration-300 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed text-sm font-semibold shadow-lg hover:shadow-xl disabled:shadow-md flex items-center justify-center gap-2"
          >
            {connecting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Connecting...
              </>
            ) : (
              'Connect Source'
            )}
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