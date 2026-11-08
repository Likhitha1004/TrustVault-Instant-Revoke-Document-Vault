import React, { useState, useEffect, useCallback } from 'react';
import { 
  Shield, Lock, RefreshCw, AlertTriangle, 
  ArrowLeft, X, CheckCircle2
} from 'lucide-react';
import type { User, Document, AuditLog, SystemMetrics } from './types';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { VaultView } from './components/VaultView';
import { AuditView } from './components/AuditView';
import { SettingsView } from './components/SettingsView';
import { PreviewModal } from './components/PreviewModal';
import { EditModal, DeleteModal, ProfileModal } from './components/Modals';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('tv_token'));
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // Auth State
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [loginId, setLoginId] = useState('admin@trustvault.io');
  const [password, setPassword] = useState('AdminPass2026!');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regRole, setRegRole] = useState<'admin' | 'owner' | 'viewer'>('viewer');
  const [isSubmittingAuth, setIsSubmittingAuth] = useState(false);

  // Navigation & Layout
  const [activeTab, setActiveTab] = useState<'dashboard' | 'vault' | 'audit' | 'settings'>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Vault State
  const [docs, setDocs] = useState<Document[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [chainStatus, setChainStatus] = useState<any>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);
  const [isVerifyingChain, setIsVerifyingChain] = useState(false);

  // Toast Notifications
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterOwner, setFilterOwner] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Document Pagination State
  const [docPage, setDocPage] = useState(1);
  const [docPageSize, setDocPageSize] = useState(6);

  // Audit Filter & Pagination State
  const [auditActionFilter, setAuditActionFilter] = useState('ALL');
  const [auditPage, setAuditPage] = useState(1);
  const auditPageSize = 10;

  // Upload Form State
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('Legal');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);

  // Modal States
  const [editingDoc, setEditingDoc] = useState<Document | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const [deletingDoc, setDeletingDoc] = useState<Document | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [showProfileModal, setShowProfileModal] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  // Preview Modal State
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // In-line Grant Permission State
  const [grantEmail, setGrantEmail] = useState('');
  const [grantCanEdit, setGrantCanEdit] = useState(false);
  const [grantingDocId, setGrantingDocId] = useState<string | null>(null);
  const [isSavingGrant, setIsSavingGrant] = useState(false);
  const [revokingPermId, setRevokingPermId] = useState<string | null>(null);
  const [downloadingDocId, setDownloadingDocId] = useState<string | null>(null);

  // --- API Callbacks ---

  const logout = useCallback(async () => {
    const activeToken = token || localStorage.getItem('tv_token');
    if (activeToken) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${activeToken}` }
        });
      } catch {
        // Network errors on logout tolerated
      }
    }
    localStorage.removeItem('tv_token');
    setToken(null);
    setCurrentUser(null);
    setDocs([]);
    setAuditLogs([]);
    setMetrics(null);
    setActiveTab('dashboard');
    setSuccessMsg('');
    setErrorMsg('');
    setShowProfileModal(false);
    setEditingDoc(null);
    setDeletingDoc(null);
    setPreviewDoc(null);
    setMobileMenuOpen(false);
  }, [token]);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      if (!activeToken) return;
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (res.ok) {
        const user = await res.json();
        setCurrentUser(user);
      } else {
        logout();
      }
    } catch {
      logout();
    }
  }, [token, logout]);

  const loadDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (filterCategory) params.append('category', filterCategory);
      if (filterOwner.trim()) params.append('owner', filterOwner.trim());
      if (filterDateFrom) params.append('date_from', filterDateFrom);
      if (filterDateTo) params.append('date_to', filterDateTo);
      if (sortBy) params.append('sort_by', sortBy);

      const url = params.toString() 
        ? `${API_BASE}/documents?${params.toString()}`
        : `${API_BASE}/documents`;

      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingDocs(false);
    }
  }, [token, searchQuery, filterCategory, filterOwner, filterDateFrom, filterDateTo, sortBy]);

  const loadAuditLogs = useCallback(async () => {
    setIsLoadingAudit(true);
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      let url = `${API_BASE}/audit?limit=200`;
      if (auditActionFilter !== 'ALL') {
        url += `&action=${encodeURIComponent(auditActionFilter)}`;
      }
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingAudit(false);
    }
  }, [token, auditActionFilter]);

  const verifyChain = useCallback(async () => {
    setIsVerifyingChain(true);
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/audit/verify`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setChainStatus(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsVerifyingChain(false);
    }
  }, [token]);

  const loadMetrics = useCallback(async () => {
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/audit/metrics`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  // Initial token load
  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token, fetchCurrentUser]);

  // Document & metrics re-fetch trigger
  useEffect(() => {
    if (currentUser) {
      loadDocuments();
      if (currentUser.role === 'admin') {
        loadAuditLogs();
        verifyChain();
        loadMetrics();
      }
    }
  }, [currentUser, loadDocuments, loadAuditLogs, verifyChain, loadMetrics]);

  // Keyboard accessibility: Escape key closes active modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (previewDoc) setPreviewDoc(null);
        if (editingDoc) setEditingDoc(null);
        if (deletingDoc) setDeletingDoc(null);
        if (showProfileModal) setShowProfileModal(false);
        if (grantingDocId) setGrantingDocId(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [previewDoc, editingDoc, deletingDoc, showProfileModal, grantingDocId]);

  // Auth Handlers
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmittingAuth) return;
    setErrorMsg('');
    setIsSubmittingAuth(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: loginId.trim(), password })
      });
      const text = await res.text();
      let data: any = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        throw new Error(`Server returned non-JSON response (${res.status}): ${text.substring(0, 100)}`);
      }
      if (!res.ok) {
        throw new Error(data.detail || `Login failed (${res.status})`);
      }
      localStorage.setItem('tv_token', data.access_token);
      setToken(data.access_token);
      setCurrentUser(data.user);
      setSuccessMsg(`Authenticated as ${data.user.role.toUpperCase()}: ${data.user.username}`);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmittingAuth(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmittingAuth) return;
    if (!regUsername.trim() || !regEmail.trim() || !regPassword) {
      setErrorMsg('All fields are required for registration.');
      return;
    }
    setErrorMsg('');
    setIsSubmittingAuth(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: regUsername.trim(),
          email: regEmail.trim(),
          password: regPassword,
          role: regRole
        })
      });
      const text = await res.text();
      let data: any = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        throw new Error(`Server returned non-JSON response (${res.status})`);
      }
      if (!res.ok) {
        throw new Error(data.detail || `Registration failed (${res.status})`);
      }
      setSuccessMsg(`Account created for ${data.username}! You can now sign in.`);
      setAuthMode('login');
      setLoginId(data.email);
      setPassword(regPassword);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmittingAuth(false);
    }
  };

  // Pre-flight file validation and duplicate detection
  const handleFileSelect = async (file: File | null) => {
    setUploadFile(file);
    setDuplicateWarning(null);
    if (!file) return;

    // Check size limit: 10MB
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg(`File exceeds 10MB limit (${(file.size / (1024 * 1024)).toFixed(2)}MB). Direct S3 uploads strictly enforce a 10MB ceiling.`);
      return;
    }

    if (!uploadTitle) {
      setUploadTitle(file.name.replace(/\.[^/.]+$/, ''));
    }

    // In-browser SHA-256 calculation for duplicate detection
    try {
      const buffer = await file.slice(0, 1024 * 1024 * 2).arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const sha256Prefix = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      const existingMatch = docs.find(d => d.file_hash_sha256.startsWith(sha256Prefix) || d.original_filename === file.name);
      if (existingMatch) {
        setDuplicateWarning(`A document named '${existingMatch.title}' (${existingMatch.original_filename}) already exists in your vault.`);
      }
    } catch {
      // Non-blocking crypto hash check
    }
  };

  // Upload handler with direct S3 support
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isUploading) return;
    if (!uploadFile) {
      setErrorMsg('Please select a file to upload.');
      return;
    }

    if (uploadFile.size > 10 * 1024 * 1024) {
      setErrorMsg('Upload rejected: File size exceeds the mandatory 10MB maximum limit.');
      return;
    }

    setErrorMsg('');
    setIsUploading(true);
    setUploadProgress(15);

    try {
      const activeToken = token || localStorage.getItem('tv_token');
      let data;

      if (uploadFile.size > 4 * 1024 * 1024) {
        // Direct Presigned S3 Upload to bypass Vercel 4.5MB Serverless payload limit
        setUploadProgress(30);
        const buffer = await uploadFile.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const sha256 = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        setUploadProgress(50);
        const intentRes = await fetch(`${API_BASE}/documents/upload-intent`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${activeToken}`
          },
          body: JSON.stringify({
            title: uploadTitle || uploadFile.name,
            category: uploadCategory,
            filename: uploadFile.name,
            file_size: uploadFile.size,
            file_hash_sha256: sha256,
            mime_type: uploadFile.type || 'application/octet-stream'
          })
        });
        const intentData = await intentRes.json();
        if (!intentRes.ok) throw new Error(intentData.detail || 'Upload authorization failed');

        setUploadProgress(75);
        const putRes = await fetch(intentData.upload_url, {
          method: 'PUT',
          headers: {
            'Content-Type': uploadFile.type || 'application/octet-stream'
          },
          body: uploadFile
        });
        if (!putRes.ok) throw new Error(`Direct storage upload failed with status ${putRes.status}`);

        setUploadProgress(90);
        const confirmRes = await fetch(`${API_BASE}/documents/confirm-upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${activeToken}`
          },
          body: JSON.stringify({
            title: uploadTitle || uploadFile.name,
            category: uploadCategory,
            original_filename: uploadFile.name,
            storage_path: intentData.storage_path,
            upload_token: intentData.upload_token,
            file_size: uploadFile.size,
            file_hash_sha256: sha256,
            mime_type: uploadFile.type || 'application/octet-stream'
          })
        });
        data = await confirmRes.json();
        if (!confirmRes.ok) throw new Error(data.detail || 'Upload confirmation failed');
      } else {
        const formData = new FormData();
        formData.append('title', uploadTitle);
        formData.append('category', uploadCategory);
        formData.append('file', uploadFile);

        setUploadProgress(60);
        const res = await fetch(`${API_BASE}/documents/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${activeToken}` },
          body: formData
        });
        data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Upload failed');
        }
      }

      setUploadProgress(100);
      setSuccessMsg(`Document '${data.title}' safely committed to vault.`);
      setUploadTitle('');
      setUploadFile(null);
      setDuplicateWarning(null);
      const fileInput = document.getElementById('upload-file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      await loadDocuments();
      if (currentUser?.role === 'admin') {
        loadMetrics();
        loadAuditLogs();
        verifyChain();
      }
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const resetUploadForm = () => {
    setUploadTitle('');
    setUploadCategory('Legal');
    setUploadFile(null);
    setDuplicateWarning(null);
    const fileInput = document.getElementById('upload-file-input') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  // Download Handler
  const handleDownload = async (docId: string, filename: string) => {
    if (downloadingDocId) return;
    setDownloadingDocId(docId);
    setErrorMsg('');
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${docId}/download`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSuccessMsg(`Downloaded '${filename}' successfully.`);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setDownloadingDocId(null);
    }
  };

  // Document Preview Handler
  const handlePreview = async (doc: Document) => {
    setPreviewDoc(doc);
    setPreviewContent(null);
    setPreviewImageUrl(null);
    setIsLoadingPreview(true);

    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${doc.id}/download`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (!res.ok) {
        throw new Error(`Failed to load document stream (${res.status})`);
      }
      const blob = await res.blob();
      if (doc.mime_type.startsWith('image/')) {
        const url = URL.createObjectURL(blob);
        setPreviewImageUrl(url);
      } else if (
        doc.mime_type.startsWith('text/') || 
        doc.mime_type === 'application/json' ||
        doc.original_filename.match(/\\.(txt|json|md|csv|py|js|ts|html|css|yaml|yml)$/i)
      ) {
        const text = await blob.text();
        setPreviewContent(text.slice(0, 100000));
      }
    } catch (err: any) {
      console.warn('Preview fallback to metadata:', err.message);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  // Close Preview & cleanup blob URL
  const handleClosePreview = () => {
    if (previewImageUrl) {
      URL.revokeObjectURL(previewImageUrl);
    }
    setPreviewDoc(null);
    setPreviewContent(null);
    setPreviewImageUrl(null);
  };

  // Document Edit
  const handleUpdateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDoc || isSavingEdit) return;
    setIsSavingEdit(true);

    const prevDoc = editingDoc;
    const optimisticUpdatedDoc = { ...prevDoc, title: editTitle, category: editCategory, updated_at: new Date().toISOString() };

    // Optimistic UI update: update local list and close dialog immediately
    setDocs((prev: Document[]) => prev.map((d: Document) => d.id === prevDoc.id ? optimisticUpdatedDoc : d));
    setEditingDoc(null);
    setSuccessMsg(`Document '${editTitle}' metadata updated.`);

    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${prevDoc.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${activeToken}`
        },
        body: JSON.stringify({ title: editTitle, category: editCategory })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Update failed');
      // Sync authoritative state silently
      setDocs((prev: Document[]) => prev.map((d: Document) => d.id === data.id ? data : d));
    } catch (err: any) {
      // Rollback on failure
      setDocs((prev: Document[]) => prev.map((d: Document) => d.id === prevDoc.id ? prevDoc : d));
      setErrorMsg(err.message);
    } finally {
      setIsSavingEdit(false);
    }
  };

  // Document Delete
  const handleDeleteDocument = async () => {
    if (!deletingDoc || isDeleting) return;
    setIsDeleting(true);

    const targetDoc = deletingDoc;
    // Optimistic UI update: instantly remove from list and close modal
    setDocs((prev: Document[]) => prev.filter((d: Document) => d.id !== targetDoc.id));
    setDeletingDoc(null);
    setSuccessMsg(`Document '${targetDoc.title}' permanently expunged.`);

    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${targetDoc.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Delete failed');

      if (currentUser?.role === 'admin') {
        loadMetrics();
        loadAuditLogs();
        verifyChain();
      }
    } catch (err: any) {
      // Rollback on failure
      setDocs((prev: Document[]) => [targetDoc, ...prev]);
      setErrorMsg(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  // Sharing Grants
  const handleSaveGrant = async (e: React.FormEvent, docId: string) => {
    e.preventDefault();
    if (isSavingGrant) return;
    setIsSavingGrant(true);
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${docId}/permissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${activeToken}`
        },
        body: JSON.stringify({
          grantee_email: grantEmail.trim(),
          can_read: true,
          can_edit: grantCanEdit
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Grant failed');
      setSuccessMsg(`Granted access to ${grantEmail}.`);
      setGrantingDocId(null);
      setGrantEmail('');
      await loadDocuments();
      if (currentUser?.role === 'admin') loadMetrics();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsSavingGrant(false);
    }
  };

  const handleRevokePermission = async (docId: string, permId: string) => {
    if (revokingPermId) return;
    setRevokingPermId(permId);
    try {
      const activeToken = token || localStorage.getItem('tv_token');
      const res = await fetch(`${API_BASE}/documents/${docId}/permissions/${permId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Revoke failed');
      setSuccessMsg('Permission instantly revoked (0ms window).');
      await loadDocuments();
      if (currentUser?.role === 'admin') loadMetrics();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setRevokingPermId(null);
    }
  };

  const resetFilters = () => {
    setSearchQuery('');
    setFilterCategory('');
    setFilterOwner('');
    setFilterDateFrom('');
    setFilterDateTo('');
    setSortBy('newest');
    setDocPage(1);
  };

  return (
    <div className="min-h-screen bg-[#050505] text-zinc-100 flex flex-col font-sans selection:bg-green-500/30 selection:text-white">
      {/* Sticky Header */}
      <Header
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
        setShowProfileModal={setShowProfileModal}
        logout={logout}
        setAuthMode={setAuthMode}
        setLoginId={setLoginId}
        setPassword={setPassword}
      />

      {/* Main App Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        {/* Toast Error Banner */}
        {errorMsg && (
          <div id="error-toast-banner" className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 text-xs flex items-center justify-between shadow-lg animate-in fade-in" role="alert">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              id="dismiss-error-btn"
              onClick={() => setErrorMsg('')}
              className="text-red-400 hover:text-white p-1 rounded transition cursor-pointer"
              title="Dismiss error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Toast Success Banner */}
        {successMsg && (
          <div id="success-toast-banner" className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 text-xs flex items-center justify-between shadow-lg animate-in fade-in" role="status">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
            <button
              id="dismiss-success-btn"
              onClick={() => setSuccessMsg('')}
              className="text-emerald-400 hover:text-white p-1 rounded transition cursor-pointer"
              title="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* AUTHENTICATION VIEW */}
        {!currentUser && (
          <div className="max-w-md w-full mx-auto my-auto py-8">
            <div className="p-8 rounded-2xl border border-zinc-800 bg-zinc-950/80 shadow-2xl backdrop-blur flex flex-col gap-6">
              <div className="flex flex-col items-center text-center gap-2">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-green-600 to-lime-700 flex items-center justify-center shadow-xl shadow-green-900/40">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-white mt-1">TrustVault Security Portal</h2>
                <p className="text-xs text-zinc-400">
                  Zero-trust document storage backed by cryptographic audit proofs.
                </p>
              </div>

              {/* Tabs: Sign In / Register */}
              <div className="grid grid-cols-2 p-1 bg-zinc-900 rounded-xl border border-zinc-800">
                <button
                  id="tab-login-btn"
                  onClick={() => setAuthMode('login')}
                  className={`py-2 text-xs font-semibold rounded-lg transition cursor-pointer ${
                    authMode === 'login' ? 'bg-green-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  id="tab-register-btn"
                  onClick={() => setAuthMode('register')}
                  className={`py-2 text-xs font-semibold rounded-lg transition cursor-pointer ${
                    authMode === 'register' ? 'bg-green-600 text-white shadow' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  Register
                </button>
              </div>

              {authMode === 'login' ? (
                <form onSubmit={handleLogin} className="flex flex-col gap-4">
                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Username or Email</label>
                    <input
                      id="login-id-input"
                      type="text"
                      value={loginId}
                      onChange={(e) => setLoginId(e.target.value)}
                      placeholder="admin@trustvault.io"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-green-500 transition"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Password</label>
                    <input
                      id="login-password-input"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-green-500 transition"
                      required
                    />
                  </div>

                  <button
                    id="login-submit-btn"
                    type="submit"
                    disabled={isSubmittingAuth}
                    className="w-full py-2.5 rounded-lg bg-gradient-to-r from-green-600 to-lime-600 hover:from-green-500 hover:to-lime-500 text-white font-medium text-xs shadow-lg shadow-green-900/30 transition disabled:opacity-40 cursor-pointer flex items-center justify-center gap-2"
                  >
                    {isSubmittingAuth ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <>
                        <Lock className="h-3.5 w-3.5" />
                        <span>Sign In to TrustVault</span>
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleRegister} className="flex flex-col gap-4">
                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Username</label>
                    <input
                      id="reg-username-input"
                      type="text"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="alice"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-green-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Email Address</label>
                    <input
                      id="reg-email-input"
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="alice@trustvault.io"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-green-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Password</label>
                    <input
                      id="reg-password-input"
                      type="password"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Minimum 8 characters"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-green-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-400 mb-1">Role Assignment</label>
                    <select
                      id="reg-role-select"
                      value={regRole}
                      onChange={(e: any) => setRegRole(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500 cursor-pointer"
                    >
                      <option value="viewer">Viewer (Read-only)</option>
                      <option value="owner">Owner (Upload & Manage Documents)</option>
                      <option value="admin">Admin (Full System & Audit Access)</option>
                    </select>
                  </div>

                  <button
                    id="reg-submit-btn"
                    type="submit"
                    disabled={isSubmittingAuth}
                    className="w-full py-2.5 rounded-lg bg-gradient-to-r from-green-600 to-lime-600 hover:from-green-500 hover:to-lime-500 text-white font-medium text-xs shadow-lg shadow-green-900/30 transition disabled:opacity-40 cursor-pointer flex items-center justify-center gap-2"
                  >
                    {isSubmittingAuth ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        <span>Creating Account...</span>
                      </>
                    ) : (
                      <span>Create Account</span>
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}

        {/* LOGGED IN VIEWS */}
        {currentUser && (
          <div className="flex flex-col gap-6">
            {/* Back to Vault Button for subviews */}
            {activeTab !== 'vault' && (
              <div className="flex items-center justify-between">
                <button
                  id="back-to-vault-btn"
                  onClick={() => setActiveTab('vault')}
                  className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition cursor-pointer"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Back to Documents Vault</span>
                </button>
              </div>
            )}

            {/* TAB 1: DASHBOARD OVERVIEW */}
            {activeTab === 'dashboard' && (
              <DashboardView
                currentUser={currentUser}
                docs={docs}
                auditLogs={auditLogs}
                metrics={metrics}
                chainStatus={chainStatus}
                setActiveTab={setActiveTab}
                onPreview={handlePreview}
                onDownload={handleDownload}
                downloadingDocId={downloadingDocId}
              />
            )}

            {/* TAB 2: VAULT DOCUMENTS */}
            {activeTab === 'vault' && (
              <VaultView
                currentUser={currentUser}
                docs={docs}
                isLoadingDocs={isLoadingDocs}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                filterCategory={filterCategory}
                setFilterCategory={setFilterCategory}
                filterOwner={filterOwner}
                setFilterOwner={setFilterOwner}
                filterDateFrom={filterDateFrom}
                setFilterDateFrom={setFilterDateFrom}
                filterDateTo={filterDateTo}
                setFilterDateTo={setFilterDateTo}
                sortBy={sortBy}
                setSortBy={setSortBy}
                showAdvancedFilters={showAdvancedFilters}
                setShowAdvancedFilters={setShowAdvancedFilters}
                loadDocuments={loadDocuments}
                resetFilters={resetFilters}
                docPage={docPage}
                setDocPage={setDocPage}
                docPageSize={docPageSize}
                setDocPageSize={setDocPageSize}
                uploadTitle={uploadTitle}
                setUploadTitle={setUploadTitle}
                uploadCategory={uploadCategory}
                setUploadCategory={setUploadCategory}
                uploadFile={uploadFile}
                setUploadFile={setUploadFile}
                isUploading={isUploading}
                uploadProgress={uploadProgress}
                handleUpload={handleUpload}
                resetUploadForm={resetUploadForm}
                duplicateWarning={duplicateWarning}
                onFileSelect={handleFileSelect}
                onPreview={handlePreview}
                onDownload={handleDownload}
                downloadingDocId={downloadingDocId}
                onEdit={(doc) => {
                  setEditingDoc(doc);
                  setEditTitle(doc.title);
                  setEditCategory(doc.category);
                }}
                onDelete={(doc) => setDeletingDoc(doc)}
                grantingDocId={grantingDocId}
                setGrantingDocId={setGrantingDocId}
                grantEmail={grantEmail}
                setGrantEmail={setGrantEmail}
                grantCanEdit={grantCanEdit}
                setGrantCanEdit={setGrantCanEdit}
                isSavingGrant={isSavingGrant}
                handleSaveGrant={handleSaveGrant}
                handleRevokePermission={handleRevokePermission}
                revokingPermId={revokingPermId}
              />
            )}

            {/* TAB 3: AUDIT TRAIL */}
            {activeTab === 'audit' && (
              <AuditView
                currentUser={currentUser}
                auditLogs={auditLogs}
                isLoadingAudit={isLoadingAudit}
                chainStatus={chainStatus}
                isVerifyingChain={isVerifyingChain}
                verifyChain={verifyChain}
                auditActionFilter={auditActionFilter}
                setAuditActionFilter={setAuditActionFilter}
                auditPage={auditPage}
                setAuditPage={setAuditPage}
                auditPageSize={auditPageSize}
                loadAuditLogs={loadAuditLogs}
              />
            )}

            {/* TAB 4: SETTINGS */}
            {activeTab === 'settings' && (
              <SettingsView
                currentUser={currentUser}
                token={token}
                logout={logout}
              />
            )}
          </div>
        )}
      </main>

      {/* MODALS */}
      <PreviewModal
        doc={previewDoc}
        content={previewContent}
        imageUrl={previewImageUrl}
        isLoading={isLoadingPreview}
        onClose={handleClosePreview}
        onDownload={handleDownload}
      />

      <EditModal
        doc={editingDoc}
        editTitle={editTitle}
        setEditTitle={setEditTitle}
        editCategory={editCategory}
        setEditCategory={setEditCategory}
        isSaving={isSavingEdit}
        onSave={handleUpdateDocument}
        onClose={() => setEditingDoc(null)}
      />

      <DeleteModal
        doc={deletingDoc}
        isDeleting={isDeleting}
        onConfirm={handleDeleteDocument}
        onClose={() => setDeletingDoc(null)}
      />

      <ProfileModal
        show={showProfileModal}
        currentUser={currentUser}
        copiedId={copiedId}
        onCopyId={() => {
          if (currentUser) {
            navigator.clipboard.writeText(currentUser.id);
            setCopiedId(true);
            setTimeout(() => setCopiedId(false), 2000);
          }
        }}
        onClose={() => setShowProfileModal(false)}
      />

      {/* Global SaaS Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950/40 p-4 text-center text-xs text-zinc-500">
        TrustVault Platform • Zero-Trust Cloud Document Governance & Chained Cryptographic Audit
      </footer>
    </div>
  );
}

export default App;
