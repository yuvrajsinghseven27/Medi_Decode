import React from 'react';
import { PhoneCall, Bell, Activity, UploadCloud, Key } from 'lucide-react';

interface TopBarProps {
  backendStatus: 'connected' | 'checking' | 'offline';
  backendVersion?: string;
  patientName?: string;
  patientId?: string;
  onUploadClick: () => void;
  onAccountClick?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  backendStatus,
  backendVersion = '0.1.0',
  patientName = 'Ramesh Patel',
  patientId = '#MED-4092',
  onUploadClick,
  onAccountClick,
}) => {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 sm:px-6 backdrop-blur-md">
      {/* Brand & Status */}
      <div className="flex items-center gap-3 sm:gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-400 text-white shadow-lg shadow-teal-500/20">
          <Activity className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white sm:text-xl">
              Medi<span className="text-teal-400">Decode</span>
            </h1>
            <span className="hidden rounded-full bg-teal-500/10 px-2 py-0.5 text-xs font-medium text-teal-300 ring-1 ring-inset ring-teal-500/20 sm:inline-block">
              AI Rx Safety
            </span>
          </div>
          {/* Status Indicator */}
          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                backendStatus === 'connected'
                  ? 'bg-emerald-400 animate-pulse'
                  : backendStatus === 'checking'
                  ? 'bg-amber-400 animate-ping'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-400">
              {backendStatus === 'connected'
                ? `Core Engine v${backendVersion} Online`
                : backendStatus === 'checking'
                ? 'Connecting API...'
                : 'Offline / Standalone Mode'}
            </span>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* API Docs Launcher */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden items-center gap-1.5 rounded-lg border border-teal-500/30 bg-teal-500/10 px-2.5 py-1.5 text-xs font-semibold text-teal-300 transition-colors hover:bg-teal-500/20 sm:flex"
          title="Open Swagger API Explorer"
        >
          <Key className="h-3.5 w-3.5 text-teal-400" />
          <span>API Docs</span>
        </a>

        {/* Emergency Quick Action */}
        <a
          href="tel:911"
          className="hidden items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-300 transition-colors hover:bg-rose-500/20 md:flex"
          title="Emergency Medical Hotline / Poison Control"
        >
          <PhoneCall className="h-3.5 w-3.5 text-rose-400" />
          <span>Emergency Helpline</span>
        </a>

        {/* Upload Prescription Action */}
        <button
          onClick={onUploadClick}
          className="flex items-center gap-2 rounded-lg bg-teal-500 px-3.5 py-1.5 text-xs sm:text-sm font-semibold text-slate-950 shadow-md shadow-teal-500/20 transition-all hover:bg-teal-400 hover:shadow-teal-500/30 active:scale-95"
        >
          <UploadCloud className="h-4 w-4" />
          <span className="hidden xs:inline">Scan Prescription</span>
        </button>

        {/* Notifications */}
        <button
          className="relative rounded-lg border border-slate-800 bg-slate-800/60 p-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          aria-label="Safety Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-teal-400 ring-2 ring-slate-900" />
        </button>

        {/* User / Patient Profile (Clickable modal opener) */}
        <button
          onClick={onAccountClick}
          className="flex items-center gap-2.5 border-l border-slate-800 pl-2 sm:pl-4 hover:opacity-80 transition-opacity text-left"
          title="Switch Patient or View System Links"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-teal-300 ring-1 ring-slate-700">
            {patientName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'RP'}
          </div>
          <div className="hidden text-left lg:block">
            <p className="text-xs font-medium text-slate-200">{patientName}</p>
            <p className="text-[10px] text-slate-400">ID: {patientId}</p>
          </div>
        </button>
      </div>
    </header>
  );
};
