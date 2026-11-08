import React, { useState } from 'react';
import { 
  FileText, Download, Trash2, Edit2, Eye, Upload, 
  Search, SlidersHorizontal, RotateCcw, ChevronLeft, ChevronRight,
  Shield, Check, X, Users, Lock, Grid, List, AlertTriangle
} from 'lucide-react';
import type { User, Document } from '../types';
import { formatBytes } from '../types';

interface VaultViewProps {
  currentUser: User;
  docs: Document[];
  isLoadingDocs: boolean;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  filterCategory: string;
  setFilterCategory: (c: string) => void;
  filterOwner: string;
  setFilterOwner: (o: string) => void;
  filterDateFrom: string;
  setFilterDateFrom: (d: string) => void;
  filterDateTo: string;
  setFilterDateTo: (d: string) => void;
  sortBy: string;
  setSortBy: (s: string) => void;
  showAdvancedFilters: boolean;
  setShowAdvancedFilters: React.Dispatch<React.SetStateAction<boolean>>;
  loadDocuments: () => void;
  resetFilters: () => void;
  // Pagination
  docPage: number;
  setDocPage: React.Dispatch<React.SetStateAction<number>>;
  docPageSize: number;
  setDocPageSize: (size: number) => void;
  // Upload State
  uploadTitle: string;
  setUploadTitle: (t: string) => void;
  uploadCategory: string;
  setUploadCategory: (c: string) => void;
  uploadFile: File | null;
  setUploadFile: (f: File | null) => void;
  isUploading: boolean;
  uploadProgress: number;
  handleUpload: (e: React.FormEvent) => void;
  resetUploadForm: () => void;
  duplicateWarning: string | null;
  onFileSelect: (file: File | null) => void;
  // Actions
  onPreview: (doc: Document) => void;
  onDownload: (docId: string, filename: string) => void;
  downloadingDocId: string | null;
  onEdit: (doc: Document) => void;
  onDelete: (doc: Document) => void;
  // Sharing
  grantingDocId: string | null;
  setGrantingDocId: (id: string | null) => void;
  grantEmail: string;
  setGrantEmail: (e: string) => void;
  grantCanEdit: boolean;
  setGrantCanEdit: (can: boolean) => void;
  isSavingGrant: boolean;
  handleSaveGrant: (e: React.FormEvent, docId: string) => void;
  handleRevokePermission: (docId: string, permId: string) => void;
  revokingPermId: string | null;
}

