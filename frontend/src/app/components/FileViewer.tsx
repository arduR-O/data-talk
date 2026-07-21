import React, { useState, useEffect } from 'react';
import { X, FileText, Table, Loader2 } from 'lucide-react';
import { API_BASE } from '../lib/api';

interface FileViewerProps {
  isOpen: boolean;
  onClose: () => void;
  filename: string;
  token: string;
}

export default function FileViewer({ isOpen, onClose, filename, token }: FileViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen && filename) {
      fetchFileContent();
    }
  }, [isOpen, filename]);

  const fetchFileContent = async () => {
    setLoading(true);
    setError('');
    setData(null);
    try {
      const response = await fetch(`${API_BASE}/api/uploadfiles/${encodeURIComponent(filename)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const resData = await response.json();
      
      if (response.ok) {
        setData(resData);
      } else {
        setError(resData.detail || 'Failed to load file contents');
      }
    } catch (err) {
      setError('Network error fetching file content.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-xs font-medium font-mono">Reading file contents...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
          <div className="w-12 h-12 rounded-full bg-red-950/20 border border-red-500/20 flex items-center justify-center text-red-400 mb-3">
            <X className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-red-200">{error}</p>
        </div>
      );
    }

    if (!data) return null;

    if (data.type === 'csv') {
      const filteredRows = searchQuery
        ? data.rows.filter((row: any) =>
            Object.values(row).some((val) =>
              String(val).toLowerCase().includes(searchQuery.toLowerCase())
            )
          )
        : data.rows;

      return (
        <div className="flex flex-col h-full overflow-hidden">
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search table rows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full max-w-md px-3.5 py-2 bg-slate-950/50 border border-white/5 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 text-xs transition-all"
            />
          </div>
          
          <div className="flex-1 overflow-auto rounded-xl border border-white/5 bg-slate-950/20 scrollbar-thin">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/60 sticky top-0 border-b border-white/5 backdrop-blur-md">
                  {data.columns.map((col: string) => (
                    <th key={col} className="px-4 py-3 font-semibold text-slate-300 border-r border-white/5 last:border-r-0 font-mono">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.length > 0 ? (
                  filteredRows.map((row: any, idx: number) => (
                    <tr key={idx} className="border-b border-white/5 last:border-b-0 hover:bg-white/[0.02] transition-colors">
                      {data.columns.map((col: string) => (
                        <td key={col} className="px-4 py-2.5 text-slate-300 font-mono border-r border-white/5 last:border-r-0 truncate max-w-xs">
                          {String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={data.columns.length} className="px-4 py-8 text-center text-slate-500">
                      No matching records found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Showing first {filteredRows.length} rows</span>
            <span>Total rows in file: {data.total_rows}</span>
          </div>
        </div>
      );
    }

    if (data.type === 'text') {
      return (
        <div className="flex-1 overflow-auto rounded-xl border border-white/5 bg-slate-950/40 p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed scrollbar-thin">
          {data.content}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-5xl h-[80vh] flex flex-col bg-slate-900/90 border border-white/10 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-slate-900/40">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-lg">
              {data?.type === 'csv' ? <Table className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white truncate font-mono">{filename}</h2>
              <p className="text-[10px] text-slate-400 mt-0.5 capitalize">{data?.type || 'File'} Preview</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/5 rounded-lg border border-transparent hover:border-white/5 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 p-6 overflow-hidden flex flex-col bg-slate-900/10">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
