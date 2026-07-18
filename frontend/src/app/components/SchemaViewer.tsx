import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Database, Table, Key, X, Loader2, ChevronRight, ChevronDown } from 'lucide-react';
import { API_BASE } from '../lib/api';

interface Column {
  name: string;
  type: string;
  primary_key: boolean;
}

interface TableInfo {
  name: string;
  columns: Column[];
  sample_rows: any[];
}

interface SchemaViewerProps {
  isOpen: boolean;
  onClose: () => void;
  token: string;
}

export default function SchemaViewer({ isOpen, onClose, token }: SchemaViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSchema();
    }
  }, [isOpen]);

  const fetchSchema = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/database/schema`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (response.ok) {
        if (data.tables && data.tables.length > 0) {
          setTables(data.tables);
          setExpandedTable(data.tables[0].name);
        } else {
          setError(data.message || 'No schema information found.');
        }
      } else {
        setError(data.detail || 'Failed to fetch schema');
      }
    } catch (err) {
      setError('Network error fetching schema.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;
  if (typeof window === 'undefined') return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[85vh] bg-[#030712] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/10 bg-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl flex items-center justify-center border border-white/10">
              <Database className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Database Schema</h2>
              <p className="text-xs text-slate-400">Live virtualization of connected tables</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 gap-4">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-slate-400 text-sm">Reflecting database schema...</p>
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 gap-2 text-center">
              <Database className="w-12 h-12 text-slate-600 mb-2 opacity-50" />
              <p className="text-red-400 text-sm font-medium">{error}</p>
              <p className="text-slate-500 text-xs mt-1">Please ensure a valid database is connected in your workspace.</p>
            </div>
          ) : tables.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 gap-2">
              <Table className="w-12 h-12 text-slate-600 mb-2 opacity-50" />
              <p className="text-slate-400 text-sm">No tables found in the database.</p>
            </div>
          ) : (
            <>
              {/* Sidebar: Table List */}
              <div className="w-full md:w-1/3 border-r border-white/10 bg-white/[0.02] overflow-y-auto scrollbar-hide">
                <div className="p-3">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-2">
                    Tables ({tables.length})
                  </h3>
                  <div className="space-y-1">
                    {tables.map(table => (
                      <button
                        key={table.name}
                        onClick={() => setExpandedTable(table.name)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all ${
                          expandedTable === table.name 
                            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' 
                            : 'text-slate-300 hover:bg-white/5 border border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <Table className={`w-4 h-4 flex-shrink-0 ${expandedTable === table.name ? 'text-blue-400' : 'text-slate-500'}`} />
                          <span className="truncate font-mono">{table.name}</span>
                        </div>
                        <ChevronRight className={`w-4 h-4 flex-shrink-0 transition-transform ${expandedTable === table.name ? 'opacity-100' : 'opacity-0'}`} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Main Area: Table Details */}
              <div className="flex-1 bg-[#030712] overflow-y-auto scrollbar-hide">
                {tables.map(table => {
                  if (table.name !== expandedTable) return null;
                  
                  return (
                    <div key={table.name} className="p-6 animate-in fade-in slide-in-from-right-4 duration-300">
                      
                      <div className="mb-8">
                        <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                          <span className="w-1 h-4 bg-blue-500 rounded-full"></span>
                          Columns
                        </h3>
                        <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                          <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-400 uppercase bg-black/20 border-b border-white/5">
                              <tr>
                                <th className="px-4 py-3 font-medium">Name</th>
                                <th className="px-4 py-3 font-medium">Type</th>
                                <th className="px-4 py-3 font-medium w-24 text-center">PK</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                              {table.columns.map((col, idx) => (
                                <tr key={idx} className="hover:bg-white/5 transition-colors">
                                  <td className="px-4 py-2.5 font-mono text-blue-200">
                                    <div className="flex items-center gap-2">
                                      {col.primary_key && <Key className="w-3 h-3 text-yellow-500 flex-shrink-0" />}
                                      {col.name}
                                    </div>
                                  </td>
                                  <td className="px-4 py-2.5 font-mono text-xs text-purple-300">{col.type}</td>
                                  <td className="px-4 py-2.5 text-center">
                                    {col.primary_key && <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.6)]"></span>}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                      
                      {table.sample_rows && table.sample_rows.length > 0 && (
                        <div>
                          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                            <span className="w-1 h-4 bg-purple-500 rounded-full"></span>
                            Data Snapshot (Sample)
                          </h3>
                          <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden h-[400px] flex flex-col">
                            {/* Header */}
                            <div className="flex bg-black/20 border-b border-white/5 px-4 py-3">
                              {table.columns.map(col => (
                                <div key={col.name} className="flex-1 font-medium text-xs text-slate-400 uppercase truncate pr-4">
                                  {col.name}
                                </div>
                              ))}
                            </div>
                            {/* Body */}
                            <div className="flex-1 overflow-y-auto scrollbar-hide">
                              {table.sample_rows.map((row: any, rowIdx: number) => (
                                <div key={rowIdx} className="flex items-center px-4 py-2 hover:bg-white/5 border-b border-white/[0.03] transition-colors">
                                  {table.columns.map((col: Column) => (
                                    <div key={col.name} className="flex-1 font-mono text-xs text-slate-300 truncate pr-4">
                                      {row[col.name] !== null && row[col.name] !== undefined ? String(row[col.name]) : <span className="text-slate-600 italic">null</span>}
                                    </div>
                                  ))}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                      
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
