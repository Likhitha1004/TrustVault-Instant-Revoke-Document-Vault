import React from 'react';
import { Shield, LayoutDashboard, Lock, History, Settings, User as UserIcon, Menu, X } from 'lucide-react';
import type { User } from '../types';

interface HeaderProps {
  currentUser: User | null;
  activeTab: 'dashboard' | 'vault' | 'audit' | 'settings';
  setActiveTab: (tab: 'dashboard' | 'vault' | 'audit' | 'settings') => void;
  mobileMenuOpen: boolean;
  setMobileMenuOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setShowProfileModal: (show: boolean) => void;
  logout: () => void;
  setAuthMode: (mode: 'login' | 'register') => void;
  setLoginId: (id: string) => void;
  setPassword: (pwd: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  mobileMenuOpen,
  setMobileMenuOpen,
  setShowProfileModal,
  logout,
  setAuthMode,
  setLoginId,
  setPassword
}) => {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo & System Status */}
        <div id="nav-brand-logo" className="flex items-center gap-3 shrink-0">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-green-600 to-lime-700 flex items-center justify-center shadow-lg shadow-green-900/30 ring-1 ring-white/10">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white font-mono">TrustVault</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20 font-mono">v1.0-PROD</span>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <div id="system-status-indicator" className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-[9px] font-mono">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                </span>
                SYS OK • AWS EU-WEST-1 • VERIFIED
              </div>
            </div>
          </div>
        </div>

        {/* Desktop Navigation Tabs */}
        {currentUser && (
          <nav className="hidden md:flex items-center gap-1 bg-zinc-900/60 p-1 rounded-xl border border-zinc-800/80">
            <button
              id="nav-tab-dashboard"
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-green-600 text-white shadow-md shadow-green-900/30'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <LayoutDashboard className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </button>

            <button
              id="nav-tab-vault"
              onClick={() => setActiveTab('vault')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeTab === 'vault'
                  ? 'bg-green-600 text-white shadow-md shadow-green-900/30'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <Lock className="h-3.5 w-3.5" />
              <span>Vault</span>
            </button>

            <button
              id="nav-tab-audit"
              onClick={() => setActiveTab('audit')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeTab === 'audit'
                  ? 'bg-green-600 text-white shadow-md shadow-green-900/30'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <History className="h-3.5 w-3.5" />
              <span>Audit Trail</span>
            </button>

            <button
              id="nav-tab-settings"
              onClick={() => setActiveTab('settings')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeTab === 'settings'
                  ? 'bg-green-600 text-white shadow-md shadow-green-900/30'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <Settings className="h-3.5 w-3.5" />
              <span>Settings</span>
            </button>
          </nav>
        )}

        {/* User Role Profile & Quick Switcher */}
        <div className="flex items-center gap-2">
          {currentUser ? (
            <div className="flex items-center gap-2">
              <button
                id="header-profile-btn"
                onClick={() => setShowProfileModal(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-xs font-mono transition cursor-pointer"
                title="View Account & Security Details"
              >
                <div className="h-5 w-5 rounded-full bg-green-950 border border-green-500/40 flex items-center justify-center text-green-300 text-[10px] font-bold">
                  {currentUser.username[0]?.toUpperCase() || 'U'}
                </div>
                <span className="hidden sm:inline font-medium text-white">{currentUser.username}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold ${
                  currentUser.role === 'admin'
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                    : currentUser.role === 'owner'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}>
                  {currentUser.role}
                </span>
              </button>

              <button
                id="header-logout-btn"
                onClick={logout}
                className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-red-950/40 border border-zinc-800 hover:border-red-500/40 text-xs text-zinc-400 hover:text-red-300 transition cursor-pointer"
                title="Sign out securely"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <button
                id="quick-admin-btn"
                onClick={() => { setAuthMode('login'); setLoginId('admin@trustvault.io'); setPassword('AdminPass2026!'); }}
                className="px-2 py-1 rounded text-[11px] font-mono bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
              >
                Admin
              </button>
              <button
                id="quick-owner-btn"
                onClick={() => { setAuthMode('login'); setLoginId('owner@trustvault.io'); setPassword('OwnerPass2026!'); }}
                className="px-2 py-1 rounded text-[11px] font-mono bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
              >
                Owner
              </button>
              <button
                id="quick-viewer-btn"
                onClick={() => { setAuthMode('login'); setLoginId('viewer@trustvault.io'); setPassword('ViewerPass2026!'); }}
                className="px-2 py-1 rounded text-[11px] font-mono bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
              >
                Viewer
              </button>
            </div>
          )}

          {/* Mobile Menu Button */}
          {currentUser && (
            <button
              id="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(prev => !prev)}
              className="md:hidden p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Mobile Dropdown Navigation */}
      {currentUser && mobileMenuOpen && (
        <div className="md:hidden border-t border-zinc-800 bg-zinc-950 p-4 flex flex-col gap-2 animate-in slide-in-from-top duration-150">
          <button
            id="mobile-nav-dashboard"
            onClick={() => { setActiveTab('dashboard'); setMobileMenuOpen(false); }}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition cursor-pointer ${
              activeTab === 'dashboard' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
            }`}
          >
            <LayoutDashboard className="h-4 w-4" />
            <span>Dashboard Overview</span>
          </button>

          <button
            id="mobile-nav-vault"
            onClick={() => { setActiveTab('vault'); setMobileMenuOpen(false); }}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition cursor-pointer ${
              activeTab === 'vault' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
            }`}
          >
            <Lock className="h-4 w-4" />
            <span>Documents Vault</span>
          </button>

          <button
            id="mobile-nav-audit"
            onClick={() => { setActiveTab('audit'); setMobileMenuOpen(false); }}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition cursor-pointer ${
              activeTab === 'audit' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
            }`}
          >
            <History className="h-4 w-4" />
            <span>Audit Trail & Cryptographic Chain</span>
          </button>

          <button
            id="mobile-nav-settings"
            onClick={() => { setActiveTab('settings'); setMobileMenuOpen(false); }}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition cursor-pointer ${
              activeTab === 'settings' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>Settings & Security Posture</span>
          </button>

          <button
            id="mobile-profile-btn"
            onClick={() => { setShowProfileModal(true); setMobileMenuOpen(false); }}
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left text-zinc-400 hover:text-white hover:bg-zinc-900 border-t border-zinc-800/80 mt-1 pt-2 transition cursor-pointer"
          >
            <UserIcon className="h-4 w-4" />
            <span>Account Details ({currentUser.username})</span>
          </button>
        </div>
      )}
    </header>
  );
};