export const VaultView: React.FC<VaultViewProps> = ({
  currentUser,
  docs,
  isLoadingDocs,
  searchQuery,
  setSearchQuery,
  filterCategory,
  setFilterCategory,
  filterOwner,
  setFilterOwner,
  filterDateFrom,
  setFilterDateFrom,
  filterDateTo,
  setFilterDateTo,
  sortBy,
  setSortBy,
  showAdvancedFilters,
  setShowAdvancedFilters,
  loadDocuments,
  resetFilters,
  docPage,
  setDocPage,
  docPageSize,
  setDocPageSize,
  uploadTitle,
  setUploadTitle,
  uploadCategory,
  setUploadCategory,
  uploadFile,
  isUploading,
  uploadProgress,
  handleUpload,
  resetUploadForm,
  duplicateWarning,
  onFileSelect,
  onPreview,
  onDownload,
  downloadingDocId,
  onEdit,
  onDelete,
  grantingDocId,
  setGrantingDocId,
  grantEmail,
  setGrantEmail,
  grantCanEdit,
  setGrantCanEdit,
  isSavingGrant,
  handleSaveGrant,
  handleRevokePermission,
  revokingPermId
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [isDragging, setIsDragging] = useState(false);

  // Pagination calculation
  const totalDocPages = Math.max(1, Math.ceil(docs.length / docPageSize));
  const paginatedDocs = docs.slice((docPage - 1) * docPageSize, docPage * docPageSize);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-200">
      {/* Left 2 Cols: Document Explorer & Actions */}
      <div className="lg:col-span-2 flex flex-col gap-4">
        {/* Controls Bar: Search, Category, Sort, View Toggle */}
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 shadow-lg flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                id="search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents by title or filename..."
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-8 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-green-500 transition"
              />
              {searchQuery && (
                <button
                  id="clear-search-btn"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-2.5 text-zinc-500 hover:text-white cursor-pointer"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {/* Category Dropdown */}
            <select
              id="filter-category-select"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-green-500 cursor-pointer"
            >
              <option value="">All Categories</option>
              <option value="Legal">Legal</option>
              <option value="Finance">Finance</option>
              <option value="Technical">Technical</option>
              <option value="General">General</option>
            </select>

            {/* Sort Dropdown */}
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-green-500 cursor-pointer"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="title_asc">Title (A-Z)</option>
              <option value="title_desc">Title (Z-A)</option>
              <option value="size_desc">Size (Largest)</option>
              <option value="size_asc">Size (Smallest)</option>
            </select>

            {/* Actions: View Toggle, Filter Toggle, Refresh */}
            <div className="flex items-center gap-1.5 self-end sm:self-auto">
              <button
                id="view-toggle-grid-btn"
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg border transition cursor-pointer ${
                  viewMode === 'grid'
                    ? 'bg-green-600 text-white border-green-500'
                    : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-white'
                }`}
                title="Grid Cards View"
              >
                <Grid className="h-3.5 w-3.5" />
              </button>

              <button
                id="view-toggle-table-btn"
                onClick={() => setViewMode('table')}
                className={`p-2 rounded-lg border transition cursor-pointer ${
                  viewMode === 'table'
                    ? 'bg-green-600 text-white border-green-500'
                    : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-white'
                }`}
                title="Compact Table View"
              >
                <List className="h-3.5 w-3.5" />
              </button>

              <button
                id="toggle-advanced-filters-btn"
                onClick={() => setShowAdvancedFilters(prev => !prev)}
                className={`p-2 rounded-lg border transition cursor-pointer ${
                  showAdvancedFilters
                    ? 'bg-zinc-800 text-green-400 border-green-500/40'
                    : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-white'
                }`}
                title="Toggle Advanced Filters"
              >
                <SlidersHorizontal className="h-3.5 w-3.5" />
              </button>

              <button
                id="refresh-docs-btn"
                onClick={loadDocuments}
                className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
                title="Refresh Vault Documents"
              >
                <RotateCcw className={`h-3.5 w-3.5 ${isLoadingDocs ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Advanced Filter Drawer */}
          {showAdvancedFilters && (
            <div className="pt-3 border-t border-zinc-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3 animate-in fade-in">
              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Owner Email / Name</label>
                <input
                  id="filter-owner-input"
                  type="text"
                  value={filterOwner}
                  onChange={(e) => setFilterOwner(e.target.value)}
                  placeholder="Filter by owner..."
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-green-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Created After</label>
                <input
                  id="filter-date-from-input"
                  type="date"
                  value={filterDateFrom}
                  onChange={(e) => setFilterDateFrom(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-green-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-zinc-400 mb-1">Created Before</label>
                <input
                  id="filter-date-to-input"
                  type="date"
                  value={filterDateTo}
                  onChange={(e) => setFilterDateTo(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-green-500"
                />
              </div>

              <div className="sm:col-span-3 flex justify-end">
                <button
                  id="clear-all-filters-btn"
                  onClick={resetFilters}
                  className="text-xs text-zinc-400 hover:text-white transition cursor-pointer"
                >
                  Clear all filters
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Document Results Count */}
        <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
          <span>{docs.length} document{docs.length === 1 ? '' : 's'} available</span>
          {isLoadingDocs && <span className="text-green-400 animate-pulse font-mono">Syncing...</span>}
        </div>

        {/* Empty State */}
        {docs.length === 0 && !isLoadingDocs && (
          <div className="p-12 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/40 flex flex-col items-center justify-center gap-3">
            <div className="h-12 w-12 rounded-full bg-zinc-900 flex items-center justify-center text-zinc-500">
              <FileText className="h-6 w-6" />
            </div>
            <div className="text-sm font-semibold text-white">No documents found</div>
            <p className="text-xs text-zinc-400 max-w-sm">
              No files match your filter criteria, or the vault is currently empty.
            </p>
            <button
              id="reset-empty-search-btn"
              onClick={resetFilters}
              className="mt-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 transition cursor-pointer"
            >
              Reset search & filters
            </button>
          </div>
        )}

        {/* GRID VIEW */}
        {viewMode === 'grid' && docs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {paginatedDocs.map((doc) => {
              const isOwner = doc.owner_id === currentUser.id;
              const canEdit = isOwner || (currentUser.role === 'admin') || doc.permissions?.some(p => p.grantee_id === currentUser.id && p.can_edit && p.is_active);
              const isShared = doc.permissions && doc.permissions.length > 0;

              return (
                <div
                  key={doc.id}
                  className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/80 hover:border-zinc-700 transition flex flex-col justify-between gap-4 shadow-lg"
                >
                  <div className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <div className="h-8 w-8 rounded-lg bg-green-950/40 border border-green-500/20 flex items-center justify-center text-green-400 shrink-0">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div className="overflow-hidden">
                          <h3 className="text-sm font-semibold text-white truncate" title={doc.title}>
                            {doc.title}
                          </h3>
                          <div className="text-[11px] text-zinc-500 font-mono truncate" title={doc.original_filename}>
                            {doc.original_filename}
                          </div>
                        </div>
                      </div>

                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-900 border border-zinc-800 text-zinc-300 shrink-0">
                        {doc.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-zinc-400 font-mono">
                      <span>{formatBytes(doc.file_size)}</span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>

                    <div className="flex items-center gap-2 pt-1 border-t border-zinc-900 text-[11px]">
                      <span className="text-zinc-500">Access:</span>
                      {isOwner ? (
                        <span className="text-green-400 font-medium">Owner</span>
                      ) : (
                        <span className="text-blue-400 font-medium">Shared with you</span>
                      )}
                      {isShared && (
                        <span className="text-zinc-500 ml-auto font-mono text-[10px]">
                          {doc.permissions.length} active grant{doc.permissions.length === 1 ? '' : 's'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions & Sharing */}
                  <div className="flex flex-col gap-2 pt-2 border-t border-zinc-900">
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1">
                        <button
                          id={`preview-doc-btn-${doc.id}`}
                          onClick={() => onPreview(doc)}
                          className="px-2.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white text-xs font-medium border border-zinc-800 transition cursor-pointer flex items-center gap-1.5"
                          title="Preview document in browser"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>Preview</span>
                        </button>

                        <button
                          id={`download-doc-btn-${doc.id}`}
                          onClick={() => onDownload(doc.id, doc.original_filename)}
                          disabled={downloadingDocId === doc.id}
                          className="px-2.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white text-xs font-medium border border-zinc-800 transition cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
                          title="Download document safely"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>Download</span>
                        </button>
                      </div>

                      <div className="flex items-center gap-1">
                        {canEdit && (
                          <button
                            id={`edit-doc-btn-${doc.id}`}
                            onClick={() => onEdit(doc)}
                            className="p-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 transition cursor-pointer"
                            title="Edit metadata"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </button>
                        )}

                        {(isOwner || currentUser.role === 'admin') && (
                          <button
                            id={`delete-doc-btn-${doc.id}`}
                            onClick={() => onDelete(doc)}
                            className="p-1.5 rounded-lg bg-zinc-900 hover:bg-red-950/40 text-zinc-400 hover:text-red-400 border border-zinc-800 hover:border-red-500/30 transition cursor-pointer"
                            title="Delete document"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Sharing Section */}
                    {(isOwner || currentUser.role === 'admin') && (
                      <div className="pt-2 border-t border-zinc-900/60">
                        {grantingDocId === doc.id ? (
                          <form onSubmit={(e) => handleSaveGrant(e, doc.id)} className="flex flex-col gap-2 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800">
                            <span className="text-[11px] font-semibold text-zinc-300">Grant Document Access</span>
                            <input
                              id="grantee-email-input"
                              type="email"
                              value={grantEmail}
                              onChange={(e) => setGrantEmail(e.target.value)}
                              placeholder="grantee@trustvault.io"
                              className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-green-500"
                              required
                            />
                            <div className="flex items-center justify-between">
                              <label className="flex items-center gap-1.5 text-xs text-zinc-400 cursor-pointer">
                                <input
                                  id="grant-can-edit-checkbox"
                                  type="checkbox"
                                  checked={grantCanEdit}
                                  onChange={(e) => setGrantCanEdit(e.target.checked)}
                                  className="rounded border-zinc-800 text-green-600 focus:ring-0 cursor-pointer"
                                />
                                <span>Allow Editing</span>
                              </label>

                              <div className="flex items-center gap-1.5">
                                <button
                                  id="cancel-grant-btn"
                                  type="button"
                                  onClick={() => setGrantingDocId(null)}
                                  className="px-2 py-0.5 rounded text-xs text-zinc-400 hover:text-white transition cursor-pointer"
                                >
                                  Cancel
                                </button>
                                <button
                                  id="save-grant-btn"
                                  type="submit"
                                  disabled={isSavingGrant}
                                  className="px-2.5 py-0.5 rounded bg-green-600 hover:bg-green-500 text-white text-xs font-medium transition cursor-pointer"
                                >
                                  {isSavingGrant ? 'Saving...' : 'Grant'}
                                </button>
                              </div>
                            </div>
                          </form>
                        ) : (
                          <div className="flex items-center justify-between">
                            <button
                              id={`open-grant-btn-${doc.id}`}
                              onClick={() => { setGrantingDocId(doc.id); setGrantEmail('viewer@trustvault.io'); setGrantCanEdit(false); }}
                              className="text-xs text-green-400 hover:text-green-300 font-medium transition cursor-pointer flex items-center gap-1"
                            >
                              <Users className="h-3 w-3" />
                              <span>+ Grant Access</span>
                            </button>

                            {doc.permissions && doc.permissions.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {doc.permissions.map((p) => (
                                  <span key={p.id} className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
                                    {p.grantee_username || p.grantee_email}
                                    <button
                                      id={`revoke-perm-btn-${p.id}`}
                                      onClick={() => handleRevokePermission(doc.id, p.id)}
                                      disabled={revokingPermId === p.id}
                                      className="text-zinc-500 hover:text-red-400 cursor-pointer"
                                      title="Revoke access"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* TABLE VIEW */}
        {viewMode === 'table' && docs.length > 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-900/40 text-zinc-400 text-[11px] uppercase tracking-wider border-b border-zinc-800">
                  <tr>
                    <th className="py-2.5 px-4">Document Title</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4">Size</th>
                    <th className="py-2.5 px-4">Created Date</th>
                    <th className="py-2.5 px-4">Access Level</th>
                    <th className="py-2.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                  {paginatedDocs.map((doc) => {
                    const isOwner = doc.owner_id === currentUser.id;
                    const canEdit = isOwner || (currentUser.role === 'admin') || doc.permissions?.some(p => p.grantee_id === currentUser.id && p.can_edit && p.is_active);

                    return (
                      <tr key={doc.id} className="hover:bg-zinc-900/30 transition">
                        <td className="py-2.5 px-4">
                          <div className="font-semibold text-white max-w-[220px] truncate" title={doc.title}>
                            {doc.title}
                          </div>
                          <div className="text-[10px] text-zinc-500 font-mono truncate max-w-[220px]">
                            {doc.original_filename}
                          </div>
                        </td>
                        <td className="py-2.5 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-900 border border-zinc-800 text-zinc-300">
                            {doc.category}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 font-mono text-zinc-400">
                          {formatBytes(doc.file_size)}
                        </td>
                        <td className="py-2.5 px-4 font-mono text-zinc-400">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-2.5 px-4">
                          {isOwner ? (
                            <span className="text-green-400 font-medium">Owner</span>
                          ) : (
                            <span className="text-blue-400 font-medium">Shared</span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              id={`table-preview-${doc.id}`}
                              onClick={() => onPreview(doc)}
                              className="p-1 rounded bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white transition cursor-pointer"
                              title="Preview"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                            <button
                              id={`table-download-${doc.id}`}
                              onClick={() => onDownload(doc.id, doc.original_filename)}
                              disabled={downloadingDocId === doc.id}
                              className="p-1 rounded bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white transition cursor-pointer disabled:opacity-40"
                              title="Download"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </button>
                            {canEdit && (
                              <button
                                id={`table-edit-${doc.id}`}
                                onClick={() => onEdit(doc)}
                                className="p-1 rounded bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 hover:text-white transition cursor-pointer"
                                title="Edit"
                              >
                                <Edit2 className="h-3.5 w-3.5" />
                              </button>
                            )}
                            {(isOwner || currentUser.role === 'admin') && (
                              <button
                                id={`table-delete-${doc.id}`}
                                onClick={() => onDelete(doc)}
                                className="p-1 rounded bg-zinc-800/80 hover:bg-red-950/60 text-zinc-300 hover:text-red-400 transition cursor-pointer"
                                title="Delete"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Pagination Controls */}
        {docs.length > docPageSize && (
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 px-1 text-xs text-zinc-400">
            <div>
              Showing {((docPage - 1) * docPageSize) + 1} to {Math.min(docPage * docPageSize, docs.length)} of {docs.length} documents
            </div>
            <div className="flex items-center gap-2">
              <select
                id="doc-page-size-select"
                value={docPageSize}
                onChange={(e) => { setDocPageSize(Number(e.target.value)); setDocPage(1); }}
                className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-300 focus:outline-none"
              >
                <option value={6}>6 per page</option>
                <option value={12}>12 per page</option>
                <option value={24}>24 per page</option>
              </select>

              <button
                id="doc-prev-page-btn"
                onClick={() => setDocPage((p) => Math.max(1, p - 1))}
                disabled={docPage === 1}
                className="p-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
                title="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <span className="font-medium text-zinc-300 px-1">
                Page {docPage} of {totalDocPages}
              </span>

              <button
                id="doc-next-page-btn"
                onClick={() => setDocPage((p) => Math.min(totalDocPages, p + 1))}
                disabled={docPage >= totalDocPages}
                className="p-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
                title="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Right Col: Drag-and-Drop Upload & Security Highlights */}
      <div className="flex flex-col gap-4">
        {(currentUser.role === 'admin' || currentUser.role === 'owner') ? (
          <form onSubmit={handleUpload} className="p-5 rounded-xl border border-zinc-800 bg-zinc-950/60 flex flex-col gap-3 shadow-xl">
            <div className="flex items-center justify-between font-semibold text-sm text-white">
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4 text-green-400" />
                <span>Upload to Vault</span>
              </div>
              <button
                type="button"
                id="reset-upload-btn"
                onClick={resetUploadForm}
                className="text-[11px] text-zinc-500 hover:text-zinc-300 transition cursor-pointer"
                title="Reset upload form"
              >
                Reset
              </button>
            </div>

            <p className="text-xs text-zinc-400">
              Files undergo strict magic-byte inspection. 10MB limit strictly enforced via direct S3 presigned upload.
            </p>

            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`p-4 border-2 border-dashed rounded-xl transition flex flex-col items-center justify-center text-center cursor-pointer ${
                isDragging
                  ? 'border-green-500 bg-green-950/20 shadow-lg shadow-green-900/20'
                  : 'border-zinc-800 hover:border-zinc-700 bg-zinc-900/20'
              }`}
              onClick={() => document.getElementById('upload-file-input')?.click()}
            >
              <Upload className={`h-6 w-6 mb-2 ${isDragging ? 'text-green-400 animate-bounce' : 'text-zinc-500'}`} />
              <div className="text-xs font-medium text-zinc-300">
                {uploadFile ? uploadFile.name : 'Drag & drop file here or click to browse'}
              </div>
              <div className="text-[10px] text-zinc-500 font-mono mt-1">
                {uploadFile ? `${formatBytes(uploadFile.size)} • ${uploadFile.type || 'unknown type'}` : 'PDF, DOCX, PNG, JPG, JSON, TXT up to 10MB'}
              </div>

              <input
                id="upload-file-input"
                type="file"
                onChange={(e) => onFileSelect(e.target.files ? e.target.files[0] : null)}
                className="hidden"
              />
            </div>

            {/* Duplicate Warning Alert */}
            {duplicateWarning && (
              <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <div className="text-[11px] leading-tight">
                  <span className="font-semibold">Duplicate Alert:</span> {duplicateWarning}
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Document Title</label>
              <input
                id="upload-title-input"
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="e.g. Master Services Agreement"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-green-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Category</label>
              <select
                id="upload-category-select"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-green-500 cursor-pointer"
              >
                <option value="Legal">Legal & Contracts</option>
                <option value="Finance">Finance & Payroll</option>
                <option value="Technical">Technical Specifications</option>
                <option value="General">General Documents</option>
              </select>
            </div>

            {/* Simulated Progress Bar */}
            {isUploading && (
              <div className="flex flex-col gap-1 pt-1">
                <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono">
                  <span>Uploading to S3...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-lime-500 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              id="commit-upload-btn"
              type="submit"
              disabled={isUploading || !uploadFile}
              className="mt-2 w-full py-2.5 rounded-lg bg-gradient-to-r from-green-600 to-lime-600 hover:from-green-500 hover:to-lime-500 text-white font-medium text-xs transition disabled:opacity-40 shadow-lg shadow-green-900/30 cursor-pointer"
            >
              {isUploading ? 'Encrypting & Uploading...' : 'Commit Document to Vault'}
            </button>
          </form>
        ) : (
          <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-950/60 text-center flex flex-col items-center gap-3">
            <Lock className="h-8 w-8 text-zinc-500" />
            <h3 className="text-sm font-semibold text-white">Read-Only Viewer Account</h3>
            <p className="text-xs text-zinc-400">
              Your role is restricted to viewing and downloading documents shared with you.
            </p>
          </div>
        )}

        {/* Security Guarantees Callout */}
        <div className="p-5 rounded-xl border border-zinc-800/80 bg-zinc-950/40 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-white">
            <Shield className="h-4 w-4 text-emerald-400" />
            <span>Cryptographic Guarantees</span>
          </div>
          <ul className="text-[11px] text-zinc-400 flex flex-col gap-2">
            <li className="flex items-start gap-2">
              <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>Direct S3 presigned upload with SHA-256 fingerprinting</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>Instant permission revocation with 0ms authorization cut-off</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>Advisory-locked sequential audit commits preventing race conditions</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
