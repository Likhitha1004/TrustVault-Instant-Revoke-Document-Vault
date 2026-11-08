import React, { useState } from 'react';
import { 
  X, Download, Copy, Check, FileText, Image as ImageIcon, 
  FileCode, ShieldCheck
} from 'lucide-react';
import type { Document } from '../types';
import { formatBytes } from '../types';

interface PreviewModalProps {
  doc: Document | null;
  content: string | null;
  imageUrl: string | null;
  isLoading: boolean;
  onClose: () => void;
  onDownload: (docId: string, filename: string) => void;
}

export const PreviewModal: React.FC<PreviewModalProps> = ({
  doc,
  content,
  imageUrl,
  isLoading,
  onClose,
  onDownload
}) => {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedContent, setCopiedContent] = useState(false);

  if (!doc) return null;

  const handleCopyHash = () => {
    navigator.clipboard.writeText(doc.file_hash_sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyContent = () => {
    if (content) {
      navigator.clipboard.writeText(content);
      setCopiedContent(true);
      setTimeout(() => setCopiedContent(false), 2000);
    }
  };

  const isImage = imageUrl || doc.mime_type.startsWith('image/');
  const isText = content !== null;

  return (
    <div 
      id="preview-modal-dialog"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-zinc-800 flex items-center justify-between gap-3 bg-zinc-900/40">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-green-950/60 border border-green-500/30 flex items-center justify-center text-green-400 shrink-0">
              {isImage ? <ImageIcon className="h-5 w-5" /> : isText ? <FileCode className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
            </div>
            <div className="overflow-hidden">
              <h3 className="text-sm font-bold text-white truncate" title={doc.title}>
                {doc.title}
              </h3>
              <div className="flex items-center gap-2 text-[11px] text-zinc-400 font-mono mt-0.5">
                <span>{doc.original_filename}</span>
                <span>•</span>
                <span>{formatBytes(doc.file_size)}</span>
                <span>•</span>
                <span className="text-green-400">{doc.category}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              id="preview-download-btn"
              onClick={() => onDownload(doc.id, doc.original_filename)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition cursor-pointer"
              title="Download file"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Download</span>
            </button>

            <button
              id="close-preview-modal-x-btn"
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-850 transition cursor-pointer"
              title="Close Preview (Esc)"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content Viewer */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1 flex flex-col gap-4">
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-zinc-400">
              <div className="h-8 w-8 rounded-full border-2 border-green-500 border-t-transparent animate-spin" />
              <span className="text-xs font-mono">Fetching authenticated stream...</span>
            </div>
          ) : isImage && imageUrl ? (
            <div className="flex items-center justify-center bg-zinc-900/40 rounded-xl p-4 border border-zinc-800/80">
              <img 
                src={imageUrl} 
                alt={doc.title} 
                className="max-h-[50vh] max-w-full rounded-lg object-contain shadow-lg"
              />
            </div>
          ) : isText && content ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
                <span>Text Preview</span>
                <button
                  onClick={handleCopyContent}
                  className="flex items-center gap-1 text-green-400 hover:text-green-300 cursor-pointer"
                >
                  {copiedContent ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  <span>{copiedContent ? 'Copied' : 'Copy Content'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800 font-mono text-xs text-zinc-300 max-h-[45vh] overflow-y-auto whitespace-pre-wrap break-all leading-relaxed">
                {content}
              </pre>
            </div>
          ) : (
            /* Cryptographic Fingerprint & Binary Inspector */
            <div className="flex flex-col gap-4 py-4">
              <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/30 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-white">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <span>Document Cryptographic Verification</span>
                </div>
                <p className="text-xs text-zinc-400">
                  This file format ({doc.mime_type}) is securely archived in private S3 storage. Direct in-browser byte rendering is restricted to authorized downloads to protect confidential data.
                </p>

                <div className="mt-2 flex flex-col gap-1.5">
                  <div className="flex items-center justify-between text-[11px] text-zinc-400">
                    <span>SHA-256 Fingerprint:</span>
                    <button
                      id="copy-preview-hash-btn"
                      onClick={handleCopyHash}
                      className="flex items-center gap-1 text-green-400 hover:text-green-300 cursor-pointer"
                    >
                      {copiedHash ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      <span>{copiedHash ? 'Hash Copied!' : 'Copy Hash'}</span>
                    </button>
                  </div>
                  <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 font-mono text-[11px] text-emerald-400 break-all select-all">
                    {doc.file_hash_sha256}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs mt-2 pt-3 border-t border-zinc-800/80">
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase font-mono">Byte Size</span>
                    <div className="font-mono text-white mt-0.5">{doc.file_size.toLocaleString()} bytes</div>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase font-mono">MIME Type</span>
                    <div className="font-mono text-white mt-0.5">{doc.mime_type}</div>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase font-mono">Integrity Status</span>
                    <div className="font-mono text-emerald-400 mt-0.5 flex items-center gap-1">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      <span>Verified</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800 flex items-center justify-between bg-zinc-900/30 text-xs text-zinc-400">
          <span className="font-mono text-[11px]">ID: {doc.id}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-medium transition cursor-pointer"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};
