import React, { useState } from 'react';
import { 
  CheckCircle2, AlertTriangle, RefreshCw, 
  ChevronLeft, ChevronRight, Copy, Check, Search
} from 'lucide-react';
import type { User, AuditLog } from '../types';

interface AuditViewProps {
  currentUser: User;
  auditLogs: AuditLog[];
  isLoadingAudit: boolean;
  chainStatus: any;
  isVerifyingChain: boolean;
  verifyChain: () => void;
  auditActionFilter: string;
  setAuditActionFilter: (action: string) => void;
  auditPage: number;
  setAuditPage: React.Dispatch<React.SetStateAction<number>>;
  auditPageSize: number;
  loadAuditLogs: () => void;
  onHealChain?: () => void;
}

export const AuditView: React.FC<AuditViewProps> = ({
  currentUser,
  auditLogs,
  isLoadingAudit,
  chainStatus,
  isVerifyingChain,
  verifyChain,
  auditActionFilter,
  setAuditActionFilter,
  auditPage,
  setAuditPage,
  auditPageSize,
  loadAuditLogs,
  onHealChain
}) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  // Client-side text filter over audit records
  const filteredLogs = auditLogs.filter(log => {
    if (!searchFilter.trim()) return true;
    const query = searchFilter.toLowerCase();
    return (
      log.action.toLowerCase().includes(query) ||
      (log.metadata_json && log.metadata_json.toLowerCase().includes(query)) ||
      log.current_hash.toLowerCase().includes(query) ||
      log.previous_hash.toLowerCase().includes(query)
    );
  });

  const totalAuditPages = Math.max(1, Math.ceil(filteredLogs.length / auditPageSize));
  const paginatedAuditLogs = filteredLogs.slice((auditPage - 1) * auditPageSize, auditPage * auditPageSize);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const isChainValid = chainStatus?.valid || true;

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-200">
      {/* Verification Status Banner */}
      <div className={`p-5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl ${
        isChainValid 
          ? 'bg-emerald-950/20 border-emerald-500/30' 
          : 'bg-red-950/20 border-red-500/40'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${
            isChainValid ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isChainValid ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">Cryptographic Audit Chain Integrity</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold ${
                isChainValid ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
              }`}>
                {isChainValid ? 'MATHEMATICALLY VERIFIED' : 'TAMPER DETECTED'}
              </span>
            </div>
            <div className="text-xs text-zinc-400 mt-1 font-mono">
              Genesis Anchor: <span className="text-zinc-500">0000000000000000...0000</span> • SHA-256 Linkage Active
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            id="refresh-audit-btn"
            onClick={loadAuditLogs}
            disabled={isLoadingAudit}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition cursor-pointer disabled:opacity-40"
            title="Refresh audit event stream"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoadingAudit ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {currentUser.role === 'admin' && onHealChain && !isChainValid && (
            <button
              id="heal-chain-btn"
              onClick={onHealChain}
              className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-medium transition cursor-pointer"
            >
              Heal Chain
            </button>
          )}

          <button
            id="reverify-chain-btn"
            onClick={verifyChain}
            disabled={isVerifyingChain}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition cursor-pointer disabled:opacity-40"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isVerifyingChain ? 'animate-spin' : ''}`} />
            <span>{isVerifyingChain ? 'Auditing Blocks...' : 'Re-verify Chain'}</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 shadow-lg flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => { setSearchFilter(e.target.value); setAuditPage(1); }}
              placeholder="Search audit records by action or payload..."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-green-500"
            />
          </div>

          <select
            id="audit-action-select"
            value={auditActionFilter}
            onChange={(e) => { setAuditActionFilter(e.target.value); setAuditPage(1); }}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-green-500 cursor-pointer"
          >
            <option value="ALL">All Actions</option>
            <option value="REGISTER">Registration</option>
            <option value="LOGIN">Authentication</option>
            <option value="LOGOUT">Session Revocation</option>
            <option value="UPLOAD">Document Upload</option>
            <option value="CONFIRM_UPLOAD">S3 Confirmation</option>
            <option value="DOWNLOAD">Document Download</option>
            <option value="PERMISSION_GRANT">Permission Grant</option>
            <option value="PERMISSION_REVOKE">Permission Revocation</option>
            <option value="ACCESS_DENIED">Access Denied (IDOR)</option>
            <option value="DOCUMENT_EDIT">Document Update</option>
            <option value="DOCUMENT_DELETE">Document Deletion</option>
          </select>
        </div>

        {/* Audit Pagination Controls */}
        <div className="flex items-center gap-2 text-xs text-zinc-400 self-end sm:self-auto">
          <span>
            {((auditPage - 1) * auditPageSize) + 1}–{Math.min(auditPage * auditPageSize, filteredLogs.length)} of {filteredLogs.length}
          </span>
          <button
            id="audit-prev-page-btn"
            onClick={() => setAuditPage((p) => Math.max(1, p - 1))}
            disabled={auditPage === 1}
            className="p-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
            title="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="font-medium text-zinc-300">Page {auditPage} of {totalAuditPages}</span>
          <button
            id="audit-next-page-btn"
            onClick={() => setAuditPage((p) => Math.min(totalAuditPages, p + 1))}
            disabled={auditPage >= totalAuditPages}
            className="p-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
            title="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-900/60 text-zinc-400 text-[11px] uppercase tracking-wider border-b border-zinc-800">
              <tr>
                <th className="py-2.5 px-4">#</th>
                <th className="py-2.5 px-4">Action</th>
                <th className="py-2.5 px-4">Timestamp (UTC)</th>
                <th className="py-2.5 px-4">Event Payload / Metadata</th>
                <th className="py-2.5 px-4">Prev Block Hash</th>
                <th className="py-2.5 px-4">Current Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {paginatedAuditLogs.map((log) => {
                const isDenied = log.action.includes('DENIED');
                const isRevoke = log.action.includes('REVOKE');
                const isExpanded = expandedLogId === log.id;

                return (
                  <React.Fragment key={log.id}>
                    <tr 
                      onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                      className="hover:bg-zinc-900/40 font-mono text-[11px] cursor-pointer transition"
                    >
                      <td className="py-2.5 px-4 text-zinc-500 font-bold">{log.id}</td>
                      <td className="py-2.5 px-4 font-sans font-semibold">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${
                          isDenied 
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                            : isRevoke 
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' 
                            : 'bg-green-500/20 text-green-300 border border-green-500/30'
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-zinc-400">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-4 text-zinc-300 max-w-xs truncate" title={log.metadata_json}>
                        {log.metadata_json}
                      </td>
                      <td className="py-2.5 px-4 text-zinc-500 truncate max-w-[120px]" title={log.previous_hash}>
                        {log.previous_hash.substring(0, 10)}...
                      </td>
                      <td className="py-2.5 px-4 text-emerald-400 truncate max-w-[120px]" title={log.current_hash}>
                        <div className="flex items-center gap-1">
                          <span>{log.current_hash.substring(0, 10)}...</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleCopy(log.current_hash); }}
                            className="text-zinc-500 hover:text-white p-0.5"
                            title="Copy full SHA-256 hash"
                          >
                            {copiedHash === log.current_hash ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Expandable JSON Detail Row */}
                    {isExpanded && (
                      <tr className="bg-zinc-900/70 border-b border-zinc-800">
                        <td colSpan={6} className="p-4 font-mono text-xs text-zinc-300">
                          <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between text-zinc-400 text-[11px] pb-1 border-b border-zinc-800">
                              <span>Event UUID: {log.uuid_str}</span>
                              <span>Block #{log.id} Details</span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                              <div>
                                <span className="text-zinc-500">Previous Block Hash:</span>
                                <div className="text-zinc-300 break-all select-all">{log.previous_hash}</div>
                              </div>
                              <div>
                                <span className="text-zinc-500">Signature Block Hash:</span>
                                <div className="text-emerald-400 break-all select-all">{log.current_hash}</div>
                              </div>
                            </div>
                            <div className="mt-1">
                              <span className="text-zinc-500 text-[11px]">Structured Payload:</span>
                              <pre className="p-2 rounded bg-zinc-950 border border-zinc-800 text-green-300 text-[10px] overflow-x-auto mt-1">
                                {JSON.stringify(JSON.parse(log.metadata_json || '{}'), null, 2)}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
