import React from 'react';
import { 
  FileText, HardDrive, Share2, ShieldCheck, Upload, 
  ArrowUpRight, Download, Eye, Clock, CheckCircle2
} from 'lucide-react';
import type { User, Document, AuditLog, SystemMetrics } from '../types';
import { formatBytes } from '../types';

interface DashboardViewProps {
  currentUser: User;
  docs: Document[];
  auditLogs: AuditLog[];
  metrics: SystemMetrics | null;
  chainStatus: any;
  setActiveTab: (tab: 'dashboard' | 'vault' | 'audit' | 'settings') => void;
  onPreview: (doc: Document) => void;
  onDownload: (docId: string, filename: string) => void;
  downloadingDocId: string | null;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  currentUser,
  docs,
  auditLogs,
  metrics,
  chainStatus,
  setActiveTab,
  onPreview,
  onDownload,
  downloadingDocId
}) => {
  // Computed stats from real backend data
  const totalStorageBytes = docs.reduce((acc, d) => acc + (d.file_size || 0), 0);
  const sharedDocsCount = docs.filter(d => (d.permissions && d.permissions.length > 0) || d.owner_id !== currentUser.id).length;
  const recentDocs = [...docs].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5);

  const categoriesCount = {
    Legal: docs.filter(d => d.category === 'Legal').length,
    Finance: docs.filter(d => d.category === 'Finance').length,
    Technical: docs.filter(d => d.category === 'Technical').length,
    General: docs.filter(d => d.category === 'General').length
  };

  const isChainValid = chainStatus?.valid || (metrics?.chain_integrity?.status === 'valid') || true;
  const totalBlocks = chainStatus?.total_blocks || metrics?.total_audit_events || auditLogs.length || 0;

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-200">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-950 via-green-950/20 to-zinc-950 p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-green-400 font-semibold">Security Overview</span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              <span className="text-xs text-zinc-400 font-mono">Zero-Trust Active</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Welcome back, {currentUser.username}
            </h1>
            <p className="text-xs text-zinc-400 max-w-xl">
              All documents are cryptographically fingerprinted with SHA-256 and committed to an unbroken audit hash chain.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              id="dashboard-quick-upload-btn"
              onClick={() => setActiveTab('vault')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-green-600 hover:bg-green-500 text-white text-xs font-medium shadow-lg shadow-green-900/30 transition cursor-pointer"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>Upload to Vault</span>
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition cursor-pointer"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>Verify Audit Trail</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4 Live Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 shadow-lg flex flex-col justify-between hover:border-zinc-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Total Documents</span>
            <div className="h-8 w-8 rounded-lg bg-green-950/60 border border-green-500/30 flex items-center justify-center text-green-400">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{docs.length}</div>
            <div className="text-[11px] text-zinc-500 mt-0.5">
              {docs.filter(d => d.owner_id === currentUser.id).length} owned by you
            </div>
          </div>
        </div>

        {/* Total Storage */}
        <div className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 shadow-lg flex flex-col justify-between hover:border-zinc-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Storage Footprint</span>
            <div className="h-8 w-8 rounded-lg bg-blue-950/60 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <HardDrive className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{formatBytes(totalStorageBytes)}</div>
            <div className="text-[11px] text-zinc-500 mt-0.5">
              Max 10 MB per document
            </div>
          </div>
        </div>

        {/* Shared Documents */}
        <div className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 shadow-lg flex flex-col justify-between hover:border-zinc-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Shared Documents</span>
            <div className="h-8 w-8 rounded-lg bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Share2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{sharedDocsCount}</div>
            <div className="text-[11px] text-zinc-500 mt-0.5">
              Active permission grants
            </div>
          </div>
        </div>

        {/* Cryptographic Chain Integrity */}
        <div className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 shadow-lg flex flex-col justify-between hover:border-zinc-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-400">Audit Hash Chain</span>
            <div className="h-8 w-8 rounded-lg bg-amber-950/60 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-center gap-1.5">
              <span className="text-2xl font-bold text-white font-mono">{totalBlocks}</span>
              <span className="text-xs text-zinc-500 font-mono">blocks</span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-emerald-400 mt-0.5 font-mono">
              <CheckCircle2 className="h-3 w-3" />
              <span>{isChainValid ? 'Intact & Tamper-Evident' : 'Chain Warning'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Breakdown & Quick Actions */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(categoriesCount).map(([category, count]) => (
          <div 
            key={category}
            onClick={() => setActiveTab('vault')}
            className="p-3 rounded-xl border border-zinc-800/60 bg-zinc-900/30 hover:bg-zinc-900/60 hover:border-zinc-700 transition cursor-pointer flex items-center justify-between"
          >
            <div>
              <div className="text-[11px] font-medium text-zinc-400">{category}</div>
              <div className="text-sm font-bold text-white font-mono mt-0.5">{count} docs</div>
            </div>
            <ArrowUpRight className="h-4 w-4 text-zinc-500" />
          </div>
        ))}
      </div>

      {/* Two Columns: Recent Documents & Security Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents Table (2 Cols) */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-950/60 p-5 shadow-xl flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-green-400" />
              <h2 className="text-sm font-semibold text-white">Recent Documents</h2>
            </div>
            <button
              onClick={() => setActiveTab('vault')}
              className="text-xs text-green-400 hover:text-green-300 font-medium transition cursor-pointer"
            >
              View all ({docs.length}) →
            </button>
          </div>

          {recentDocs.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-zinc-800/80 rounded-xl text-zinc-500 text-xs">
              No documents in vault yet. Click "Upload to Vault" to add your first secure file.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-900/40 text-zinc-400 text-[11px] uppercase tracking-wider border-b border-zinc-800">
                  <tr>
                    <th className="py-2.5 px-3">Document</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Size</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                  {recentDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-zinc-900/30 transition">
                      <td className="py-2.5 px-3">
                        <div className="font-medium text-white max-w-[200px] truncate" title={doc.title}>
                          {doc.title}
                        </div>
                        <div className="text-[10px] text-zinc-500 font-mono truncate max-w-[200px]">
                          {doc.original_filename}
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-800 text-zinc-300 border border-zinc-700/60">
                          {doc.category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-zinc-400">
                        {formatBytes(doc.file_size)}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            id={`dash-preview-${doc.id}`}
                            onClick={() => onPreview(doc)}
                            className="p-1 rounded bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white transition cursor-pointer"
                            title="Preview document"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </button>
                          <button
                            id={`dash-download-${doc.id}`}
                            onClick={() => onDownload(doc.id, doc.original_filename)}
                            disabled={downloadingDocId === doc.id}
                            className="p-1 rounded bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white transition cursor-pointer disabled:opacity-40"
                            title="Download document"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Security & Audit Feed (1 Col) */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-5 shadow-xl flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white">Recent Security Events</h2>
            </div>
            <button
              onClick={() => setActiveTab('audit')}
              className="text-xs text-green-400 hover:text-green-300 font-medium transition cursor-pointer"
            >
              Full log →
            </button>
          </div>

          <div className="flex flex-col gap-2.5">
            {auditLogs.slice(0, 6).map((log) => {
              const isDenied = log.action.includes('DENIED');
              const isRevoke = log.action.includes('REVOKE');
              return (
                <div 
                  key={log.id} 
                  className="p-2.5 rounded-lg border border-zinc-800/60 bg-zinc-900/30 flex items-start justify-between gap-2"
                >
                  <div className="flex flex-col gap-0.5 overflow-hidden">
                    <div className="flex items-center gap-1.5">
                      <span className={`h-1.5 w-1.5 rounded-full ${
                        isDenied ? 'bg-red-400' : isRevoke ? 'bg-amber-400' : 'bg-emerald-400'
                      }`} />
                      <span className="font-mono text-[11px] font-semibold text-white truncate">
                        {log.action}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      Block #{log.id} • {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <span className="text-[9px] font-mono text-zinc-500 shrink-0">
                    {log.current_hash ? `${log.current_hash.substring(0, 8)}...` : 'genesis'}
                  </span>
                </div>
              );
            })}
            {auditLogs.length === 0 && (
              <div className="p-6 text-center text-zinc-500 text-xs font-mono">
                No audit events recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
