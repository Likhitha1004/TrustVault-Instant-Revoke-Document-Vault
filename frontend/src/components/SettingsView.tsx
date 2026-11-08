import React, { useState } from 'react';
import { 
  Shield, Server, Database, Lock, 
  Key, Cpu, Copy, Check, LogOut
} from 'lucide-react';
import type { User } from '../types';

interface SettingsViewProps {
  currentUser: User;
  token: string | null;
  logout: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  currentUser,
  token,
  logout
}) => {
  const [copiedId, setCopiedId] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  const handleCopyId = () => {
    navigator.clipboard.writeText(currentUser.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleCopyToken = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-200 max-w-4xl mx-auto">
      {/* Account Profile Card */}
      <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 shadow-xl flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-green-950/60 border border-green-500/30 flex items-center justify-center text-green-300 font-bold text-lg font-mono">
              {currentUser.username[0]?.toUpperCase()}
            </div>
            <div>
              <h2 className="text-base font-bold text-white">{currentUser.username}</h2>
              <div className="text-xs text-zinc-400">{currentUser.email}</div>
            </div>
          </div>

          <span className={`px-2.5 py-1 rounded-lg text-xs uppercase font-mono font-semibold ${
            currentUser.role === 'admin'
              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
              : currentUser.role === 'owner'
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          }`}>
            Role: {currentUser.role}
          </span>
        </div>

        <div className="pt-4 border-t border-zinc-800/80 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-zinc-500 font-mono">Account Identifier (UUID):</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="font-mono text-zinc-300 bg-zinc-900 px-2 py-1 rounded border border-zinc-800 truncate">
                {currentUser.id}
              </span>
              <button
                id="copy-settings-user-id-btn"
                onClick={handleCopyId}
                className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
                title="Copy User ID"
              >
                {copiedId ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          <div>
            <span className="text-zinc-500 font-mono">Session Authorization Status:</span>
            <div className="flex items-center gap-2 mt-1 text-emerald-400 font-mono bg-zinc-900 px-2 py-1 rounded border border-zinc-800">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>JWT Signed • Active Bearer Session</span>
            </div>
          </div>
        </div>
      </div>

      {/* Production Architecture & Security Matrix */}
      <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 shadow-xl flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Server className="h-4 w-4 text-green-400" />
          <span>Production Infrastructure & Security Architecture</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl border border-zinc-800/80 bg-zinc-900/30 flex flex-col gap-1">
            <span className="text-zinc-400 font-semibold flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-green-400" />
              Serverless Compute Runtime
            </span>
            <span className="text-zinc-300 font-mono text-[11px]">
              Vercel Python 3.12 Serverless Functions (FastAPI)
            </span>
            <span className="text-[10px] text-zinc-500">Single-origin routing • Zero CORS hops</span>
          </div>

          <div className="p-3 rounded-xl border border-zinc-800/80 bg-zinc-900/30 flex flex-col gap-1">
            <span className="text-zinc-400 font-semibold flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5 text-blue-400" />
              Database Engine & Pooling
            </span>
            <span className="text-zinc-300 font-mono text-[11px]">
              Supabase PostgreSQL (AWS eu-west-1 pooler:5432)
            </span>
            <span className="text-[10px] text-zinc-500">SQLAlchemy NullPool • 0 connection leaks</span>
          </div>

          <div className="p-3 rounded-xl border border-zinc-800/80 bg-zinc-900/30 flex flex-col gap-1">
            <span className="text-zinc-400 font-semibold flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-amber-400" />
              Object Storage & Direct Uploads
            </span>
            <span className="text-zinc-300 font-mono text-[11px]">
              Supabase S3 Private Bucket (`trustvault-docs`)
            </span>
            <span className="text-[10px] text-zinc-500">Presigned SigV4 PUT/GET • 10MB policy</span>
          </div>

          <div className="p-3 rounded-xl border border-zinc-800/80 bg-zinc-900/30 flex flex-col gap-1">
            <span className="text-zinc-400 font-semibold flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-emerald-400" />
              Concurrency & Tamper Evidence
            </span>
            <span className="text-zinc-300 font-mono text-[11px]">
              PostgreSQL Advisory Lock (`77123991`)
            </span>
            <span className="text-[10px] text-zinc-500">SHA-256 sequential audit chain serialization</span>
          </div>
        </div>
      </div>

      {/* Session Management & Token Revocation */}
      <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 shadow-xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Key className="h-4 w-4 text-amber-400" />
            <span>Active Session Management</span>
          </div>

          <button
            id="settings-logout-btn"
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 border border-red-500/40 text-red-200 text-xs font-medium transition cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Revoke Token & Sign Out</span>
          </button>
        </div>

        <p className="text-xs text-zinc-400">
          TrustVault maintains a database-backed token blacklist. Signing out instantly computes a SHA-256 hash of your bearer token and commits it to the <code className="text-zinc-300 font-mono">RevokedToken</code> registry, cutting off authorization with 0ms delay.
        </p>

        {token && (
          <div className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 overflow-hidden">
              <span className="text-[11px] text-zinc-500 font-mono">Active JWT:</span>
              <span className="text-[11px] font-mono text-zinc-400 truncate max-w-sm sm:max-w-md">
                {token.substring(0, 36)}...{token.substring(token.length - 12)}
              </span>
            </div>
            <button
              onClick={handleCopyToken}
              className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs transition cursor-pointer"
              title="Copy Token"
            >
              {copiedToken ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
