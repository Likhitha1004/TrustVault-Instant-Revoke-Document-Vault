import React from 'react';
import { X, Edit2, Trash2, User as UserIcon, Copy, Check, AlertTriangle } from 'lucide-react';
import type { User, Document } from '../types';

interface EditModalProps {
  doc: Document | null;
  editTitle: string;
  setEditTitle: (t: string) => void;
  editCategory: string;
  setEditCategory: (c: string) => void;
  isSaving: boolean;
  onSave: (e: React.FormEvent) => void;
  onClose: () => void;
}

export const EditModal: React.FC<EditModalProps> = ({
  doc,
  editTitle,
  setEditTitle,
  editCategory,
  setEditCategory,
  isSaving,
  onSave,
  onClose
}) => {
  if (!doc) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in" role="dialog" aria-modal="true">
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 max-w-md w-full shadow-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2 font-semibold text-sm text-white">
            <Edit2 className="h-4 w-4 text-green-400" />
            <span>Edit Document Metadata</span>
          </div>
          <button 
            id="close-edit-modal-x-btn"
            onClick={onClose} 
            className="text-zinc-500 hover:text-white p-1 rounded transition cursor-pointer"
            title="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={onSave} className="flex flex-col gap-3.5">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Document Title</label>
            <input 
              id="edit-doc-title-input"
              type="text" 
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1">Category</label>
            <select 
              id="edit-doc-category-select"
              value={editCategory}
              onChange={(e) => setEditCategory(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500 cursor-pointer"
            >
              <option value="Legal">Legal</option>
              <option value="Finance">Finance</option>
              <option value="Technical">Technical</option>
              <option value="General">General</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
            <button 
              id="cancel-edit-modal-btn"
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg border border-zinc-800 text-xs text-zinc-400 hover:text-white transition cursor-pointer"
            >
              Cancel
            </button>
            <button 
              id="save-edit-modal-btn"
              type="submit"
              disabled={isSaving}
              className="px-4 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-xs text-white font-medium transition cursor-pointer disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface DeleteModalProps {
  doc: Document | null;
  isDeleting: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export const DeleteModal: React.FC<DeleteModalProps> = ({
  doc,
  isDeleting,
  onConfirm,
  onClose
}) => {
  if (!doc) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in" role="dialog" aria-modal="true">
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-5 max-w-md w-full shadow-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2 font-semibold text-sm text-red-400">
            <Trash2 className="h-4 w-4 text-red-400" />
            <span>Confirm Document Deletion</span>
          </div>
          <button 
            id="close-delete-modal-x-btn"
            onClick={onClose} 
            className="text-zinc-500 hover:text-white p-1 rounded transition cursor-pointer"
            title="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="text-xs text-zinc-300 leading-relaxed flex flex-col gap-2">
          <p>
            Are you sure you want to permanently delete document <strong className="text-white font-semibold">"{doc.title}"</strong>?
          </p>
          <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg text-red-300 text-[11px] flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
            <span>
              This will remove the file from private S3 object storage, revoke all shared permissions, and record an immutable tombstone event in the cryptographic audit trail.
            </span>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
          <button 
            id="cancel-delete-modal-btn"
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg border border-zinc-800 text-xs text-zinc-400 hover:text-white transition cursor-pointer"
          >
            Cancel
          </button>
          <button 
            id="confirm-delete-modal-btn"
            type="button"
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs text-white font-medium transition cursor-pointer disabled:opacity-50"
          >
            {isDeleting ? 'Deleting...' : 'Delete Permanently'}
          </button>
        </div>
      </div>
    </div>
  );
};

interface ProfileModalProps {
  show: boolean;
  currentUser: User | null;
  copiedId: boolean;
  onCopyId: () => void;
  onClose: () => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  show,
  currentUser,
  copiedId,
  onCopyId,
  onClose
}) => {
  if (!show || !currentUser) return null;

  return (
    <div id="profile-modal-dialog" className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in" role="dialog" aria-modal="true">
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 max-w-sm w-full shadow-2xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2 font-semibold text-sm text-white">
            <UserIcon className="h-4 w-4 text-green-400" />
            <span>User Profile & Security</span>
          </div>
          <button 
            id="close-profile-modal-x-btn"
            onClick={onClose} 
            className="text-zinc-500 hover:text-white p-1 rounded transition cursor-pointer"
            title="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex flex-col gap-3 text-xs">
          <div>
            <span className="text-zinc-500 font-mono text-[11px] block">Username:</span>
            <span className="font-semibold text-white text-sm">{currentUser.username}</span>
          </div>

          <div>
            <span className="text-zinc-500 font-mono text-[11px] block">Email Address:</span>
            <span className="text-zinc-300 font-mono">{currentUser.email}</span>
          </div>

          <div>
            <span className="text-zinc-500 font-mono text-[11px] block">System Role:</span>
            <span className={`inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold ${
              currentUser.role === 'admin' ? 'bg-red-500/20 text-red-300' : currentUser.role === 'owner' ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300'
            }`}>
              {currentUser.role}
            </span>
          </div>

          <div>
            <span className="text-zinc-500 font-mono text-[11px] block">Account Identifier (UUID):</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-zinc-400 bg-zinc-900 px-2 py-1 rounded border border-zinc-800 text-[11px] truncate flex-1">
                {currentUser.id}
              </span>
              <button
                id="copy-userid-btn"
                onClick={onCopyId}
                className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs transition cursor-pointer shrink-0"
                title="Copy User ID"
              >
                {copiedId ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-zinc-800 flex justify-end">
          <button 
            id="close-profile-modal-btn"
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200 transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
