"use client";
import React, { useState, useRef, useEffect } from 'react';
import { Database, CloudUpload, FileText, CheckCircle, AlertCircle, X, Loader2, DatabaseBackup, ChevronDown, Eye } from "lucide-react";
import { API_BASE } from '../lib/api';
import SchemaViewer from './SchemaViewer';

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  status: 'uploading' | 'uploaded' | 'error';
}

interface Connection {
  id: number;
  name: string;
  type: string;
  status: string;
}

export default function UploadCard() {
  const [dbUrl, setDbUrl] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const [loading, setLoading] = useState(true);
  const [filesDropdownOpen, setFilesDropdownOpen] = useState(true);
  const [isSchemaViewerOpen, setIsSchemaViewerOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [connections, setConnections] = useState<Connection[]>([]);

  const getAuthToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  useEffect(() => {
    loadPersistedData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPersistedData = async () => {
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // Load uploaded files
      const filesResponse = await fetch(`${API_BASE}/api/uploadfiles/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (filesResponse.ok) {
        const filesData = await filesResponse.json();
        const loadedFiles: UploadedFile[] = filesData.files.map((file: any) => ({
          id: file.filename,
          name: file.filename,
          size: formatFileSize(file.size),
          status: 'uploaded' as const
        }));
        setUploadedFiles(loadedFiles);
      }

      // Load database connection details
      const dbResponse = await fetch(`${API_BASE}/api/database-url`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (dbResponse.ok) {
        const dbData = await dbResponse.json();
        if (dbData.configured && dbData.db_url) {
          setDbUrl(dbData.db_url);
          setConnections([{
            id: 1,
            name: dbData.db_url,
            type: 'database',
            status: 'connected'
          }]);
        }
      }
    } catch (error) {
      console.error('Failed to load persisted data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const token = getAuthToken();
    if (!token) {
      alert('Please log in to upload files');
      return;
    }

    setUploading(true);

    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const newFiles: UploadedFile[] = Array.from(files).map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      name: file.name,
      size: formatFileSize(file.size),
      status: 'uploading' as const,
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);

    try {
      const response = await fetch(`${API_BASE}/api/uploadfiles/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadedFiles((prev) =>
          prev.map((file) =>
            newFiles.some((nf) => nf.id === file.id)
              ? { ...file, status: 'uploaded' as const }
              : file
          )
        );
        // Refresh sources lists after successful file processing
        loadPersistedData();
      } else {
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

    const token = getAuthToken();
    if (!token) {
      setConnectionError('Please log in to connect a database');
      return;
    }

    setConnecting(true);
    setConnectionError('');

    try {
      const response = await fetch(`${API_BASE}/api/database-url`, {
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
        const newConnection = {
          id: 1,
          name: dbUrl.trim(),
          type: 'database',
          status: 'connected'
        };
        setConnections([newConnection]);
        setConnectionError('');
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

  const removeConnection = async (id: number) => {
    const token = getAuthToken();
    if (!token) return;

    try {
      await fetch(`${API_BASE}/api/database-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ db_url: '' }),
      });
      
      setConnections([]);
      setDbUrl('');
    } catch (error) {
      console.error('Failed to remove connection:', error);
    }
  };

  const removeFile = async (filename: string) => {
    const token = getAuthToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE}/api/uploadfiles/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setUploadedFiles(prev => prev.filter(file => file.name !== filename));
        // Reset DB Connection URL if the file deleted was their active database SQLite session
        if (dbUrl && dbUrl.includes(filename)) {
          setDbUrl('');
          setConnections([]);
        }
      } else {
        alert('Failed to delete file');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete file');
    }
  };

  const getFileStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-400" />;
      case 'uploaded':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getFileStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'from-blue-950/20 to-indigo-950/20 border-blue-500/20 text-blue-300';
      case 'uploaded':
        return 'from-emerald-950/20 to-green-950/20 border-emerald-500/20 text-emerald-300';
      case 'error':
        return 'from-red-950/20 to-red-950/20 border-red-500/20 text-red-300';
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900/40 border border-white/5 rounded-2xl shadow-2xl w-full h-full p-6 flex flex-col justify-center items-center backdrop-blur-md">
        <div className="flex items-center gap-2.5 text-slate-400 text-xs">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Synchronizing data sources...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full pr-4 py-2 space-y-6 overflow-y-auto relative flex flex-col justify-between">
      
      <div className="space-y-6">
        {/* Title */}
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-400" />
            Workspace Sources
          </h2>
          <p className="text-[10px] text-slate-400 mt-0.5">Manage connected databases & RAG documents</p>
        </div>

        {/* Drag and Drop Zone */}
        <div className="space-y-3">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md,.csv,.db,.sqlite"
            onChange={handleFileInputChange}
            className="hidden"
          />
          
          <div 
            onClick={handleClick}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`border border-dashed rounded-xl p-6 text-center transition-all duration-300 cursor-pointer backdrop-blur-sm ${
              isDragging
                ? 'border-blue-500 bg-blue-950/10'
                : 'border-white/10 hover:border-white/20 bg-slate-950/20 hover:bg-slate-950/30'
            } ${uploading ? 'pointer-events-none opacity-40' : ''}`}
          >
            <CloudUpload className={`w-8 h-8 mx-auto mb-3 transition-colors ${
              isDragging ? 'text-blue-400' : 'text-slate-500'
            }`} />
            <p className="text-xs text-slate-400 mb-2 font-medium">
              {isDragging ? 'Drop files here' : 'Drop PDF, TXT, MD, CSV, or DB/SQLITE files here'}
            </p>
            <span className="text-[10px] text-slate-500 font-semibold px-2 py-1 bg-white/5 border border-white/10 rounded-lg">
              {uploading ? 'Processing...' : 'Browse Local Files'}
            </span>
          </div>
        </div>

        {/* Dynamic Database Input Section */}
        <div className="space-y-3 pt-3 border-t border-white/5">
          <h3 className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5 uppercase tracking-wide">
            <DatabaseBackup className="w-3.5 h-3.5" /> Database URL mapping
          </h3>
          
          <div className="space-y-3">
            <div className="relative">
              <input
                type="text"
                placeholder="postgresql://user:pass@host:port/dbname"
                value={dbUrl}
                onChange={(e) => setDbUrl(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/60 border border-white/5 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 text-xs transition-all"
              />
            </div>
            
            {/* Active Database Status Banner */}
            <div className={`p-3.5 rounded-xl border text-xs shadow-sm transition-all duration-300 ${
              dbUrl && !dbUrl.includes('datatalk_demo.db')
                ? 'bg-emerald-950/15 border-emerald-500/20 text-emerald-300'
                : 'bg-blue-950/15 border-blue-500/20 text-blue-300'
            }`}>
              <div className="flex items-start gap-2.5">
                <div className="relative mt-0.5">
                  <div className={`w-2.5 h-2.5 rounded-full ${
                    dbUrl && !dbUrl.includes('datatalk_demo.db') ? 'bg-green-500' : 'bg-blue-500'
                  } shadow-sm`}></div>
                </div>
                <div className="flex-1 flex items-center justify-between gap-2 min-w-0">
                  <div className="min-w-0">
                    <p className="font-bold truncate">
                      {dbUrl && !dbUrl.includes('datatalk_demo.db') 
                        ? 'Connected to Active Database' 
                        : 'Active Database: Fictional Company (Demo)'}
                    </p>
                    <p className="text-[10px] mt-1 opacity-80 leading-relaxed font-mono truncate">
                      {dbUrl && !dbUrl.includes('datatalk_demo.db')
                        ? dbUrl.split('@')[1] || dbUrl
                        : 'Tables: employee, department, project, employee_project'}
                    </p>
                  </div>
                  <button
                    onClick={() => setIsSchemaViewerOpen(true)}
                    className="flex-shrink-0 p-1.5 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 text-white flex items-center gap-1.5 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span className="hidden xl:inline">View Schema</span>
                  </button>
                </div>
              </div>
            </div>
            
            {connectionError && (
              <div className="p-2.5 bg-red-950/15 border border-red-500/20 rounded-xl text-red-400 text-[11px] flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{connectionError}</span>
              </div>
            )}
            
            <button
              onClick={handleConnect}
              disabled={!dbUrl.trim() || connecting}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-xl transition-all disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-xs font-semibold shadow-md flex items-center justify-center gap-1.5"
            >
              {connecting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{connections.length > 0 ? 'Update Connection String' : 'Map Connection String'}</span>
            </button>
          </div>
        </div>

        {/* Uploaded Documents List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-white/5">
            <button
              onClick={() => setFilesDropdownOpen(!filesDropdownOpen)}
              className="w-full flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wide cursor-pointer hover:text-white transition-colors"
            >
              <span className="flex items-center gap-1.5"><FileText className="w-3.5 h-3.5" /> Uploaded documents ({uploadedFiles.length})</span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${filesDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {filesDropdownOpen && (
              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {uploadedFiles.map((file) => (
                  <div key={file.id} className={`flex items-center justify-between p-2.5 bg-white/[0.01] rounded-xl border shadow-sm ${getFileStatusColor(file.status)}`}>
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      {getFileStatusIcon(file.status)}
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold truncate">
                          {file.name}
                        </p>
                        <p className="text-[9px] opacity-70">
                          {file.size} {file.status === 'uploading' && '• Processing vectors...'}
                        </p>
                      </div>
                    </div>
                    <button 
                      onClick={() => removeFile(file.name)}
                      className="p-1 rounded-lg bg-slate-950/20 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-white/5 transition-all disabled:opacity-40"
                      disabled={file.status === 'uploading'}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Connection Status indicator */}
      <div className="flex items-center justify-center gap-2 text-xs font-semibold pt-4 border-t border-white/5 text-slate-400 mt-6">
        {connections.length > 0 || uploadedFiles.length > 0 ? (
          <>
            <div className="w-2 h-2 bg-green-500 rounded-full shadow-sm shadow-green-500/50"></div>
            <span className="text-green-400/90">
              {[
                connections.length > 0 && `${connections.length} custom DB mapped`,
                uploadedFiles.length > 0 && `${uploadedFiles.length} file${uploadedFiles.length !== 1 ? 's' : ''} active`
              ].filter(Boolean).join(' • ')}
            </span>
          </>
        ) : (
          <>
            <div className="w-2 h-2 bg-blue-500 rounded-full shadow-sm shadow-blue-500/50"></div>
            <span className="text-blue-400/90">Seeded Demo Database Active</span>
          </>
        )}
      </div>

      <SchemaViewer 
        isOpen={isSchemaViewerOpen} 
        onClose={() => setIsSchemaViewerOpen(false)} 
        token={getAuthToken() || ''}
      />
    </div>
  );
}